"""Blender headless: printable landscape phone carrier, independent neck interface."""
import bpy, bmesh, json, struct
from pathlib import Path
OUT=Path(__file__).resolve().parent/'generated'; OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=.001
def box(name,x0,x1,y0,y1,z0,z1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
    o=bpy.context.object;o.name=name;o.dimensions=(x1-x0,y1-y0,z1-z0)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def cyl(x,y,z0,z1,r):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=z1-z0,location=(x,y,(z0+z1)/2))
    return bpy.context.object
def op(a,b,mode):
    bpy.context.view_layer.objects.active=a
    m=a.modifiers.new(mode,'BOOLEAN');m.operation=mode;m.solver='EXACT';m.object=b
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(b,do_unlink=True);return a
def fuse(a,*parts):
    for b in parts:op(a,b,'UNION')
    return a
def stats(o):
    bm=bmesh.new();bm.from_mesh(o.data);remain=set(bm.verts);components=0
    while remain:
        todo=[remain.pop()];components+=1
        while todo:
            for e in todo.pop().link_edges:
                for v in e.verts:
                    if v in remain:remain.remove(v);todo.append(v)
    r=dict(dimensions_mm=[round(x,3) for x in o.dimensions],volume_mm3=round(abs(bm.calc_volume(signed=True)),2),non_manifold_edges=sum(not e.is_manifold for e in bm.edges),connected_components=components)
    bm.free();return r
def export(o,path):
    # Binary STL in millimetres, independent of Blender exporter version.
    o.data.calc_loop_triangles()
    with path.open('wb') as f:
        f.write(b'Qmini J2 carrier, mm'.ljust(80,b' '))
        f.write(struct.pack('<I',len(o.data.loop_triangles)))
        for tri in o.data.loop_triangles:
            a,b,c=[o.matrix_world @ o.data.vertices[i].co for i in tri.vertices]
            n=(b-a).cross(c-a).normalized()
            f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
def mat(name,col):
    m=bpy.data.materials.new(name);m.diffuse_color=col;return m
white=mat('Ivory PETG',(.87,.9,.93,1));black=mat('J2 envelope',(.03,.04,.06,1))
base=box('J2_carrier',-80,80,-36,-25,0,3.2)
fuse(base,box('top rail',-80,80,25,36,0,3.2),box('centre brace',-20,20,-30,30,0,3.2))
for x in [-75,75]:
    for y in [-30,30]:op(base,cyl(x,y,-1,4.2,1.7),'DIFFERENCE')
for x in [-15,15]:
    for y in [-15,15]:
        op(base,cyl(x,y,-1,4.2,1.7),'DIFFERENCE')
        # counterbore on phone-facing side; verify screw head is flush
        op(base,cyl(x,y,1.45,4.3,3.2),'DIFFERENCE')
base.data.materials.append(white);parts=[base]
for sx in [-1,1]:
    for sy in [-1,1]:
        def rect(name,xa,xb,ya,yb,za,zb):
            return box(name,*sorted((sx*xa,sx*xb)),*sorted((sy*ya,sy*yb)),za,zb)
        c=rect('retainer',68.9,80,23,36,3.2,14.8)
        fuse(c,rect('front lip',65.5,71,24,34.5,12.25,14.8),rect('side stop',63,70.5,35.15,38,3.2,12.8))
        op(c,cyl(sx*75,sy*30,2.2,15.8,1.7),'DIFFERENCE')
        c.name='Retainer_%s%s'%('L' if sx<0 else 'R','B' if sy<0 else 'T')
        c.data.materials.append(white);parts.append(c)
phone=box('Bare_SM-J200Y_reference_NOT_PRINT',-68.25,68.25,-34.5,34.5,3.2,11.6);phone.data.materials.append(black)
report={}
for o in parts:
    report[o.name]=stats(o)
    assert report[o.name]['non_manifold_edges']==0 and report[o.name]['connected_components']==1,report
    clone=o.copy();clone.data=o.data.copy();bpy.context.collection.objects.link(clone)
    gauge=phone.copy();gauge.data=phone.data.copy();bpy.context.collection.objects.link(gauge)
    op(clone,gauge,'INTERSECT')
    report[o.name]['phone_intersection_mm3']=stats(clone)['volume_mm3']
    assert report[o.name]['phone_intersection_mm3']<.01,report
    bpy.data.objects.remove(clone,do_unlink=True)
    p=o.copy();p.data=o.data.copy();bpy.context.collection.objects.link(p)
    bpy.ops.object.select_all(action='DESELECT');p.select_set(True);bpy.context.view_layer.objects.active=p
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS');p.location=(0,0,p.dimensions.z/2)
    bpy.context.view_layer.update();export(p,OUT/(o.name+'.stl'));bpy.data.objects.remove(p,do_unlink=True)
report['assumptions']={'phone_mm':[136.5,69,8.4],'edge_clearance_mm':.65,'front_lip_clearance_mm':.65,'interface':'30 x 30 mm M3 square on carrier; robot-side adapter unverified','fasteners':'4 M3 through-bolts with locking nuts for retainers; 4 M3 for adapter','filament':'PETG recommended; no physical load test'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Qmini_J2_head.blend'))
print(json.dumps(report,indent=2))
