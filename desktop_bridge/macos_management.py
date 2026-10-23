"""Mac-only setup and native console; Windows release feeds remain Windows-only."""
import json
from pathlib import Path
import subprocess
import sys

from . import __version__
from .management import ManagementServer
from .macos_onboarding import Onboarding, source_install
from .macos_power import PowerPolicy


class MacManagementServer(ManagementServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installation = source_install(self.store.directory)
        self.release = {'version': __version__, 'pack_id': 'macos-source'}
        self.power_policy = PowerPolicy(self.store.directory)
        self.onboarding = Onboarding(self, self.power_policy)
        self.console = None

    def asset(self, path):
        web = Path(__file__).parent / 'web'
        if path == '/macos.js':
            return (web / 'macos.js').read_bytes(), 'text/javascript; charset=utf-8'
        if path == '/macos-onboarding.js':
            return (web / 'macos-onboarding.js').read_bytes(), 'text/javascript; charset=utf-8'
        if path == '/macos.css':
            return (web / 'macos.css').read_bytes(), 'text/css; charset=utf-8'
        value = super().asset(path)
        if path == '/' and value:
            html = value[0].decode().replace('</head>', '<link rel="stylesheet" href="/macos.css"><script src="/macos.js" defer></script><script src="/macos-onboarding.js" defer></script></head>')
            html = html.replace('登入 Windows 後在背景自動啟動', '登入 macOS 後在背景自動啟動')
            return html.encode(), value[1]
        return value

    def state(self):
        value = super().state()
        value['macos_release'] = {'version': __version__, 'source_commit': (self.installation or {}).get('source_commit'),
                                  'distribution': 'source', 'source_checkout': (self.installation or {}).get('source_checkout')}
        value['macos_onboarding'] = self.onboarding.state()
        try:
            value['macos_update'] = json.loads((Path(self.installation['install_root']) / 'macos-update.json').read_text()) if self.installation else None
        except (OSError, ValueError):
            value['macos_update'] = None
        return value

    def open_console(self, browser=False):
        if browser:
            import webbrowser
            return webbrowser.open(self.url)
        if self.console and self.console.poll() is None:
            from .windows import Instance
            instance = Instance(self.store.directory / 'console')
            instance.notify()
            instance.close()
            return True
        self.console = subprocess.Popen([sys.executable, '-m', 'desktop_bridge.macos_console'],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=Path(__file__).resolve().parent.parent, start_new_session=True)
        # Session credential is private stdin only, never a process argument or control file.
        self.console.stdin.write(json.dumps({'origin': self.origin, 'token': self.token,
                                            'directory': str(self.store.directory)}).encode())
        self.console.stdin.close()
        return True

    def action(self, path, data):
        if path.startswith('/manage/macos-onboarding/'):
            return self.onboarding.action(path.rsplit('/', 1)[-1], data)
        if path == '/manage/macos-console/browser':
            return {'opened': self.open_console(browser=True)}
        if path == '/manage/macos-update/apply':
            source = (self.installation or {}).get('source_checkout')
            if not source or not (Path(source) / 'tools/install.py').is_file():
                raise ValueError('Use the source installation guide to select a checkout.')
            # The source path was recorded by the installer, never accepted from browser input.
            subprocess.Popen([sys.executable, str(Path(__file__).resolve().parent.parent / 'tools/mac_service.py'),
                'update', '--install-root', self.installation['install_root'], '--source', source],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return {'ok': True, 'status': 'draining'}
        return super().action(path, data)

    def stop(self):
        # Viewer notices the management session disappearing and closes itself.
        super().stop()
