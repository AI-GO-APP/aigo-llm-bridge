"""Bundle selected guides; link other tracked resources to the exact source commit."""
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote, unquote, urlsplit

DOCUMENTS = ('AGENTS.md', 'CLAUDE.md', 'skills/byo-cloudflare/SKILL.md', *(
    'docs/' + name for name in (
        'README.md', 'REQUIREMENTS.md', 'ARCHITECTURE.md', 'SCHEMA.md', 'API.md',
        'DESIGN-SYSTEM.md', 'DECISIONS.md', 'ACCEPTANCE.md',
        'ONBOARDING.md', 'CI-CD.md', 'RELEASE.md',
        'BYO-QUICKSTART.md', 'DEVICE-IDENTITY.md', 'AI-AGENT-SETUP.md', 'P1-Windows-guide.md',
        'OPENROUTER-PRICING.md', 'THIRD-PARTY-INTEGRATION.md', 'AI-EA-CLOUD-BEST-PRACTICE.md',
        'CROSS-PLATFORM-INSTALL.md', 'WINDOWS-INSTALL-UPDATE.md',
        'qa/2026-10-22-windows-velopack-acceptance.md')))


def stage_documents(root, stage, commit):
    root, stage = Path(root).resolve(), Path(stage)
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0'))
    selected = set(DOCUMENTS)
    for name in DOCUMENTS:
        if name not in tracked:
            raise ValueError('Bundled documentation must be tracked: ' + name)
        document = root / name
        def link(match):
            target = match[1]
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                return match[0]
            resolved = (document.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(root) or not resolved.exists():
                raise ValueError('Missing or external local documentation target: ' + target)
            relative = resolved.relative_to(root).as_posix()
            if relative in selected:
                return match[0]
            if relative not in tracked and not any(p.startswith(relative + '/') for p in tracked):
                raise ValueError('Documentation points at an untracked resource: ' + target)
            url = 'https://github.com/AI-GO-APP/aigo-llm-bridge/blob/' + commit + '/' + quote(relative)
            if parsed.fragment:
                url += '#' + parsed.fragment
            return '](' + url + ')'
        # Code examples are literal instructions, not document hyperlinks.
        parts = re.split(r'(```.*?```|~~~.*?~~~)', document.read_text(encoding='utf-8'), flags=re.S)
        for index in range(0, len(parts), 2):
            parts[index] = re.sub(r'\]\(([^)\s]+)\)', link, parts[index])
        destination = stage / 'documents' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(''.join(parts), encoding='utf-8')
    (stage / 'documents.json').write_text(json.dumps(DOCUMENTS), encoding='utf-8')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Stage installer guides with commit-pinned external links.')
    parser.add_argument('--stage', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    stage_documents(root, args.stage, commit)
