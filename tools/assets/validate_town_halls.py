"""Validate the installed vertical town hall family."""
import json
import struct
from collections import Counter
from pathlib import Path

from PIL import Image
from validate_early_housing import glb_document
from validate_building_ground import ground_signature, sprite_alignment

ROOT=Path(__file__).resolve().parents[2]
PNG=ROOT/'frontend/public/assets/buildings/center/town_hall'


def validate_topology(path,doc):
    raw=path.read_bytes()
    json_size=struct.unpack_from('<I',raw,12)[0]
    offset=20+json_size
    size,kind=struct.unpack_from('<II',raw,offset)
    assert kind==0x004e4942,path
    data=memoryview(raw)[offset+8:offset+8+size]
    def accessor(index):
        item=doc['accessors'][index];view=doc['bufferViews'][item['bufferView']]
        fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[item['componentType']]
        width={'VEC3':3,'SCALAR':1}[item['type']]
        unpack=struct.Struct('<'+fmt*width)
        start=view.get('byteOffset',0)+item.get('byteOffset',0)
        stride=view.get('byteStride',unpack.size)
        return [unpack.unpack_from(data,start+i*stride) for i in range(item['count'])]
    for mesh in doc['meshes']:
        vertices={};edges=Counter();orientation=Counter()
        for primitive in mesh['primitives']:
            assert primitive.get('mode',4)==4,path
            positions=accessor(primitive['attributes']['POSITION'])
            ids=[]
            for point in positions:
                key=tuple(round(v*1e6) for v in point)
                ids.append(vertices.setdefault(key,len(vertices)))
            indices=[item[0] for item in accessor(primitive['indices'])]
            for i in range(0,len(indices),3):
                triangle=[ids[j] for j in indices[i:i+3]]
                assert len(set(triangle))==3,(path,mesh.get('name'),'degenerate triangle')
                for a,b in zip(triangle,triangle[1:]+triangle[:1]):
                    edge=tuple(sorted((a,b)));edges[edge]+=1
                    orientation[edge]+=1 if a<b else -1
        assert all(count==2 for count in edges.values()),(path,mesh.get('name'),'open/nonmanifold edges')
        assert all(value==0 for value in orientation.values()),(path,mesh.get('name'),'inconsistent winding')


def validate():
    manifest=json.loads((PNG/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['levels']==list(range(1,16))
    assert manifest['states']==['active','construction','damaged']
    assert len(manifest['items'])==45
    assert (ROOT/manifest['backup']).is_file()
    items={item['id']:item for item in manifest['items']}
    results=[]
    for level in range(1,16):
        active_name=f'town_hall_l{level:02d}_active'
        active_ground=ground_signature(PNG/(active_name+'_LOD0.glb'))
        for state in ('active','construction','damaged'):
            name=f'town_hall_l{level:02d}_{state}'
            item=items[name]
            glb=ROOT/item['glb']
            assert glb.is_file() and (ROOT/item['blend']).is_file(),name
            doc=glb_document(glb)
            validate_topology(glb,doc)
            tris=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
            assert tris==item['triangles'] and tris>1000,(name,tris)
            assert all(abs(v)<=1.801 for bounds in item['bounds'][:2] for v in bounds),name
            for lod in item['lods']:
                path=ROOT/lod['glb']
                assert path.is_file() and path.read_bytes()[:4]==b'glTF',path
            with Image.open(ROOT/item['png']) as image:
                assert image.mode=='RGBA' and image.size==(512,384),name
                box=image.getchannel('A').getbbox()
                assert box and box[0]>0 and box[1]>0 and box[2]<512 and box[3]<384,(name,box)
            if state!='active':
                assert ground_signature(glb)==active_ground,name
                assert sprite_alignment(PNG/(active_name+'.png'),ROOT/item['png']),name
            results.append({'name':name,'triangles':tris,'alpha_bounds':box})
    (PNG/'vertical-generation-validation.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'models':len(results),'max_triangles':max(r['triangles'] for r in results)}))


if __name__=='__main__': validate()
