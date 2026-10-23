"""Validated default API capacity; larger inference concurrency is deferred."""

STANDARD_CONCURRENCY = 64
CONTROL_CONCURRENCY = 8
DEFAULT_KEY_RPM = 600


def is_inference_request(method, path):
    return method == "POST" and path in {
        "/api/v1/chat/completions", "/v1/chat/completions", "/api/alpha/decisions",
        "/bridge/v1/jobs", "/bridge/v1/models/probe",
    }
