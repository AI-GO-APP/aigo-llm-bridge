"""Refresh published artifact hashes without executing package code."""
import concurrent.futures
import json
from pathlib import Path
import re
import urllib.request

ROOT=Path(__file__).resolve().parents[2]


def main():
    target=ROOT/'packaging/windows/requirements-lock.txt'
    pins=re.findall(r'^([\w-]+)==([\w.]+)',target.read_text(),re.M)
    def hashes(pin):
        name,version=pin
        with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=30) as response:data=json.load(response)
        if data.get('vulnerabilities'):raise ValueError('Published vulnerabilities: '+name)
        values=sorted({item['digests']['sha256'] for item in data['urls'] if not item.get('yanked')})
        if not values:raise ValueError('No published hashes: '+name)
        return f'{name}=={version} \\\n'+ ' \\\n'.join('    --hash=sha256:'+value for value in values)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:lines=list(pool.map(hashes,pins))
    target.write_text('# Published PyPI hashes; regenerate with packaging/windows/refresh_lock.py.\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    signing=[line for pin,line in zip(pins,lines) if pin[0] in {'cryptography','certifi','cffi','pycparser'}]
    target.with_name('requirements-signing-lock.txt').write_text('# Signing-job subset of requirements-lock.txt.\n'+'\n'.join(signing)+'\n',encoding='utf-8')
    print(json.dumps({'packages':len(pins),'hashes':sum(x.count('--hash=') for x in lines)}))


if __name__=='__main__':main()
