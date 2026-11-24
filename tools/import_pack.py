"""Turn a speaker's voice pack (.fsh from the recording studio) into a second built-in voice.

  python3 scripts/import_pack.py PACK.fsh "Label shown in Settings" [--out site/] [--no-check]

Refuses a pack without the speaker's consent. Every clip is decoded, checked against its expected
text with the Hebrew speech model, levelled, and encoded as MP3. Writes OUT/media/pack2.mp3,
OUT/voice2.js and a report beside the pack."""
import sys,json,struct,subprocess,os,re,tempfile
R='/home/claude/heb/'
args=[a for a in sys.argv[1:] if not a.startswith('--')];flags=sys.argv[1:]
out=flags[flags.index('--out')+1] if '--out' in flags else R+'site/'
if '--out' in flags: args.remove(out)
src,label=args[0],args[1]
b=open(src,'rb').read();n=struct.unpack('<I',b[:4])[0];idx=json.loads(b[4:4+n].decode());base=4+n
meta=idx[0].get('meta',{}) if idx and 'meta' in idx[0] else {}
if not meta.get('consent'): sys.exit('Refused: the speaker did not tick the consent box in the recording studio.')
clips=[e for e in idx if 'id' in e]
C=json.load(open('/tmp/content.json'));W={w['id']:w for w in C['WORDS']};L=C['LESSONS']
def expect(i):
    if re.fullmatch(r's\d+',i):
        k=int(i[1:])-1;return ' '.join(W[x]['he'] for x in L[k]['sample']) if 0<=k<len(L) else None
    return W[i]['he'] if i in W else None
norm=lambda s:re.sub(r'[^א-ת ]','',re.sub(r'[֑-ׇ]','',s)).translate(str.maketrans('ךםןףץ','כמנפצ')).split()
model=None
if '--no-check' not in flags:
    import numpy as np,faster_whisper
    model=faster_whisper.WhisperModel('ivrit-ai/whisper-large-v3-turbo-ct2',device='cpu',compute_type='int8',cpu_threads=4)
tmp=tempfile.mkdtemp();pack=b'';P={};rep=[]
for e in clips:
    i=e['id'];ex=expect(i)
    if ex is None: rep.append([i,'skipped','not in this course']);continue
    raw=os.path.join(tmp,'in');open(raw,'wb').write(b[base+e['off']:base+e['off']+e['len']])
    wav=os.path.join(tmp,'a.wav');r=subprocess.run(['ffmpeg','-v','error','-y','-i',raw,'-ac','1','-ar','16000',wav])
    if r.returncode: rep.append([i,'rejected','could not decode']);continue
    if model:
        a=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',wav,'-f','f32le','-'],capture_output=True).stdout,dtype=np.float32)
        segs,_=model.transcribe(a,language='he',beam_size=5,condition_on_previous_text=False,without_timestamps=True)
        got=' '.join(s.text.strip() for s in segs);g,x=norm(got),norm(ex)
        loose=lambda ws:[w.replace('ו','').replace('י','') for w in ws]
        hit=sum(1 for w in loose(x) if w in loose(g))
        ok=(g==x) or (loose(g)==loose(x)) or (len(x)>1 and hit>=len(x)-1)
        if not ok: rep.append([i,'rejected','heard: '+got]);continue
    mp3=os.path.join(tmp,'o.mp3')
    subprocess.run(['ffmpeg','-v','error','-y','-i',wav,'-af','loudnorm=I=-18:TP=-1.5','-ac','1','-ar','44100','-c:a','libmp3lame','-b:a','96k',mp3],check=True)
    m=open(mp3,'rb').read();P[i]=[len(pack),len(m)];pack+=m;rep.append([i,'ok',''])
os.makedirs(os.path.join(out,'media'),exist_ok=True)
open(os.path.join(out,'media','pack2.mp3'),'wb').write(pack)
V={'label':label,'name':meta.get('speaker') or 'a fluent speaker','date':meta.get('date',''),'n':len(P),'PACK':P}
open(os.path.join(out,'voice2.js'),'w').write('// Second built-in voice, from a pack recorded and consented to by '+V['name']+'.\nwindow.VOICE2='+json.dumps(V,ensure_ascii=False,separators=(',',':'))+';\n')
json.dump(rep,open(src+'.report.json','w'),ensure_ascii=False,indent=0)
print('kept',len(P),'of',len(clips),'| rejected',sum(1 for r in rep if r[1]=='rejected'),'| skipped',sum(1 for r in rep if r[1]=='skipped'),'|',round(len(pack)/1e6,2),'MB')
