"""Optional Windows bundle extension. Source and Mac management stay unchanged."""
import json
from pathlib import Path
import threading
import subprocess

from .management import ManagementServer
from .secret import protect
from .windows_release import config, atomic_json
from . import windows_updates


class WindowsManagementServer(ManagementServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.release = config()
        self.update_state = {'status': 'not_checked'}
        self.update_lock = threading.Lock()
        self.before_update = None

    def start(self):
        super().start()
        path = self.store.directory / 'windows-control.dpapi'
        temp = path.with_suffix('.tmp')
        temp.write_bytes(protect(json.dumps({'origin': self.origin, 'token': self.token, 'pack_id': self.release['pack_id']}).encode()))
        temp.replace(path)
        windows_updates.finish(self.release, self.store)
        self.check_updates()

    def stop(self):
        (self.store.directory / 'windows-control.dpapi').unlink(missing_ok=True)
        super().stop()

    def check_updates(self):
        if not self.update_lock.acquire(blocking=False):
            return
        def run():
            try:
                result = windows_updates.check(self.release, self.store.directory)
                self.update_state = {k: result[k] for k in ('installed', 'latest', 'available', 'required')}
                self.update_state['status'] = 'ready'
                if result['required']:
                    floor = self.store.directory / 'updates' / 'minimum-block.json'
                    if not floor.is_file():
                        atomic_json(floor, {'pack_id':self.release['pack_id'], 'previous_accepting':self.store.get('accepting')})
                    self.store.set('accepting', False)
            except Exception:
                self.update_state = {'status': 'unavailable', 'installed': self.release['version']}
            finally:
                self.update_lock.release()
        threading.Thread(target=run, daemon=True, name='windows-update-check').start()

    def state(self):
        value = super().state()
        value['windows_release'] = {k: self.release[k] for k in ('version', 'core_version', 'commit', 'channel', 'local_probe')}
        value['windows_update'] = self.update_state
        return value

    def action(self, path, data):
        if path == '/manage/windows-update/setup':
            from .windows_release import stable_entry
            subprocess.Popen([str(stable_entry('aigo-bridge.exe')), 'setup', '--data-dir', str(self.store.directory)],
                creationflags=subprocess.CREATE_NEW_CONSOLE)
            return {'ok': True}
        if path == '/manage/windows-update/apply':
            if not self.update_lock.acquire(blocking=False):
                return {'ok': False, 'status': 'busy'}
            from .windows_release import stable_entry
            self.update_state = {'status':'applying', 'installed':self.release['version']}
            def run():
                try:
                    result = subprocess.run([str(stable_entry('aigo-bridge.exe')), 'update', 'apply',
                        '--data-dir', str(self.store.directory)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if result.returncode:
                        self.update_state = {'status':'failed', 'installed':self.release['version']}
                finally:
                    self.update_lock.release()
            threading.Thread(target=run, daemon=True, name='windows-update-apply').start()
            return {'ok':True, 'status':'applying'}
        if path == '/manage/windows-update/check':
            self.check_updates()
            return {'ok': True, 'update': self.update_state}
        if path == '/manage/windows-update/drain':
            if self.before_update is None:
                self.before_update = self.store.get('accepting')
            self.store.set('accepting', False)
            with self.store.lock:
                count = self.store.db.execute("select count(*) from requests where status in ('queued','running')").fetchone()[0]
            return {'active_requests': count, 'previous_accepting': self.before_update}
        if path == '/manage/windows-update/resume':
            if self.before_update is not None:
                self.store.set('accepting', self.before_update)
                self.before_update = None
            return {'ok': True}
        if path == '/manage/windows-update/shutdown':
            if self.before_update is None:
                raise ValueError()
            self.on_shutdown()
            return {'ok': True}
        return super().action(path, data)
