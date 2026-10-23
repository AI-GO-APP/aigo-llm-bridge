"""Validated default API capacity; larger inference concurrency is deferred."""

STANDARD_CONCURRENCY = 64
CONTROL_CONCURRENCY = 8
DEFAULT_KEY_RPM = 600
# 64 CLI pipe sets plus API/Relay sockets exceed macOS launchd's 256 soft descriptor limit.
FILE_LIMIT = 4096


def ensure_file_limit(target=FILE_LIMIT):
    """Raise the POSIX soft descriptor limit for this process; returns the effective soft limit."""
    try: import resource
    except ImportError: return None
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    want = target if hard == resource.RLIM_INFINITY else min(target, hard)
    if soft != resource.RLIM_INFINITY and soft < want:
        try: resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))
        except (ValueError, OSError): pass
    return resource.getrlimit(resource.RLIMIT_NOFILE)[0]


def is_inference_request(method, path):
    return method == "POST" and path in {
        "/api/v1/chat/completions", "/v1/chat/completions", "/api/alpha/decisions",
        "/bridge/v1/jobs", "/bridge/v1/models/probe",
    }
