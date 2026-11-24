# Free Speech in Hebrew: night-stage plates. Run: blender -b -P stage.py -- OUTDIR [names]
import bpy, math, random, sys, os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; OUT=a[0]; ONLY=set(a[1:])
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
def backdrop(cam,dist=40,size=60,**kw):
    bpy.ops.mesh.primitive_plane_add(size=1); p=bpy.context.object; p.scale=(size*0.5625,size,1)
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

# 1 SKY: shared night plate
if want('sky'):
    reset(); c=camera((0,-10,1.2),(92,0,0),lens=28); backdrop(c,dist=30,size=40)
    # a far glass horizon: thin luminous arc
    m=mat('hz',base=(0.2,0.2,0.35,1),rough=0.1,trans=1,emit=(0.6,0.55,1,1),es=0.6)
    bpy.ops.mesh.primitive_torus_add(major_radius=30,minor_radius=0.03,location=(0,30,-29.2)); assign(bpy.context.object,m)
    render('sky')

# 2 TREE: crystalline root organism (branches are drawn live by the app)
if want('tree'):
    reset(); c=camera((0,-9,1.1),(90,0,0),lens=40,dof=9,fs=4); backdrop(c,dist=26,size=36,aurora=0.7)
    glass=mat('glass',base=(0.85,0.85,1,1),rough=0.04,trans=1,ior=1.45,coat=1)
    vein=mat('vein',base=GOLD,emit=GOLD,es=7)
    trunk=[(0,0,-3.5,1.6),(0,0,-2.4,1.35),(0.05,0,-1.4,1.15),(0,0,-0.6,1.0),(0,0,-0.1,0.95)]
    curve(trunk,0.32,glass,'trunk'); curve([(x*0.25,y,z,r*0.3) for x,y,z,r in trunk],0.32,vein,'core')
    for k,ang in enumerate((-55,0,55)):
        a=math.radians(ang); pts=[(0,0,-3.3,0.8)]
        for i in range(1,6):
            t=i/5; pts.append((math.sin(a)*2.6*t,-0.2*t,-3.3-1.9*t+0.3*math.sin(t*3),0.8-0.6*t))
        curve(pts,0.22,glass,'root%d'%k); curve([(x,y-0.02,z,r*0.25) for x,y,z,r in pts],0.22,vein,'rv%d'%k)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42,location=(math.sin(a)*2.6,-0.2,-5.25)); s=bpy.context.object; bpy.ops.object.shade_smooth(); assign(s,mat('seed%d'%k,base=GOLD,emit=GOLD,es=1.0,rough=0.3))
    light('AREA',(3,-4,3),300,(0.7,0.7,1),(60,0,30),size=4); light('POINT',(0,-1.5,-4.5),25,(1,0.75,0.4),size=1)
    fog((0,0,-2),(8,6,6),0.015)
    c.location=(0,-10.5,-1.6); c.data.lens=34; render('tree2')

# 3 LAB: floating alchemy laboratory above the night
if want('lab'):
    reset(); c=camera((0,-7.5,4.2),(62,0,0),lens=32,dof=7.8,fs=3.2); backdrop(c,dist=30,size=44,aurora=0.9)
    stone=mat('stone',base=(0.04,0.035,0.07,1),rough=0.55,coat=0.3)
    goldm=mat('gold',base=GOLD,metal=1,rough=0.22)
    glass=mat('glass',base=(0.9,0.9,1,1),rough=0.03,trans=1,coat=1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=3.4,depth=0.5,location=(0,0,0)); slab=bpy.context.object
    bv=slab.modifiers.new('b','BEVEL'); bv.width=0.08; bv.segments=4; bpy.ops.object.shade_smooth(); assign(slab,stone)
    bpy.ops.mesh.primitive_torus_add(major_radius=3.42,minor_radius=0.035,location=(0,0,0.25)); assign(bpy.context.object,mat('rim',base=GOLD,emit=GOLD,es=5))
    # crucible
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=0.75,depth=0.8,location=(0,0.2,0.65)); cr=bpy.context.object
    so=cr.modifiers.new('s','SOLIDIFY'); so.thickness=0.06; bv=cr.modifiers.new('b','BEVEL'); bv.width=0.03; bv.segments=3; bpy.ops.object.shade_smooth(); assign(cr,goldm)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=0.68,depth=0.05,location=(0,0.2,0.88)); assign(bpy.context.object,mat('melt',base=GOLD,emit=(1,0.62,0.25,1),es=9))
    # alembic
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6,location=(-1.9,0.9,0.85)); bpy.ops.object.shade_smooth(); assign(bpy.context.object,glass)
    curve([(-1.9,0.9,1.4,1),(-1.85,0.9,2.0,0.8),(-1.3,0.85,2.3,0.6),(-0.6,0.6,2.0,0.5)],0.07,glass,'neck')
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.32,location=(-1.9,0.9,0.7)); bpy.ops.object.shade_smooth(); assign(bpy.context.object,mat('elix',base=(0.4,0.3,0.9,1),emit=(0.45,0.35,1,1),es=3))
    # vials
    for i,x in enumerate((1.6,2.05,2.5)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=0.13,depth=0.7,location=(x,1.0-0.25*i,0.6)); bpy.ops.object.shade_smooth(); assign(bpy.context.object,glass)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=0.11,depth=0.3,location=(x,1.0-0.25*i,0.42)); assign(bpy.context.object,mat('v%d'%i,base=GOLD,emit=(0.9,0.7,0.4,1),es=1.5+i))
    # floating orbit rings around crucible
    for i,(r,tilt) in enumerate(((1.25,12),(1.55,-18))):
        bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=0.012,location=(0,0.2,1.6+i*0.25),rotation=(math.radians(tilt),math.radians(tilt*0.5),0)); assign(bpy.context.object,mat('ring%d'%i,base=GOLD,emit=GOLD,es=6))
    light('POINT',(0,0.2,1.3),180,(1,0.65,0.3),size=0.4); light('SPOT',(0,0.5,8),2500,(0.75,0.72,1),(0,0,0),size=1.5,spot=38); light('AREA',(-4,-3,3),150,(0.5,0.55,1),(60,0,-50),size=3)
    fog((0,0,3),(7,7,4.5),0.02)
    render('lab')

# 4 THEATER: black-box stage, velvet curtains, one spotlight
if want('theater'):
    reset(); c=camera((0,-9.5,1.7),(86,0,0),lens=30,dof=8,fs=4)
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
    # stage-front rim light strip
    curve([(-4.5,-0.6,0.03,1),(4.5,-0.6,0.03,1)],0.02,mat('rim',base=GOLD,emit=GOLD,es=6),'rim')
    light('AREA',(-6,-2,5),110,(0.75,0.4,1),(70,0,-60),size=4); light('AREA',(6,-2,5),110,(0.75,0.4,1),(70,0,60),size=4)
    light('SPOT',(0,-1.0,9.5),5000,(1,0.86,0.7),(8,0,0),size=0.6,spot=24); light('AREA',(0,-6,4),40,(0.5,0.5,1),(70,0,0),size=6)
    fog((0,1,4.5),(8,6,6),0.03,(0.8,0.78,1,1))
    render('theater3')

# 5 TIMELINE: thirty glass stepping stones toward the horizon
if want('path'):
    reset(); c=camera((0,-6.5,2.4),(80,0,0),lens=30,dof=7,fs=4); backdrop(c,dist=60,size=80)
    glass=mat('glass',base=(0.85,0.86,1,1),rough=0.05,trans=1,coat=1)
    for i in range(30):
        t=i/29; y=-2+t*42; x=math.sin(t*4.2)*1.6*(1-t*0.5)-0.6*(1-t)
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=0.55*(1-0.35*t),depth=0.12,location=(x,y,0)); s=bpy.context.object
        bv=s.modifiers.new('b','BEVEL'); bv.width=0.04; bv.segments=3; bpy.ops.object.shade_smooth(); assign(s,glass)
        e=0.8+2.5*t if i<29 else 9
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=0.32*(1-0.35*t),depth=0.02,location=(x,y,0.07)); assign(bpy.context.object,mat('g%d'%i,base=GOLD,emit=GOLD,es=e))
    light('AREA',(0,-4,6),200,(0.6,0.6,1),(40,0,0),size=8)
    fog((0,18,2),(14,26,4),0.008)
    render('path')

# 6 EMBER: the living fuse spark (transparent)
if want('ember'):
    reset(512,512,True); c=camera((0,-4,0),(90,0,0),lens=50)
    m=bpy.data.materials.new('ember'); m.use_nodes=True; N=m.node_tree.nodes; L=m.node_tree.links; N.remove(N['Principled BSDF'])
    lw=N.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value=0.35
    ramp=N.new('ShaderNodeValToRGB'); r=ramp.color_ramp; r.elements[0].color=(1,0.62,0.25,1); r.elements[1].color=(0.55,0.12,0.02,1); L.new(lw.outputs['Facing'],ramp.inputs[0])
    em=N.new('ShaderNodeEmission'); em.inputs[1].default_value=2.2; L.new(ramp.outputs[0],em.inputs[0]); L.new(em.outputs[0],N['Material Output'].inputs[0])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.32,segments=64,ring_count=32); bpy.ops.object.shade_smooth(); assign(bpy.context.object,m)
    for i in range(40):
        a=random.random()*6.283; rr=0.45+random.random()*0.5
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.012+random.random()*0.02,location=(math.cos(a)*rr,0,math.sin(a)*rr)); assign(bpy.context.object,mat('s%d'%i,base=GOLD,emit=(1,0.6,0.25,1),es=1.5*random.random()+0.8))
    render('ember')
print('ALL DONE')
