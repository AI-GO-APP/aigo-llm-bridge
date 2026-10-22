"""Create a scoped service key and deliver once through a native Mac dialog, never stdout/files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import ssl
import urllib.request
import urllib.error


def deliver(root, label, rpm):
    if sys.platform != 'darwin': raise ValueError('macOS required.')
    m=json.loads((Path(root).expanduser()/'source-install.json').read_text(encoding='utf-8'))
    sys.path.insert(0,m['app'])
    from desktop_bridge.store import Store
    from desktop_bridge.handoff import integration
    store=Store(m['data_dir'],startup=False)
    try:
        # Validate handoff before key creation. Only the OS dialog receives the cleartext.
        integration(store,None,['codex'])
        kid,key=store.create_key(label,['codex'],rpm)
        info=integration(store,None,['codex'],key)
        prefix=next(k['prefix'] for k in store.keys() if k['id']==kid)
        value={'key_id':kid,'prefix':prefix,'providers':['codex'],'base_url':info['config']['base_url']}
        print(json.dumps({**value,'delivery':'native one-time dialog; key remains valid if dialog is closed'}),flush=True)
        # Verify the retained owner key through the public endpoint before delivery.
        import certifi
        public=store.get('public_url')
        def call(endpoint,body=None):
            req=urllib.request.Request(public+endpoint,data=json.dumps(body).encode() if body else None,
                headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'aigo-mac-owner-handoff/1.0'})
            with urllib.request.urlopen(req,context=ssl.create_default_context(cafile=certifi.where()),timeout=100) as response:
                return json.load(response)
        ready=False
        for _ in range(35):
            try:call('/api/v1/models');ready=True;break
            except urllib.error.HTTPError as e:
                if e.code not in (401,503):break
            except OSError:pass
            time.sleep(2)
        if ready:
            small=next((m['id'] for m in store.get('models') if m['id']=='openai/gpt-6-luna'),info['config']['model'])
            try:
                result=call('/api/v1/chat/completions',{'model':small,'messages':[{'role':'user','content':'Reply exactly OWNER_SERVICE_READY. Do not use tools.'}],'stream':False,'reasoning_effort':'low'})
                print(json.dumps({'key_id':kid,'public_inference_verified':'OWNER_SERVICE_READY' in result['choices'][0]['message']['content'],
                                  'model':result['model'],'usage':result['usage']}),flush=True)
            except Exception:print(json.dumps({'key_id':kid,'public_inference_verified':False}),flush=True)
        else:print(json.dumps({'key_id':kid,'public_inference_verified':False}),flush=True)
        # AppleScript source goes over stdin, so the key never appears in ps argv or a script file.
        def literal(value): return '"'+value.replace('\\','\\\\').replace('"','\\"').replace('\n','" & return & "')+'"'
        text=('Mac Bridge 專用長效 KEY（僅此視窗顯示一次）\n\n'+info['config']['base_url']+
              '\nKey ID: '+kid+'\n\n'+key+'\n\n請複製到可信的服務端 secret。KEY 保留有效；不要貼回聊天或一般報告。')
        script=('activate\nset serviceKey to '+literal(key)+'\n'+
                'set handoffText to '+literal(text)+'\n'+
                'set resultDialog to display dialog handoffText with title "AIGO Mac Bridge — Secret handoff" buttons {"關閉", "複製 KEY", "複製串接訊息"} default button "複製 KEY"\n'+
                'if button returned of resultDialog is "複製 KEY" then\nset the clipboard to serviceKey\n'+
                'else if button returned of resultDialog is "複製串接訊息" then\nset the clipboard to '+literal(info['prompt'])+'\nend if\n')
        result=subprocess.run(['/usr/bin/osascript','-'],input=script.encode(),capture_output=True)
        print(json.dumps({'key_id':kid,'dialog_completed':result.returncode==0,
                          'key_retained':True,'notice':'Clipboard may contain the selected secret; save it only in a trusted secret store.'}),flush=True)
        if result.returncode: return 2
        return 0
    finally:store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-root',default=str(Path.home()/'Library/Application Support/AIGO LLM Bridge'))
    parser.add_argument('--label',default='AI EA Cloud mac-primary')
    parser.add_argument('--rpm',type=int,default=60)
    args=parser.parse_args()
    try:return deliver(args.install_root,args.label,args.rpm)
    except (OSError,ValueError,subprocess.SubprocessError):
        print('Secret handoff incomplete. Inspect key-list in this profile before creating another key; no key was printed or automatically revoked.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
