# Free Speech in Hebrew: night-stage plates. Run: blender -b -P stage.py -- OUTDIR [names]
import bpy, math, random, sys, os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; OUT=a[0]; ONLY=set(a[1:]); FONT=os.path.join(OUT,'FRL-500.ttf')
INK=(0.012,0.012,0.045,1); VIO=(0.07,0.035,0.13,1); GOLD=(1.0,0.72,0.36,1)
def reset(w=720,h=1280,transparent=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene; s.render.engine='BLENDER_EEVEE_NEXT'
    s.render.resolution_x=w; s.render.resolution_y=h; s.render.resolution_percentage=100
    s.render.film_transparent=transparent; s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGBA'
    s.eevee.taa_render_samples=48
    try: s.eevee.use_raytracing=True
    except: pass
    try: s.eevee.volumetric_tile_size='4'; s.eevee.volumetric_samples=64
    except: pass
    s.view_settings.view_transform='AgX'
    try: s.view_settings.look='AgX - Base Contrast'
    except: pass
    wd=bpy.data.worlds.new('W'); s.world=wd; wd.use_nodes=True; wd.node_tree.nodes['Background'].inputs[0].default_value=INK; wd.node_tree.nodes['Background'].inputs[1].default_value=1
    s.use_nodes=True; t=s.node_tree; [t.nodes.remove(n) for n in list(t.nodes)]
    rl=t.nodes.new('CompositorNodeRLayers'); g=t.nodes.new('CompositorNodeGlare'); o=t.nodes.new('CompositorNodeComposite')
    try: g.glare_type='BLOOM'
    except: g.glare_type='FOG_GLOW'
    try: g.threshold=0.8; g.size=8
    except: pass
    try: g.mix=0.0
    except: pass
    t.links.new(rl.outputs['Image'],g.inputs['Image']); t.links.new(g.outputs['Image'],o.inputs['Image'])
    try: t.links.new(rl.outputs['Alpha'],o.inputs['Alpha'])
    except: pass
    return s
def mat(name,base=(0.5,0.5,0.5,1),metal=0,rough=0.5,trans=0,ior=1.45,emit=None,es=0,coat=0,sheen=0,alpha=1):
    m=bpy.data.materials.new(name); m.use_nodes=True; p=m.node_tree.nodes['Principled BSDF']; I=p.inputs
    I['Base Color'].default_value=base; I['Metallic'].default_value=metal; I['Roughness'].default_value=rough
    I['Transmission Weight'].default_value=trans; I['IOR'].default_value=ior; I['Alpha'].default_value=alpha
    if emit: I['Emission Color'].default_value=emit; I['Emission Strength'].default_value=es*0.4
    if trans>0 and not emit:
        N=m.node_tree.nodes; lw=N.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value=0.25
        rp=N.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position=0.35; rp.color_ramp.elements[0].color=(0,0,0,1); rp.color_ramp.elements[1].color=(0.55,0.55,0.95,1)
        m.node_tree.links.new(lw.outputs['Facing'],rp.inputs[0]); m.node_tree.links.new(rp.outputs[0],I['Emission Color']); I['Emission Strength'].default_value=1.6
    I['Coat Weight'].default_value=coat; I['Sheen Weight'].default_value=sheen
    try: m.surface_render_method='DITHERED'
    except: pass
    return m
def assign(o,m): o.data.materials.clear(); o.data.materials.append(m); return o
def sky_mat(aurora=1.0,stars=1.0,top=(0.004,0.004,0.018,1),bot=(0.035,0.018,0.075,1)):
    m=bpy.data.materials.new('Sky'); m.use_nodes=True; N=m.node_tree.nodes; L=m.node_tree.links; [N.remove(n) for n in list(N)]
    tc=N.new('ShaderNodeTexCoord'); sep=N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'],sep.inputs[0])
    ramp=N.new('ShaderNodeValToRGB'); r=ramp.color_ramp; r.elements[0].position=0.0; r.elements[0].color=bot; r.elements[1].position=1.0; r.elements[1].color=top
    L.new(sep.outputs['Y'],ramp.inputs[0])
    # aurora: stretched noise, masked to a band
    mp=N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(1.2,5.0,1); L.new(tc.outputs['Generated'],mp.inputs[0])
    nz=N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=2.2; nz.inputs['Detail'].default_value=6; nz.inputs['Distortion'].default_value=1.4; L.new(mp.outputs[0],nz.inputs[0])
    band=N.new('ShaderNodeValToRGB'); b=band.color_ramp; b.elements[0].position=0.52; b.elements[0].color=(0,0,0,1); b.elements[1].position=0.72; b.elements[1].color=(1,1,1,1); L.new(nz.outputs['Fac'],band.inputs[0])
    hm=N.new('ShaderNodeValToRGB'); h=hm.color_ramp; h.elements[0].position=0.45; h.elements[0].color=(0,0,0,1); h.elements[1].position=0.75; h.elements[1].color=(1,1,1,1); e=h.elements.new(0.95); e.color=(0,0,0,1); L.new(sep.outputs['Y'],hm.inputs[0])
    m1=N.new('ShaderNodeMath'); m1.operation='MULTIPLY'; L.new(band.outputs[0],m1.inputs[0]); L.new(hm.outputs[0],m1.inputs[1])
    acol=N.new('ShaderNodeValToRGB'); c=acol.color_ramp; c.elements[0].color=(0.03,0.30,0.30,1); c.elements[1].color=(0.22,0.10,0.45,1); L.new(nz.outputs['Color'] if False else sep.outputs['X'],acol.inputs[0])
    m2=N.new('ShaderNodeMixRGB'); m2.blend_type='ADD'; L.new(m1.outputs[0],m2.inputs[0]); L.new(ramp.outputs[0],m2.inputs[1])
    sc=N.new('ShaderNodeMixRGB'); sc.blend_type='MULTIPLY'; sc.inputs[0].default_value=1; L.new(acol.outputs[0],sc.inputs[1]); sc.inputs[2].default_value=(0.35*aurora,)*3+(1,); L.new(sc.outputs[0],m2.inputs[2])
    # stars
    vor=N.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value=180; vor.feature='DISTANCE_TO_EDGE' if False else 'F1'; L.new(tc.outputs['Generated'],vor.inputs[0])
    st=N.new('ShaderNodeMath'); st.operation='LESS_THAN'; st.inputs[1].default_value=0.06; L.new(vor.outputs['Distance'],st.inputs[0])
    sv=N.new('ShaderNodeMath'); sv.operation='MULTIPLY'; L.new(st.outputs[0],sv.inputs[0]); L.new(vor.outputs['Color'] if 'Color' in vor.outputs else vor.outputs[1],sv.inputs[1])
    sp=N.new('ShaderNodeMath'); sp.operation='POWER'; sp.inputs[1].default_value=3.0; L.new(sv.outputs[0],sp.inputs[0])
    sm=N.new('ShaderNodeMath'); sm.operation='MULTIPLY'; sm.inputs[1].default_value=9*stars; L.new(sp.outputs[0],sm.inputs[0])
    add=N.new('ShaderNodeMixRGB'); add.blend_type='ADD'; add.inputs[0].default_value=1; L.new(m2.outputs[0],add.inputs[1]); L.new(sm.outputs[0],add.inputs[2])
    em=N.new('ShaderNodeEmission'); em.inputs[1].default_value=1.0; L.new(add.outputs[0],em.inputs[0])
    out=N.new('ShaderNodeOutputMaterial'); L.new(em.outputs[0],out.inputs[0]); return m
def backdrop(cam,dist=40,size=60,asp=0.5625,**kw):
    bpy.ops.mesh.primitive_plane_add(size=1); p=bpy.context.object; p.scale=(size*asp,size,1) if asp<1 else (size,size/asp,1)
    p.location=cam.location+ (cam.matrix_world.to_quaternion()@Vector((0,0,-dist))); p.rotation_euler=cam.rotation_euler
    assign(p,sky_mat(**kw)); return p
def camera(loc,rot,lens=35,dof=None,fs=2.8):
    bpy.ops.object.camera_add(location=loc,rotation=[math.radians(x) for x in rot]); c=bpy.context.object; c.data.lens=lens
    if dof: c.data.dof.use_dof=True; c.data.dof.focus_distance=dof; c.data.dof.aperture_fstop=fs
    bpy.context.scene.camera=c; return c
def light(kind,loc,energy,color=(1,1,1),rot=(0,0,0),size=1,spot=None):
    d=bpy.data.lights.new(kind,kind); d.energy=energy; d.color=color
    if kind=='AREA': d.size=size
    if kind=='SPOT' and spot: d.spot_size=math.radians(spot); d.spot_blend=0.6
    if kind in('POINT','SPOT'): d.shadow_soft_size=size
    o=bpy.data.objects.new(kind,d); o.location=loc; o.rotation_euler=[math.radians(x) for x in rot]; bpy.context.collection.objects.link(o); return o
def fog(center,size,density,color=(0.55,0.5,0.8,1)):
    bpy.ops.mesh.primitive_cube_add(location=center); c=bpy.context.object; c.scale=size
    m=bpy.data.materials.new('Fog'); m.use_nodes=True; N=m.node_tree.nodes; N.remove(N['Principled BSDF'])
    v=N.new('ShaderNodeVolumePrincipled'); v.inputs['Density'].default_value=density; v.inputs['Color'].default_value=color
    m.node_tree.links.new(v.outputs[0],N['Material Output'].inputs['Volume']); assign(c,m); return c
def curve(pts,bevel,m,name='C',res=12):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=bevel; cu.bevel_resolution=4; cu.use_fill_caps=True
    sp=cu.splines.new('NURBS'); sp.points.add(len(pts)-1)
    for i,(x,y,z,r) in enumerate(pts): sp.points[i].co=(x,y,z,1); sp.points[i].radius=r
    sp.use_endpoint_u=True; sp.order_u=4; sp.resolution_u=res
    o=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(o); cu.materials.append(m); return o
def render(name):
    bpy.context.scene.render.filepath=os.path.join(OUT,name+'.png'); bpy.ops.render.render(write_still=True); print('RENDERED',name)
def want(n): return not ONLY or n in ONLY
random.seed(7)


def cycles(samples=96):
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=samples;s.cycles.use_denoising=True
    try: s.cycles.denoiser='OPENIMAGEDENOISE'
    except: pass
    s.cycles.device='CPU';s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=0.03
    s.render.use_persistent_data=True
def heb(txt,loc,size,m,rot=(90,0,0),align='CENTER',extrude=0.004):
    cu=bpy.data.curves.new('T','FONT');cu.body=txt[::-1];cu.size=size;cu.align_x=align;cu.align_y='CENTER';cu.extrude=extrude;cu.bevel_depth=0.002
    try: cu.font=bpy.data.fonts.load(FONT,check_existing=True)
    except Exception as e: print('font',e)
    o=bpy.data.objects.new('T',cu);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=[math.radians(x) for x in rot];cu.materials.append(m);return o
def emis(name,col,st):
    m=bpy.data.materials.new(name);m.use_nodes=True;N=m.node_tree.nodes;N.remove(N['Principled BSDF']);e=N.new('ShaderNodeEmission');e.inputs[0].default_value=col;e.inputs[1].default_value=st
    m.node_tree.links.new(e.outputs[0],N['Material Output'].inputs[0]);return m
GOLDE=(1.0,0.78,0.42,1);CORE=(1.0,0.88,0.62,1);LAV=(0.58,0.55,0.86,1)
def size(w,h,cyc=False,samples=96):
    s=bpy.context.scene;s.render.resolution_x=w;s.render.resolution_y=h
    if cyc: cycles(samples)
# ---------- scene builders (portrait plate unless hero) ----------
def sc_sky(hero=False):
    reset(); c=camera((0,-10,1.2),(92,0,0),lens=28 if not hero else 24); backdrop(c,dist=30,size=40 if not hero else 90,asp=0.5625 if not hero else 1.78)
    m=mat('hz',base=(0.2,0.2,0.35,1),rough=0.1,trans=1,emit=(0.6,0.55,1,1),es=0.6)
    bpy.ops.mesh.primitive_torus_add(major_radius=30,minor_radius=0.03,location=(0,30,-29.2)); assign(bpy.context.object,m); return c
def sc_tree(hero=False,branches=False):
    reset(); c=camera((0,-10.5,-1.6),(90,0,0),lens=34 if not hero else 28,dof=9,fs=4); backdrop(c,dist=26 if not hero else 34,size=36 if not hero else 110,asp=0.5625 if not hero else 1.78,aurora=0.7)
    glass=mat('glass',base=(0.85,0.85,1,1),rough=0.04,trans=1,ior=1.52,coat=1); vein=mat('vein',base=GOLD,emit=GOLD,es=7 if not hero else 3)
    trunk=[(0,0,-3.5,1.6),(0,0,-2.4,1.35),(0.05,0,-1.4,1.15),(0,0,-0.6,1.0),(0,0,-0.1,0.95)]
    curve(trunk,0.32,glass,'trunk'); curve([(x*0.25,y,z,r*0.3) for x,y,z,r in trunk],0.32,vein,'core')
    for k,ang in enumerate((-55,0,55)):
        a=math.radians(ang); pts=[(0,0,-3.3,0.8)]
        for i in range(1,6):
            t=i/5; pts.append((math.sin(a)*2.6*t,-0.2*t,-3.3-1.9*t+0.3*math.sin(t*3),0.8-0.6*t))
        curve(pts,0.22,glass,'root%d'%k); curve([(x,y-0.02,z,r*0.25) for x,y,z,r in pts],0.22,vein,'rv%d'%k)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42,location=(math.sin(a)*2.6,-0.2,-5.25)); s=bpy.context.object; bpy.ops.object.shade_smooth(); assign(s,mat('seed%d'%k,base=GOLD,emit=GOLD,es=1.0,rough=0.3))
    if branches:
        bm=emis('br',GOLDE,5); lm=emis('leaf',CORE,14); random.seed(3)
        for i in range(46):
            th=math.radians(random.uniform(-75,75)); r=random.uniform(1.4,3.4); ex=math.sin(th)*r; ez=-0.1+math.cos(th)*r
            curve([(0,0,-0.1,1),(0,0,-0.1+r*0.4,0.8),(ex*0.6,-0.05,ez-0.4,0.5),(ex,-0.1,ez,0.2)],0.018,bm,'b%d'%i)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,location=(ex,-0.1,ez)); assign(bpy.context.object,lm)
        lt=mat('lt',base=(0.2,0.12,0.03,1),rough=0.5)
        for k,(ang,ch) in enumerate(((-55,'ב'),(0,'ת'),(55,'כ'))):
            a=math.radians(ang); heb(ch,(math.sin(a)*2.6,-0.65,-5.25),0.5,lt)
        for i,(w,x,z) in enumerate((('מכתב',-2.3,2.2),('כתב',2.2,2.4),('כותב',0.2,3.1))): heb(w,(x,-0.3,z),0.42,emis('w%d'%i,CORE,6))
    light('AREA',(3,-4,3),300,(0.7,0.7,1),(60,0,30),size=4); light('POINT',(0,-1.5,-4.5),25,(1,0.75,0.4),size=1)
    fog((0,0,-2),(8,6,6),0.015); c.location=(0,-10.5 if not hero else -17.0,-1.6 if not hero else -1.1)
    if hero: c.data.lens=30
    return c
def sc_lab(hero=False,rings=False,mould=False):
    reset(); c=camera((0,-7.5,4.2),(62,0,0),lens=32 if not hero else 26,dof=7.8,fs=3.2); backdrop(c,dist=30,size=44 if not hero else 110,asp=0.5625 if not hero else 1.78,aurora=0.9)
    stone=mat('stone',base=(0.04,0.035,0.07,1),rough=0.55,coat=0.3); goldm=mat('gold',base=GOLD,metal=1,rough=0.22); glass=mat('glass',base=(0.9,0.9,1,1),rough=0.03,trans=1,coat=1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=3.4,depth=0.5,location=(0,0,0)); slab=bpy.context.object
    bv=slab.modifiers.new('b','BEVEL'); bv.width=0.08; bv.segments=4; bpy.ops.object.shade_smooth(); assign(slab,stone)
    bpy.ops.mesh.primitive_torus_add(major_radius=3.42,minor_radius=0.035,location=(0,0,0.25)); assign(bpy.context.object,mat('rim',base=GOLD,emit=GOLD,es=5))
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=0.75,depth=0.8,location=(0,0.2,0.65)); cr=bpy.context.object
    so=cr.modifiers.new('s','SOLIDIFY'); so.thickness=0.06; bv=cr.modifiers.new('b','BEVEL'); bv.width=0.03; bv.segments=3; bpy.ops.object.shade_smooth(); assign(cr,goldm)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=0.68,depth=0.05,location=(0,0.2,0.88)); assign(bpy.context.object,mat('melt',base=GOLD,emit=(1,0.62,0.25,1),es=9))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6,location=(-1.9,0.9,0.85)); bpy.ops.object.shade_smooth(); assign(bpy.context.object,glass)
    curve([(-1.9,0.9,1.4,1),(-1.85,0.9,2.0,0.8),(-1.3,0.85,2.3,0.6),(-0.6,0.6,2.0,0.5)],0.07,glass,'neck')
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.32,location=(-1.9,0.9,0.7)); bpy.ops.object.shade_smooth(); assign(bpy.context.object,mat('elix',base=(0.4,0.3,0.9,1),emit=(0.45,0.35,1,1),es=3))
    for i,x in enumerate((1.6,2.05,2.5)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=0.13,depth=0.7,location=(x,1.0-0.25*i,0.6)); bpy.ops.object.shade_smooth(); assign(bpy.context.object,glass)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=0.11,depth=0.3,location=(x,1.0-0.25*i,0.42)); assign(bpy.context.object,mat('v%d'%i,base=GOLD,emit=(0.9,0.7,0.4,1),es=1.5+i))
    if rings:
        for i,(r,tilt) in enumerate(((1.25,12),(1.55,-18))):
            bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=0.012,location=(0,0.2,1.6+i*0.25),rotation=(math.radians(tilt),math.radians(tilt*0.5),0)); assign(bpy.context.object,mat('ring%d'%i,base=GOLD,emit=GOLD,es=6))
    if mould:
        bpy.ops.mesh.primitive_cube_add(location=(0,-0.6,2.25)); mo=bpy.context.object; mo.scale=(1.25,0.18,0.42); bv=mo.modifiers.new('b','BEVEL'); bv.width=0.08; bv.segments=4; assign(mo,mat('mould',base=(0.9,0.9,1,1),rough=0.06,trans=1,ior=1.47,coat=1))
        heb('מכתב',(0,-0.82,2.25),0.5,emis('mw',CORE,9))
        sm=emis('stream',(1,0.7,0.35,1),7)
        for k,x in enumerate((0.55,0.0,-0.55)): curve([(0,0.2,0.95,1),(x*0.3,0.0,1.6,0.9),(x*0.8,-0.4,2.3,0.7),(x,-0.6,2.1,0.5)],0.03,sm,'st%d'%k)
    light('POINT',(0,0.2,1.3),180,(1,0.65,0.3),size=0.4); light('SPOT',(0,0.5,8),2500,(0.75,0.72,1),(0,0,0),size=1.5,spot=38); light('AREA',(-4,-3,3),150,(0.5,0.55,1),(60,0,-50),size=3)
    fog((0,0,3),(7,7,4.5),0.02)
    if hero: c.location=(0,-9.5,4.6)
    return c
def sc_armillary():
    reset(1024,1024,True); c=camera((0,-5,1.2),(78,0,0),lens=50)
    for i,(r,tilt,yaw) in enumerate(((1.25,72,0),(1.55,60,40),(1.05,85,-30))):
        bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=0.016,location=(0,0,0),rotation=(math.radians(tilt),0,math.radians(yaw))); assign(bpy.context.object,mat('r%d'%i,base=GOLD,emit=GOLD,es=6))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06); assign(bpy.context.object,emis('c',CORE,10))
    return c
def sc_theater(hero=False,candles=False,words=False):
    reset(); c=camera((0,-12.5,2.6),(83,0,0),lens=30 if not hero else 26,dof=10,fs=4)
    floor=mat('floor',base=(0.035,0.025,0.05,1),rough=0.35,coat=0.4)
    bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,0)); assign(bpy.context.object,floor)
    bpy.ops.mesh.primitive_plane_add(size=30,location=(0,6,8),rotation=(math.radians(90),0,0)); assign(bpy.context.object,mat('wall',base=(0.01,0.01,0.02,1),rough=0.9))
    vel=mat('velvet',base=(0.16,0.05,0.22,1),rough=0.7,sheen=1)
    for side in (-1,1):
        bpy.ops.mesh.primitive_plane_add(size=1,location=(side*3.4,1.2,4.5),rotation=(math.radians(90),0,0)); cu=bpy.context.object; cu.scale=(2.6,9,1)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=60); bpy.ops.object.mode_set(mode='OBJECT')
        w=cu.modifiers.new('w','WAVE'); w.use_normal=False; w.use_y=False; w.use_x=True; w.height=0.18; w.width=0.25; w.narrowness=1.2; w.speed=0
        cu.modifiers.new('s','SOLIDIFY').thickness=0.03; bpy.ops.object.shade_smooth(); assign(cu,vel)
    bpy.ops.mesh.primitive_plane_add(size=1,location=(0,1.15,8.4),rotation=(math.radians(90),0,0)); v=bpy.context.object; v.scale=(9,1.6,1); assign(v,vel)
    gl=mat('trim',base=GOLD,emit=GOLD,es=3.5)
    curve([(-5,1.0,0.02,1),(-5,1.0,7.4,1),(0,1.0,7.9,1),(5,1.0,7.4,1),(5,1.0,0.02,1)],0.035,gl,'arch')
    curve([(-4.5,-0.6,0.03,1),(4.5,-0.6,0.03,1)],0.02,mat('rim',base=GOLD,emit=GOLD,es=6),'rim')
    # the house: tiered rows below and in front of the stage
    seat=mat('seat',base=(0.16,0.06,0.2,1),rough=0.55,sheen=1.0); step=mat('step',base=(0.05,0.035,0.07,1),rough=0.7)
    light('AREA',(0,-2.2,2.6),90,(1,0.72,0.5),(-50,0,0),size=9); light('AREA',(-7,-6,2),60,(0.6,0.4,1),(-90,0,-70),size=4); light('AREA',(7,-6,2),60,(0.6,0.4,1),(-90,0,70),size=4)
    cm=emis('flame',(1,0.72,0.4,1),12); random.seed(5)
    for r in range(5):
        y=-3.0-r*1.25; z=-1.2+r*0.42
        bpy.ops.mesh.primitive_cube_add(location=(0,y,z-0.35)); s=bpy.context.object; s.scale=(7.5,0.62,0.35); assign(s,step)
        n=14+r*2
        for i in range(n):
            x=-6.6+13.2*(i+0.5+(0.5 if r%2 else 0))/(n+0.5)
            bpy.ops.mesh.primitive_cube_add(location=(x,y+0.15,z+0.18)); b=bpy.context.object; b.scale=(0.26,0.12,0.3); bv=b.modifiers.new('b','BEVEL'); bv.width=0.09; bv.segments=2; assign(b,seat)
            if candles and random.random()<0.82:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035,location=(x,y-0.2,z+0.05)); f=bpy.context.object; f.scale=(0.7,0.7,1.5); assign(f,cm)
    if words:
        for i,(w,x,z) in enumerate((('קפה',-1.6,2.5),('לחם',1.5,2.9),('תודה',0.0,3.6))): heb(w,(x,-0.4,z),0.55,emis('sw%d'%i,CORE,7))
    light('AREA',(-6,-2,5),110,(0.75,0.4,1),(70,0,-60),size=4); light('AREA',(6,-2,5),110,(0.75,0.4,1),(70,0,60),size=4)
    light('SPOT',(0,-1.0,9.5),5000,(1,0.86,0.7),(8,0,0),size=0.6,spot=24); light('AREA',(0,-8,4),30,(0.5,0.5,1),(70,0,0),size=6)
    fog((0,-1,4.5),(9,9,6),0.03,(0.8,0.78,1,1)); return c
def sc_lake(hero=False,gate_word=None):
    reset(); c=camera((0,-6.5,2.0),(81,0,0),lens=30 if not hero else 24,dof=7,fs=4); backdrop(c,dist=70,size=90 if not hero else 220,asp=0.5625 if not hero else 1.78)
    wm=bpy.data.materials.new('water');wm.use_nodes=True;N=wm.node_tree.nodes;p=N['Principled BSDF'];p.inputs['Base Color'].default_value=(0.004,0.004,0.012,1);p.inputs['Roughness'].default_value=0.03;p.inputs['Metallic'].default_value=0.0
    wt=N.new('ShaderNodeTexWave');wt.inputs['Scale'].default_value=1.6;wt.inputs['Distortion'].default_value=3;bp=N.new('ShaderNodeBump');bp.inputs['Strength'].default_value=0.03;wm.node_tree.links.new(wt.outputs['Fac'],bp.inputs['Height']);wm.node_tree.links.new(bp.outputs['Normal'],p.inputs['Normal'])
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,40,-0.02)); assign(bpy.context.object,wm)
    glass=mat('glass',base=(0.85,0.86,1,1),rough=0.1,trans=1,coat=1); lit=int(30 if hero else 0)
    for i in range(30):
        t=i/29; y=-2+t*42; x=math.sin(t*4.2)*1.6*(1-t*0.5)-0.6*(1-t)
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=0.55*(1-0.35*t),depth=0.12,location=(x,y,0.04)); s=bpy.context.object
        bv=s.modifiers.new('b','BEVEL'); bv.width=0.04; bv.segments=3; bpy.ops.object.shade_smooth(); assign(s,glass)
        e=(0.8+2.5*t) if not hero else 5
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=0.32*(1-0.35*t),depth=0.02,location=(x,y,0.11)); assign(bpy.context.object,mat('g%d'%i,base=GOLD,emit=GOLD,es=e))
    pil=mat('pillar',base=(0.85,0.86,1,1),rough=0.05,trans=1,coat=1,)
    for sx in (-3.2,3.2):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=0.28,depth=7,location=(sx,44,3.5)); assign(bpy.context.object,pil)
        curve([(sx,43.7,0,1),(sx,43.7,7,1)],0.04,emis('pv',GOLDE,4),'pv')
    curve([(-3.6,43.7,7.0,1),(0,43.7,8.6,1),(3.6,43.7,7.0,1)],0.06,emis('lint',CORE,6),'lint')
    if gate_word: heb(gate_word,(0,43.6,3.8),2.6,emis('gw',CORE,10))
    light('AREA',(0,-4,6),200,(0.6,0.6,1),(40,0,0),size=8); light('POINT',(0,42,4),800,(1,0.8,0.5),size=2)
    fog((0,20,2.5),(16,30,5),0.008); return c
def sc_dial(hero=False):
    reset()
    if hero: c=camera((0,-3.2,6.2),(28,0,0),lens=32,dof=6.8,fs=4); bpy.ops.mesh.primitive_plane_add(size=1,location=(0,8,-6),rotation=(math.radians(62),0,0))
    else: c=camera((0,-0.29,13.4),(0,0,0),lens=50); bpy.ops.mesh.primitive_plane_add(size=1,location=(0,0,-6))
    bk=bpy.context.object; bk.scale=(40,40,1); assign(bk,sky_mat())
    br=bpy.data.materials.new('bronze');br.use_nodes=True;p=br.node_tree.nodes['Principled BSDF'];I=p.inputs;I['Base Color'].default_value=(0.42,0.26,0.12,1);I['Metallic'].default_value=1;I['Roughness'].default_value=0.36
    try: I['Anisotropic'].default_value=0.6
    except: pass
    bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=2.3,depth=0.18,location=(0,0,0)); d=bpy.context.object; bv=d.modifiers.new('b','BEVEL'); bv.width=0.05; bv.segments=4; bpy.ops.object.shade_smooth(); assign(d,br)
    ob=mat('obs',base=(0.012,0.01,0.025,1),rough=0.16,coat=0.6)
    bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.55,depth=0.2,location=(0,0,0.02)); assign(bpy.context.object,ob)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.56,minor_radius=0.02,location=(0,0,0.12)); assign(bpy.context.object,mat('rim',base=GOLD,emit=GOLD,es=3))
    pat=mat('pat',base=(0.08,0.05,0.025,1),rough=0.7)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.92,minor_radius=0.035,location=(0,0,0.09)); assign(bpy.context.object,pat)
    for i in range(24):
        a=i/24*6.283; L=0.16 if i%2==0 else 0.08
        bpy.ops.mesh.primitive_cube_add(location=(math.cos(a)*2.12,math.sin(a)*2.12,0.085),rotation=(0,0,a)); m=bpy.context.object; m.scale=(L,0.012,0.01); assign(m,pat)
    if hero:
        fz=emis('fuse',CORE,6); pts=[(math.cos(math.radians(90+k*6))*1.45,math.sin(math.radians(90+k*6))*1.45,0.14,1) for k in range(0,36)]
        curve(pts,0.012,fz,'fuse')
        em=emis('ember',(1,0.55,0.2,1),30); ex,ey=pts[-1][0],pts[-1][1]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,location=(ex,ey,0.16)); assign(bpy.context.object,em)
        light('POINT',(ex,ey,0.35),40,(1,0.5,0.2),size=0.05); random.seed(9)
        for k in range(26):
            a=random.random()*6.283; r=random.uniform(0.1,0.5)
            bpy.ops.mesh.primitive_ico_sphere_add(radius=random.uniform(0.006,0.014),location=(ex+math.cos(a)*r,ey+math.sin(a)*r,0.16+random.random()*0.3)); assign(bpy.context.object,emis('sp%d'%k,(1,0.62,0.3,1),random.uniform(6,18)))
        heb('פרי',(0,0,0.13),0.55,emis('pw',GOLDE,4),rot=(0,0,0))
    light('AREA',(4,3,3.5),420,(1,0.85,0.65),(55,0,125),size=3); light('AREA',(-4,-2,4),90,(0.55,0.5,1),(45,0,-60),size=4)
    return c
def sc_pilot():
    reset(); c=camera((0,0,0),(88,0,0),lens=16)
    bpy.ops.mesh.primitive_plane_add(size=1,location=(0,40,6),rotation=(math.radians(90),0,0)); bk=bpy.context.object; bk.scale=(110,70,1); assign(bk,sky_mat(aurora=0.0,stars=1.6))
    fl=emis('fl',GOLDE,3); random.seed(4); pts=[]
    for i in range(12):
        t=i/11; x=13-t*26; z=2.5+math.sin(t*math.pi)*5+random.uniform(-0.6,0.6); pts.append((x,30,z,1))
    curve(pts,0.018,fl,'path',res=4)
    for i,p in enumerate(pts):
        ok=i not in (3,8)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14 if ok else 0.06,location=p[:3]); assign(bpy.context.object,emis('s%d'%i,CORE if ok else LAV,40 if ok else 6))
    return c
def sc_body():
    reset(); c=camera((0,-5.2,1.15),(88,0,0),lens=50,dof=5.2,fs=2.8); backdrop(c,dist=30,size=60,asp=1.78)
    bpy.ops.mesh.primitive_plane_add(size=40,location=(0,0,0)); assign(bpy.context.object,mat('gr',base=(0.004,0.004,0.01,1),rough=0.08,coat=1))
    J={'hd':(0.05,0,1.86),'N':(0,0,1.62),'SL':(-0.17,0,1.56),'SR':(0.17,0,1.56),'eL':(-0.3,0,1.26),'eR':(0.36,0,1.4),'hL':(-0.26,0,0.98),'hR':(0.12,0,1.72),'hip':(0,0,1.02),'HL':(-0.11,0,1.0),'HR':(0.11,0,1.0),'kL':(-0.13,0,0.54),'kR':(0.15,0,0.54),'fL':(-0.14,0,0.06),'fR':(0.17,0,0.06)}
    jm=emis('j',CORE,30); bm=emis('bone',GOLDE,3)
    for k,v in J.items():
        if k=='hd': continue
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022,location=v); assign(bpy.context.object,jm)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.11,minor_radius=0.008,location=J['hd'],rotation=(math.radians(90),0,0)); assign(bpy.context.object,jm)
    for a,b in (('hip','N'),('SL','SR'),('SL','eL'),('eL','hL'),('SR','eR'),('eR','hR'),('HL','HR'),('HL','kL'),('kL','fL'),('HR','kR'),('kR','fR')):
        A,B=J[a],J[b]; curve([(A[0],A[1],A[2],1),(B[0],B[1],B[2],1)],0.004,bm,'b')
    tm=emis('trail',GOLDE,6)
    tr=[(0.12+0.25*math.cos(t*2.2),0,1.0+0.72*t+0.08*math.sin(t*6),0.2+t) for t in [i/20 for i in range(21)]]
    curve(tr,0.008,tm,'trail')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045,depth=0.11,location=(0.15,0,1.74)); assign(bpy.context.object,emis('cup',GOLDE,3))
    heb('שתה',(0,0.2,2.35),0.32,emis('w',CORE,9)); light('AREA',(2,-3,3),60,(1,0.85,0.7),(60,0,35),size=3)
    fog((0,0,0.3),(4,4,0.6),0.02); return c
def sc_duet():
    reset(); c=camera((0,-10,1.4),(92,0,0),lens=24,dof=10,fs=2.8); backdrop(c,dist=30,size=110,asp=1.78,aurora=0.8)
    hm=emis('her',GOLDE,5); ym=emis('you',LAV,3); random.seed(2)
    her=[(x*0.5,0,2.2+0.35*math.sin(x*1.3)*math.exp(-((x-1)/5)**2)*random.uniform(.6,1.2),1) for x in range(-16,17)]
    you=[(x*0.5,0,1.1+0.25*math.sin(x*1.1+0.5)*random.uniform(.6,1.2),1) for x in range(-16,17)]
    curve(her,0.02,hm,'her'); curve(you,0.016,ym,'you')
    for k in range(70):
        x=random.uniform(-2.5,0.5); z=random.uniform(1.2,2.2)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=random.uniform(0.008,0.02),location=(x,0,z)); assign(bpy.context.object,emis('m%d'%k,CORE,random.uniform(5,20)))
    heb('תודה רבה',(0,0.1,3.35),1.0,emis('w',CORE,9)); return c
def render_to(name):
    bpy.context.scene.render.filepath=os.path.join(OUT,name+'.png'); t=__import__('time').time(); bpy.ops.render.render(write_still=True); print('RENDERED',name,round(__import__('time').time()-t,1),'s')
PLATES2={'theater3':lambda:sc_theater(),'dial2':lambda:sc_dial()}
PLATES={'sky':lambda:sc_sky(),'tree':lambda:sc_tree(),'lab':lambda:sc_lab(),'theater':lambda:sc_theater(),'path':lambda:sc_lake(),'dial':lambda:sc_dial()}
HEROES={'H1_duet':sc_duet,'H2_fuse':lambda:sc_dial(True),'H3_pilot':sc_pilot,'H4_roots':lambda:sc_tree(True,True),'H5_body':sc_body,'H6_then':lambda:sc_lake(True,'שלום'),'H7_alchemy':lambda:sc_lab(True,True,True),'H8_theater':lambda:sc_theater(True,True,True)}
mode=os.environ.get('FSH_MODE','plates'); samples=int(os.environ.get('FSH_SAMPLES','96'))
if mode=='plates':
    for k,f in PLATES.items():
        if want(k): f(); size(1080,1920); render_to('P_'+k)
    if want('armillary'): sc_armillary(); render_to('P_armillary')
    for k,f in PLATES2.items():
        if want(k): f(); size(1080,1920); render_to('P_'+k)
else:
    for k,f in HEROES.items():
        if want(k): f(); size(3840,2160,mode=='cycles',samples); render_to(k)
print('ALL DONE')
