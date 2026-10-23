"""Fail-closed public version-only OSV gate; never send installer settings or I/O."""
import argparse
import json
from pathlib import Path
import re
import ssl
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def queries(root=ROOT):
    pins=re.findall(r'^([\w-]+)==([\w.]+)',(root/'packaging/windows/requirements-lock.txt').read_text(),re.M)
    packages={('PyPI',name,version) for name,version in pins}
    packages.add(('NuGet','Velopack','1.2.161'))
    lock=json.loads((root/'cloudflare/package-lock.json').read_text())
    for path,value in lock['packages'].items():
        if path and value.get('version'):
            packages.add(('npm',value.get('name') or path.rsplit('node_modules/',1)[-1],value['version']))
    return [{'package':{'ecosystem':e,'name':n},'version':v} for e,n,v in sorted(packages)]


def audit(items):
    import certifi
    opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    request=urllib.request.Request('https://api.osv.dev/v1/querybatch',data=json.dumps({'queries':items}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(request,timeout=45) as response:
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError('Dependency response too large.')
    results=json.loads(raw)['results']
    if len(results)!=len(items):raise ValueError('Incomplete dependency response.')
    hits=[{'package':q['package'],'version':q['version'],'ids':[v['id'] for v in r.get('vulns',[])]} for q,r in zip(items,results) if r.get('vulns')]
    return {'queries':len(items),'advisories':hits,'passed':not hits}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
    report=audit(queries())
    if args.output:
        path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
