"""Disposable Actions runner only: real standard-user and TS-session ownership.

Creates one temporary local account and a SYSTEM test broker, then removes both.
Passwords stay in the parent process. A duplicated token handle, never a password,
is passed to the broker. No interactive desktop, RDP login or provider is used.
"""
import argparse
import contextlib
import ctypes as c
from ctypes import wintypes as w
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    os.replace(temporary, path)


def wait_file(path, seconds=45):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        for name in ('worker-failure.json', 'broker-failure.json'):
            failure = path.parent / name
            if failure.is_file(): raise RuntimeError('Isolated test process failed: '+failure.read_text())
        if path.is_file(): return json.loads(path.read_text(encoding='utf-8'))
        time.sleep(.1)
    raise TimeoutError('Disposable Windows acceptance timed out.')


def api():
    kernel = c.WinDLL('kernel32', use_last_error=True)
    advapi = c.WinDLL('advapi32', use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.DuplicateHandle.argtypes = [w.HANDLE, w.HANDLE, w.HANDLE, c.POINTER(w.HANDLE), w.DWORD, w.BOOL, w.DWORD]
    advapi.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)]
    advapi.GetTokenInformation.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes = [c.c_void_p, c.POINTER(w.LPWSTR)]
    kernel.LocalFree.argtypes = [c.c_void_p]
    return kernel, advapi


def identity():
    kernel, advapi = api()
    token = w.HANDLE(); required = w.DWORD(); session = w.DWORD()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, c.byref(token)): raise c.WinError(c.get_last_error())
    try:
        advapi.GetTokenInformation(token, 1, None, 0, c.byref(required))
        buf = c.create_string_buffer(required.value)
        if not advapi.GetTokenInformation(token, 1, buf, required, c.byref(required)): raise c.WinError(c.get_last_error())
        sid = w.LPWSTR()
        if not advapi.ConvertSidToStringSidW(c.cast(buf, c.POINTER(c.c_void_p))[0], c.byref(sid)): raise c.WinError(c.get_last_error())
        try: value = sid.value
        finally: kernel.LocalFree(c.cast(sid, c.c_void_p))
        kernel.ProcessIdToSessionId(os.getpid(), c.byref(session))
        return value, session.value
    finally: kernel.CloseHandle(token)


def enable_tcb(kernel, advapi):
    class LUID(c.Structure): _fields_ = [('low', w.DWORD), ('high', w.LONG)]
    class PRIV(c.Structure): _fields_ = [('count', w.DWORD), ('luid', LUID), ('attributes', w.DWORD)]
    token = w.HANDLE(); priv = PRIV(); priv.count = 1; priv.attributes = 2
    advapi.LookupPrivilegeValueW.argtypes = [w.LPCWSTR, w.LPCWSTR, c.POINTER(LUID)]
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x28, c.byref(token)): raise c.WinError(c.get_last_error())
    try:
        if not advapi.LookupPrivilegeValueW(None, 'SeTcbPrivilege', c.byref(priv.luid)): raise c.WinError(c.get_last_error())
        advapi.AdjustTokenPrivileges.argtypes = [w.HANDLE, w.BOOL, c.POINTER(PRIV), w.DWORD, c.c_void_p, c.c_void_p]
        c.set_last_error(0)
        if not advapi.AdjustTokenPrivileges(token, False, c.byref(priv), 0, None, None): raise c.WinError(c.get_last_error())
        if c.get_last_error(): raise c.WinError(c.get_last_error())
    finally: kernel.CloseHandle(token)


def spawn(kernel, advapi, command):
    class STARTUP(c.Structure):
        _fields_ = [('cb', w.DWORD), ('reserved', w.LPWSTR), ('desktop', w.LPWSTR), ('title', w.LPWSTR),
            *[(name, w.DWORD) for name in ('x','y','xsize','ysize','xchars','ychars','fill','flags')],
            ('show', w.WORD), ('reserved_size', w.WORD), ('reserved_bytes', c.c_void_p),
            ('stdin', w.HANDLE), ('stdout', w.HANDLE), ('stderr', w.HANDLE)]
    class PROCESS(c.Structure):
        _fields_ = [('process', w.HANDLE), ('thread', w.HANDLE), ('pid', w.DWORD), ('tid', w.DWORD)]
    advapi.SetTokenInformation.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD]
    session = w.DWORD(command['session'])
    token = w.HANDLE(command['token'])
    try:
        if not advapi.SetTokenInformation(token, 12, c.byref(session), c.sizeof(session)): raise c.WinError(c.get_last_error())
        start = STARTUP(); start.cb = c.sizeof(start); start.desktop = ''
        process = PROCESS()
        leaf = Path(command['leaf'])
        # Do not inherit CI credentials, publisher tokens or another user's HOME.
        variables = {'SystemRoot': os.environ['SystemRoot'], 'WINDIR': os.environ['SystemRoot'],
            'TEMP': str(leaf), 'TMP': str(leaf), 'USERPROFILE': str(leaf / 'home'),
            'LOCALAPPDATA': str(leaf / 'home/AppData/Local'), 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8',
            'PATH': str(Path(os.environ['SystemRoot']) / 'System32')}
        environment = c.create_unicode_buffer('\0'.join(k+'='+v for k,v in sorted(variables.items()))+'\0\0')
        args = c.create_unicode_buffer(subprocess.list2cmdline(command['argv']))
        advapi.CreateProcessAsUserW.argtypes = [w.HANDLE, w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p,
            w.BOOL, w.DWORD, c.c_void_p, w.LPCWSTR, c.POINTER(STARTUP), c.POINTER(PROCESS)]
        if not advapi.CreateProcessAsUserW(token, None, args, None, None, False, 0x08000400,
                environment, command['cwd'], c.byref(start), c.byref(process)): raise c.WinError(c.get_last_error())
        kernel.CloseHandle(process.thread)
        return process.pid, process.process
    finally: kernel.CloseHandle(token)


def broker(root):
    assert identity()[0] == 'S-1-5-18' and (root / 'disposable-ci.json').is_file()
    kernel, advapi = api(); enable_tcb(kernel, advapi)
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    kernel.GetExitCodeProcess.argtypes = [w.HANDLE, c.POINTER(w.DWORD)]
    kernel.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
    kernel.WTSGetActiveConsoleSessionId.restype = w.DWORD
    write(root/'broker-ready.json', {'pid': os.getpid(), 'session': identity()[1],
        'console_session': kernel.WTSGetActiveConsoleSessionId()})
    children = {}
    try:
        for index in range(100):
            command = wait_file(root/f'command-{index}.json', 240)
            try:
                if command['operation'] == 'stop':
                    write(root/f'result-{index}.json', {'ok': True}); return
                if command['operation'] == 'spawn':
                    pid, handle = spawn(kernel, advapi, command)
                    children[pid] = handle; result = {'ok': True, 'pid': pid}
                else:
                    handle = children[command['pid']]
                    if kernel.WaitForSingleObject(handle, 30000) != 0: raise TimeoutError()
                    code = w.DWORD(); kernel.GetExitCodeProcess(handle, c.byref(code))
                    kernel.CloseHandle(handle); del children[command['pid']]
                    result = {'ok': True, 'exit': code.value}
            except Exception as error:
                result = {'ok': False, 'error_type': type(error).__name__, 'winerror': getattr(error, 'winerror', None)}
            write(root/f'result-{index}.json', result)
    finally:
        for handle in children.values():
            kernel.TerminateProcess(handle, 1); kernel.WaitForSingleObject(handle, 5000); kernel.CloseHandle(handle)


def worker(leaf):
    # The broker starts this copied script in a separate real user/TS session.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from desktop_bridge import windows_instance as guard, management, __main__ as app
    from desktop_bridge.windows_console import owner
    request = json.loads((leaf/'request.json').read_text())
    sid, session = identity()
    result = {'different_user': sid != request['parent_sid'], 'session': session,
        'standard_user': not bool(c.windll.shell32.IsUserAnAdmin())}
    try: owner(leaf/'protected-owner', {'pack_id': 'synthetic-ci'})
    except (OSError, ValueError): result['management_dpapi_denied'] = True
    else: result['management_dpapi_denied'] = False
    guard.MACHINE_ADDRESS = ('127.0.0.1', request['port'])
    management.ManagementServer.refresh_auth = lambda self: None
    original = management.ManagementServer.start
    def ready(manager):
        original(manager)
        write(leaf/'ready.json', {**result, 'api': manager.api.port})
        def stop():
            while not (leaf/'stop').exists(): time.sleep(.1)
            manager.on_shutdown()
        import threading
        threading.Thread(target=stop, daemon=True).start()
    management.ManagementServer.start = ready
    sys.argv = ['bridge', '--background', '--data-dir', str(leaf/'profile'), '--port', '0']
    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
        code = app.main()
    write(leaf/'finished.json', {**result, 'exit': code, 'profile_exists': (leaf/'profile').exists()})


def parent(root):
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_OS') != 'Windows':
        raise RuntimeError('This acceptance creates disposable OS accounts; Actions Windows runners only.')
    if not c.windll.shell32.IsUserAnAdmin(): raise RuntimeError('Disposable runner administrator required.')
    if root.exists(): raise ValueError('Use a new disposable acceptance directory.')
    root.mkdir(parents=True)
    kernel, advapi = api()
    task = 'LocalTokenBuffetTest-' + uuid.uuid4().hex[:12]
    username = 'ltb' + uuid.uuid4().hex[:12]
    account_created = False; task_created = False; broker_handle = None; token = w.HANDLE()
    checks = {}; report = {'checks': checks, 'scope': 'disposable runner only; no owner workstation, provider or Cloud access'}
    net = c.WinDLL('netapi32')
    net.NetUserDel.argtypes = [w.LPCWSTR, w.LPCWSTR]
    def run(*args): return subprocess.run(list(map(str,args)), check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    def quote(value): return "'"+str(value).replace("'", "''")+"'"
    try:
        run('icacls.exe', root, '/inheritance:r', '/grant:r', '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F')
        write(root/'disposable-ci.json', {'disposable': True})
        public = root/'public'; public.mkdir()
        # Copy only source/package libraries. Never grant access to checkout .git credentials.
        for name in subprocess.check_output(['git','ls-files','desktop_bridge'],cwd=ROOT,text=True).splitlines():
            if '/tests/' in name: continue
            target = public/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/name,target)
        shutil.copyfile(__file__, public/'verify_windows_machine.py')
        runtime = public/'runtime'; shutil.copytree(Path(sys.prefix)/'Lib/site-packages',runtime/'Lib/site-packages')
        (runtime/'Scripts').mkdir(); shutil.copyfile(sys.executable,runtime/'Scripts/python.exe')
        shutil.copyfile(Path(sys.prefix)/'pyvenv.cfg',runtime/'pyvenv.cfg')
        child_python = runtime/'Scripts/python.exe'
        class USER(c.Structure):
            _fields_ = [('name',w.LPWSTR),('password',w.LPWSTR),('age',w.DWORD),('priv',w.DWORD),
                ('home',w.LPWSTR),('comment',w.LPWSTR),('flags',w.DWORD),('script',w.LPWSTR)]
        user = USER(username, secrets.token_urlsafe(24)+'aA1!', 0, 1, None, None, 0x10201, None)
        net.NetUserAdd.argtypes = [w.LPCWSTR,w.DWORD,c.c_void_p,c.POINTER(w.DWORD)]
        error = w.DWORD(); status = net.NetUserAdd(None,1,c.byref(user),c.byref(error))
        if status: raise OSError(status, 'Disposable account creation failed.')
        account_created = True
        run('powershell.exe','-NoProfile','-Command',f'Add-LocalGroupMember -SID S-1-5-32-545 -Member {quote(username)} -ErrorAction Stop')
        advapi.LogonUserW.argtypes = [w.LPCWSTR,w.LPCWSTR,w.LPCWSTR,w.DWORD,w.DWORD,c.POINTER(w.HANDLE)]
        if not advapi.LogonUserW(username,'.',user.password,2,0,c.byref(token)): raise c.WinError(c.get_last_error())
        user.password = None
        run('icacls.exe', root, '/grant', username+':(RX)')
        run('icacls.exe', public, '/grant', username+':(OI)(CI)RX')
        action_args = subprocess.list2cmdline([str(Path(__file__).resolve()),'broker','--output',str(root)])
        ps = f"$ErrorActionPreference='Stop';$a=New-ScheduledTaskAction -Execute {quote(sys.executable)} -Argument {quote(action_args)} -WorkingDirectory {quote(ROOT)};$p=New-ScheduledTaskPrincipal -UserId SYSTEM -LogonType ServiceAccount -RunLevel Highest;Register-ScheduledTask -TaskName {quote(task)} -Action $a -Principal $p -Force|Out-Null;Start-ScheduledTask -TaskName {quote(task)}"
        task_created = True
        run('powershell.exe','-NoProfile','-Command',ps)
        ready = wait_file(root/'broker-ready.json')
        broker_handle = kernel.OpenProcess(0x40,False,ready['pid'])
        if not broker_handle: raise c.WinError(c.get_last_error())
        parent_sid, parent_session = identity()
        other_session = ready['session'] if ready['session'] != parent_session else ready['console_session']
        if other_session in (parent_session, 0xffffffff): raise RuntimeError('Runner has no distinct TS session for actual acceptance.')
        report.update(parent_session=parent_session,other_session=other_session)
        index = 0
        def rpc(command):
            nonlocal index
            write(root/f'command-{index}.json',command)
            result = wait_file(root/f'result-{index}.json'); index += 1
            if not result['ok']:
                report['broker_error'] = result
                raise RuntimeError('Broker operation failed.')
            return result
        def start(leaf):
            remote = w.HANDLE()
            if not kernel.DuplicateHandle(kernel.GetCurrentProcess(), token, broker_handle, c.byref(remote), 0, False, 2): raise c.WinError(c.get_last_error())
            return rpc({'operation':'spawn','token':remote.value,'session':other_session,'leaf':str(leaf),
                'argv':[str(child_python),str(public/'verify_windows_machine.py'),'worker','--output',str(leaf)],'cwd':str(public)})['pid']
        from desktop_bridge import windows_instance as guard, secret
        import socket
        with socket.socket() as available: available.bind(('127.0.0.1',0)); port = available.getsockname()[1]
        guard.MACHINE_ADDRESS = ('127.0.0.1',port)
        def leaf(name):
            path = root/name; path.mkdir()
            run('icacls.exe',path,'/grant',username+':(OI)(CI)M')
            protected = path/'protected-owner'; protected.mkdir()
            (protected/'windows-control.dpapi').write_bytes(secret.protect(json.dumps({'pack_id':'synthetic-ci','token':'synthetic management-only token','origin':'http://127.0.0.1:1'}).encode()))
            write(path/'request.json', {'port':port,'parent_sid':parent_sid})
            return path
        rejected = leaf('rejected'); first = guard.MachineInstance()
        try:
            assert first.primary
            pid = start(rejected); result = wait_file(rejected/'finished.json'); finished = rpc({'operation':'wait','pid':pid})
            checks['different_real_windows_user']=result['different_user']
            checks['different_real_ts_session']=result['session']==other_session and other_session!=parent_session
            checks['rejected_user_not_administrator']=result['standard_user']
            checks['cross_session_rejected_before_profile']=result['exit']==3 and not result['profile_exists'] and finished['exit']==0
            checks['management_dpapi_not_shared']=result['management_dpapi_denied']
        finally: first.close()
        accepted = leaf('accepted'); pid = start(accepted)
        try:
            result = wait_file(accepted/'ready.json')
            checks['standard_user_starts_after_release']=result['standard_user'] and result['different_user'] and result['session']==other_session
            second = guard.MachineInstance()
            try: checks['admin_other_session_also_rejected']=not second.primary
            finally: second.close()
            import urllib.request
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open('http://127.0.0.1:'+str(result['api'])+'/health',timeout=5) as response:
                checks['other_user_runtime_serves_http']=json.load(response)['ok']
        finally: (accepted/'stop').touch()
        finished=rpc({'operation':'wait','pid':pid}); checks['normal_other_user_shutdown']=finished['exit']==0
        successor=guard.MachineInstance()
        try: checks['cross_session_ownership_reusable']=successor.primary
        finally: successor.close()
        rpc({'operation':'stop'})
    finally:
        if token: kernel.CloseHandle(token)
        if broker_handle: kernel.CloseHandle(broker_handle)
        if task_created:
            subprocess.run(['schtasks.exe','/End','/TN',task],capture_output=True)
            checks['temporary_task_removed']=subprocess.run(['schtasks.exe','/Delete','/TN',task,'/F'],capture_output=True).returncode==0
        if account_created: checks['temporary_account_removed']=net.NetUserDel(None,username)==0
        report['success']=bool(checks) and all(checks.values()) and 'cross_session_ownership_reusable' in checks
        write(root/'acceptance.json',report)
        print(json.dumps(report),flush=True)
    assert report['success']


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['parent','broker','worker']);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try: {'parent':parent,'broker':broker,'worker':worker}[args.mode](Path(args.output).resolve())
    except Exception as error:
        # Never print account passwords, raw child output or token handles.
        failure={'failed':True,'error_type':type(error).__name__,'winerror':getattr(error,'winerror',None)}
        target=Path(args.output)
        if target.is_dir(): write(target/(args.mode+'-failure.json'),failure)
        print(json.dumps(failure),flush=True)
        raise SystemExit(1)
