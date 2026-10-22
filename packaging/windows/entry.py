"""Velopack integration is confined to new Windows bundles."""
import sys


def main():
    import velopack
    velopack.App().set_auto_apply_on_startup(False).run()
    from desktop_bridge.windows_release import config, profile
    cfg = config()
    from pathlib import Path
    from desktop_bridge import byo
    byo.template_directory = lambda: Path(sys._MEIPASS) / 'cloudflare'
    if sys.argv[1:] == ['--self-test']:
        import json
        import certifi
        import jsonschema
        import re
        from pathlib import Path
        from desktop_bridge.byo import template_directory
        # Resolve the actual shared resource layout, including the deploy template.
        result = {'version': cfg['version'], 'pack_id': cfg['pack_id'],
                  'resources': (Path(sys._MEIPASS) / 'desktop_bridge/web/index.html').is_file(),
                  'ca_bundle': Path(certifi.where()).is_file()}
        root = Path(sys._MEIPASS)
        documents = list((root/'docs').rglob('*.md')) + [root/'AGENTS.md', root/'CLAUDE.md', root/'skills/byo-cloudflare/SKILL.md']
        missing = []
        for document in documents:
            text = re.sub(r'```.*?```', '', document.read_text(encoding='utf-8'), flags=re.S)
            for target in re.findall(r'\]\(([^)\s]+)\)', text):
                if not re.match(r'^[a-z]+:|#', target) and not (document.parent/target.split('#')[0]).exists():
                    missing.append(target)
        result['document_links'] = not missing
        result['deployment_template'] = (template_directory()/'src/worker.js').is_file()
        if not all(result[k] for k in ('resources','ca_bundle','document_links','deployment_template')):
            return 2
        print(json.dumps(result))
        return 0
    if Path(sys.executable).name.lower() == 'aigo-bridge.exe':
        from desktop_bridge.windows_cli import main as cli
        return cli()
    argv = sys.argv[1:]
    if cfg['local_probe'] and not argv:
        argv = ['--background']
    import argparse
    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument('--data-dir')
    selector.add_argument('--console',action='store_true')
    selector.add_argument('--browser',action='store_true')
    selector.add_argument('--console-probe',action='store_true')
    selector.add_argument('--console-hidden',action='store_true')
    selected, _ = selector.parse_known_args(argv)
    directory=profile(cfg, selected.data_dir)
    from desktop_bridge import windows_console
    if selected.console or selected.console_probe:
        return windows_console.run(directory,browser=selected.browser,probe=selected.console_probe,hidden=selected.console_hidden)
    if '--background' not in argv and '--headless' not in argv and '--native-ui' not in argv:
        value=windows_console.ensure_service(directory)
        windows_console.request_owner(value,'/manage/windows-console/open',{'browser':selected.browser})
        return 0
    if not selected.data_dir:
        argv += ['--data-dir', str(profile(cfg))]
    sys.argv = [sys.argv[0], *argv]
    from desktop_bridge import management
    import webbrowser
    webbrowser.open=lambda _url,*_args,**_kwargs: windows_console.launch(directory)
    from desktop_bridge.windows_management import WindowsManagementServer
    management.ManagementServer = WindowsManagementServer
    from desktop_bridge.__main__ import main as bridge
    return bridge()


if __name__ == '__main__':
    raise SystemExit(main())
