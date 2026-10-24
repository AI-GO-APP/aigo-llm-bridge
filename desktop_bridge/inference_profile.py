"""Version-pinned native Chat profile; no caller content or credentials on disk."""
from collections import OrderedDict
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
import threading

from .errors import BridgeError
from .execution_budget import check

STANDARD = 'standard'
MINIMAL = 'codex-chat-minimal-v1'
CLI_VERSION = '0.163.0-alpha.11'
CLI_SIZE = 250473760
CLI_SHA256 = '8a6dc3938a2f5d30cc19c50b9ccad83a5aa2ca4a2e3411665430bb78a917220a'
CATALOG = Path(__file__).parent / 'data' / 'codex-chat-minimal-0163a11.json'
CATALOG_SHA256 = '32682dd2713a20fc44149b00a40df78153d67760c6a73c0c4eb14eb9995bfe26'
CATALOG_SIZE = 3654
CONTEXT_FLAGS = ('include_permissions_instructions', 'include_apps_instructions',
    'include_collaboration_mode_instructions', 'include_environment_context',
    'include_environment_context_time')
PROFILE_REASONS = {'verified', 'request_standard', 'model_unverified',
    'platform_unverified', 'cli_unverified', 'catalog_unavailable', 'provider_standard', 'pool_standard'}
_hash_lock = threading.Lock()
_hashes = OrderedDict()


@dataclass(frozen=True)
class Profile:
    name: str = STANDARD
    reason: str = 'request_standard'


def _alive(cancel):
    check()
    if cancel is not None and cancel.is_set():
        raise BridgeError(499, 'cancelled', '請求已取消。')


def digest(path, cancel=None):
    """Share bounded hashing across requests; invalidate on file identity/change."""
    path = Path(path)
    def identity():
        st = path.stat()
        return (str(path), st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    while not _hash_lock.acquire(timeout=.05):
        _alive(cancel)
    try:
        _alive(cancel)
        key = identity()
        if key not in _hashes:
            h = hashlib.sha256()
            with path.open('rb') as source:
                while chunk := source.read(2_000_000):
                    _alive(cancel)
                    h.update(chunk)
            if key != identity():
                raise OSError('Profile file changed during verification.')
            _hashes[key] = h.hexdigest()
            while len(_hashes) > 16:
                _hashes.popitem(last=False)
        return _hashes[key]
    finally:
        _hash_lock.release()


def availability(settings, cancel=None):
    if sys.platform != 'darwin':
        return 'platform_unverified'
    from .providers import executable
    try:
        native = Path(executable('codex', settings))
        if native.stat().st_size != CLI_SIZE or digest(native, cancel) != CLI_SHA256:
            return 'cli_unverified'
    except OSError:
        return 'cli_unverified'
    except BridgeError as error:
        if error.category != 'cli_missing':
            raise
        return 'cli_unverified'
    try:
        if CATALOG.is_symlink() or CATALOG.stat().st_size != CATALOG_SIZE or digest(CATALOG, cancel) != CATALOG_SHA256:
            return 'catalog_unavailable'
    except OSError:
        return 'catalog_unavailable'
    return 'verified'


def select(spec, settings, cancel=None):
    if spec.model['provider'] != 'codex':
        return Profile(reason='provider_standard')
    if (spec.generated_schema or spec.schema is not None or spec.tool_proposals
            or spec.format != 'text' or any(p['type'] != 'text'
                for m in spec.messages for p in m['parts'])):
        return Profile()
    if spec.model['native'] != 'gpt-6.1-sol':
        return Profile(reason='model_unverified')
    reason = availability(settings, cancel)
    return Profile(MINIMAL if reason == 'verified' else STANDARD, reason)


def resident_profiles(settings, cancel=None):
    return (MINIMAL, STANDARD) if availability(settings,cancel) == 'verified' else (STANDARD,)


def flags():
    return {'model_catalog_json': str(CATALOG.resolve()),
        'tools.experimental_request_user_input.enabled': False,
        **{name: False for name in CONTEXT_FLAGS}}


def verify_config(response):
    """Check native effective settings in RAM; never retain arbitrary config."""
    config = response.get('config') if isinstance(response, dict) else None
    if not isinstance(config, dict):
        return False
    if config.get('model_catalog_json') != str(CATALOG.resolve()):
        return False
    if any(config.get(name) is not False for name in CONTEXT_FLAGS):
        return False
    features = config.get('features')
    if not isinstance(features, dict):
        return False
    for name in ('shell_tool', 'apps', 'plugins', 'multi_agent', 'browser_use',
                 'computer_use', 'image_generation', 'view_image', 'goals'):
        value = features.get(name)
        if isinstance(value, dict):
            value = value.get('enabled')
        if value is not False:
            return False
    code_mode = features.get('code_mode')
    if not isinstance(code_mode, dict) or code_mode.get('enabled') is not False:
        return False
    servers = config.get('mcp_servers') or {}
    if not isinstance(servers, dict) or any(not isinstance(v, dict)
            or v.get('enabled') is not False for v in servers.values()):
        return False
    # Public Config omits this tool's value; its winning raw origin is exposed.
    origins = response.get('origins')
    origin = origins.get('tools.experimental_request_user_input.enabled', {}) if isinstance(origins, dict) else {}
    name = origin.get('name') if isinstance(origin, dict) else None
    return isinstance(name, dict) and name.get('type') == 'sessionFlags'


def unavailable():
    return BridgeError(503, 'codex_profile_unavailable',
        'CLI 純推論設定無法確認；尚未開始推論，請檢查 CLI／管理員設定。')
