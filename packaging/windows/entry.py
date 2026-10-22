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
        from pathlib import Path
        from desktop_bridge.byo import template_directory
        # Resolve the actual shared resource layout, including the deploy template.
        result = {'version': cfg['version'], 'pack_id': cfg['pack_id'],
                  'resources': (Path(sys._MEIPASS) / 'desktop_bridge/web/index.html').is_file(),
                  'ca_bundle': Path(certifi.where()).is_file()}
        if not result['resources'] or not result['ca_bundle']:
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
    selected, _ = selector.parse_known_args(argv)
    profile(cfg, selected.data_dir)
    if not selected.data_dir:
        argv += ['--data-dir', str(profile(cfg))]
    sys.argv = [sys.argv[0], *argv]
    from desktop_bridge import management
    from desktop_bridge.windows_management import WindowsManagementServer
    management.ManagementServer = WindowsManagementServer
    from desktop_bridge.__main__ import main as bridge
    return bridge()


if __name__ == '__main__':
    raise SystemExit(main())
