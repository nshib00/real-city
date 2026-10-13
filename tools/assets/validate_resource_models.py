"""Validate catalog completeness, GLB topology and rendered resource icons."""
import argparse
import json
import subprocess
import tarfile
from pathlib import Path

from PIL import Image, ImageDraw
from validate_building_ground import read_glb
from validate_town_halls import validate_topology

ROOT=Path(__file__).resolve().parents[2]


def catalog():
    script="""
import ts from 'typescript';
import fs from 'node:fs';
const source=fs.readFileSync('../shared/catalog/resources.ts','utf8');
const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const {resourceCatalog}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
console.log(JSON.stringify(resourceCatalog));
"""
    result=subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT/'frontend',capture_output=True,text=True,check=True)
    return json.loads(result.stdout)


def validate(directory, before=None):
    manifest=json.loads((directory/'manifest.json').read_text())
    resources=catalog()
    records={r['id']:r for r in manifest['resources']}
    catalog_ids={r['id'] for r in resources}
    assert catalog_ids.issubset(set(records))
    modeled_ids={r['id'] for r in manifest['resources'] if r.get('model')}
    assert modeled_ids.issubset({p.stem for p in directory.glob('*.glb')})
    cols=6
    rows=(len(manifest['resources'])+cols-1)//cols
    sheet=Image.new('RGB',(cols*160,rows*178),'#233b34');draw=ImageDraw.Draw(sheet)
    small=Image.new('RGB',(cols*160,rows*80),'#233b34');small_draw=ImageDraw.Draw(small)
    results=[]
    catalog_by_id={r['id']:r for r in resources}
    for i,record in enumerate(manifest['resources']):
        rid=record['id']
        if rid in catalog_by_id:
            item=catalog_by_id[rid]
            assert record['name']==item['name'] and record['category']==item['category'],rid
        triangles=None
        path=None
        if record.get('model'):
            path=directory/record['model'];doc,_=read_glb(path)
            validate_topology(path,doc)
            triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
            assert triangles==record['triangles'] and 300<triangles<24000,(rid,triangles)
            assert len(doc['scenes'])==1 and doc.get('materials'),rid
            for node in doc['nodes']:
                assert node.get('translation',[0,0,0])==[0,0,0],rid
                assert node.get('scale',[1,1,1])==[1,1,1],rid
        with Image.open(directory/record['file']) as im:
            assert im.size==(256,256) and im.mode=='RGBA',rid
            box=im.getchannel('A').getbbox()
            assert box and min(box[:2])>=12 and max(box[2:])<=244,(rid,box)
            assert max(box[2]-box[0],box[3]-box[1])>=195,(rid,box)
            assert im.getpixel((0,0))[3]==0,rid
            thumb=im.resize((144,144),Image.Resampling.LANCZOS)
            x,y=(i%cols)*160,(i//cols)*178
            sheet.paste(thumb,(x+8,y+4),thumb);draw.text((x+8,y+152),rid,fill='white')
            x,y=(i%cols)*160,(i//cols)*80
            for size,offset in ((24,8),(32,42),(48,84)):
                thumb=im.resize((size,size),Image.Resampling.LANCZOS)
                small.paste(thumb,(x+offset,y+4),thumb)
            small_draw.text((x+8,y+58),rid,fill='white')
        results.append({'id':rid,'triangles':triangles,'alpha_bounds':box,
                        'bytes':path.stat().st_size if path else (directory/record['file']).stat().st_size,
                        'mode':'glb+png' if path else 'png'})
    reverse=json.loads((directory/'roundtrip-validation.json').read_text())
    assert reverse=={'models':len(modeled_ids),'nonmanifold_edges':0,'triangles_matched':True}
    assert (directory/'resource_icons.blend').stat().st_size>1000
    if before:
        with tarfile.open(before) as archive:
            prefix='frontend/public/assets/resources/icons/'
            for name in [r['file'] for r in records.values()]+['resource_icons.blend']:
                assert archive.extractfile(prefix+name).read()!=(directory/name).read_bytes(),('Not regenerated',name)
    sheet.save(directory/'resource_icons_contact_sheet.png')
    small.save(directory/'resource_icons_small_review.png')
    (directory/'validation-report.json').write_text(json.dumps(results,indent=2)+'\n')
    triangle_counts=[r['triangles'] for r in results if r['triangles']]
    print(json.dumps({'resources':len(results),'models':len(modeled_ids),'max_triangles':max(triangle_counts),
                      'total_glb_bytes':sum(r['bytes'] for r in results),'catalog_complete':True}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path,default=ROOT/'frontend/public/assets/resources/icons')
    parser.add_argument('--before',type=Path)
    args=parser.parse_args()
    validate(args.directory,args.before)
