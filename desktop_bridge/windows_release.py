"""Windows-only bundle identity. Never selects a provider account or a Mac profile."""
import json
import os
from pathlib import Path
import sys


def config():
    path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'windows-release.json'
    if not path.is_file():
        raise ValueError('Windows release configuration is missing.')
    return json.loads(path.read_text(encoding='utf-8'))


def profile(cfg, explicit=None):
    if explicit:
        return Path(explicit).resolve()
    if getattr(sys, 'frozen', False):
        binding = Path(sys.executable).resolve().parent.parent / 'windows-profile.json'
        if binding.is_file():
            value = json.loads(binding.read_text(encoding='utf-8'))
            if value['pack_id'] != cfg['pack_id']:
                raise ValueError('Profile binding belongs to another installer.')
            return Path(value['data_dir']).resolve()
    if cfg['local_probe']:
        if cfg.get('probe_data_dir'):
            return Path(cfg['probe_data_dir']).resolve()
        return Path(os.environ['LOCALAPPDATA']) / 'AIGO LLM Bridge Probes' / cfg['pack_id'] / 'data'
    from .paths import default_directory
    return default_directory().resolve()


def stable_entry(name='AIGO-LLM-Bridge.exe'):
    current = Path(sys.executable).resolve().parent
    root = current.parent
    if current.name.lower() == 'current' and (root / 'Update.exe').is_file():
        stub = root / name
        if stub.is_file():
            return stub
    return current / name


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True), encoding='utf-8')
    os.replace(temporary, path)
