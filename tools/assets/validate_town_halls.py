"""Validate every regenerated town hall and make level/state review sheets."""
import json
import struct
import tarfile
from collections import Counter
from pathlib import Path

from PIL import Image,ImageDraw
from validate_early_housing import glb_document

ROOT=Path(__file__).resolve().parents[2]
MODELS=ROOT/'frontend/src/assets/buildings/center/town_hall'
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
    report=json.loads((MODELS/'state-revision-report.json').read_text())
    assert len(report)==30,len(report)
    roundtrip=json.loads((PNG/'roundtrip-validation.json').read_text())
    assert {entry['name'] for entry in roundtrip}==set(report)
    assert all(entry['nonmanifold_edges']==0 and entry['triangles']==report[entry['name']]['triangles'] for entry in roundtrip)
    sheet=Image.new('RGB',(768,2140),'#25372f');draw=ImageDraw.Draw(sheet)
    progression=Image.new('RGB',(1280,428),'#25372f');labels=ImageDraw.Draw(progression)
    results=[]
    with tarfile.open('/tmp/real-city-townhall-before.tar') as backup:
        for level in range(1,11):
            for col,state in enumerate(('active','construction','damaged')):
                name=f'town_hall_l{level:02d}_{state}'
                for path in (MODELS/(name+'.glb'),PNG/(name+'.png')):
                    assert backup.extractfile(str(path.relative_to(ROOT))).read()!=path.read_bytes(),path
                doc=glb_document(MODELS/(name+'.glb'))
                validate_topology(MODELS/(name+'.glb'),doc)
                assert len(doc['scenes'])==1,name
                tris=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
                assert tris==report[name]['triangles'] and 1000<tris<14000,(name,tris)
                assert all(abs(v)<1.801 for corner in report[name]['bounds'] for v in corner[:2]),name
                for node in doc['nodes']:
                    assert node.get('translation',[0,0,0])==[0,0,0],name
                    assert node.get('scale',[1,1,1])==[1,1,1],name
                if state!='active': assert report[name]['structural_edits']>15,name
                with Image.open(PNG/(name+'.png')) as im:
                    assert im.mode=='RGBA' and im.size==(512,384),name
                    box=im.getchannel('A').getbbox()
                    assert box and box[0]>0 and box[1]>0 and box[2]<512 and box[3]<384,(name,box)
                    thumb=im.resize((256,192),Image.Resampling.LANCZOS)
                    sheet.paste(thumb,(col*256,(level-1)*214),thumb)
                    draw.text((col*256+10,(level-1)*214+194),name,fill='white')
                    if state=='active':
                        x=((level-1)%5)*256;y=((level-1)//5)*214
                        progression.paste(thumb,(x,y),thumb)
                        labels.text((x+10,y+194),f'Level {level}',fill='white')
                results.append({'name':name,'triangles':tris,'alpha_bounds':box})
    assert (MODELS/'town_hall_levels.blend').stat().st_size>1000
    glb_document(MODELS/'town_hall_levels.glb')
    sheet.save(PNG/'state-review.png');progression.save(PNG/'levels-review.png')
    (PNG/'generation-validation.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'models':len(results),'max_triangles':max(r['triangles'] for r in results)}))


if __name__=='__main__': validate()
