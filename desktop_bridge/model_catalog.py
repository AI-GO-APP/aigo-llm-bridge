"""Caller-scoped metadata discovery. A picker catalog is not an entitlement proof."""
from __future__ import annotations

import copy
import re
import threading
import time

from . import providers

TTL = 30
REFRESH_MIN_INTERVAL = 5
EVIDENCE_TTL = 60
NATIVE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


class ModelCatalog:
    def __init__(self, store, *, discover=None, generation=None, clock=time.time):
        self.store = store
        self.discover = discover or providers.model_snapshot
        self.generation = generation or providers.auth_generation
        self.clock = clock
        self.lock = threading.RLock()
        self.snapshots = {}
        self.evidence = {}

    def _snapshot(self, provider, refresh):
        generation = self.generation(provider, self.store)
        now = self.clock()
        with self.lock:
            cached = self.snapshots.get(provider)
            if cached and cached[0] == generation and 0 <= now-cached[1] < (REFRESH_MIN_INTERVAL if refresh else TTL):
                return cached
            try:
                snapshot = self.discover(provider, self.store)
            except Exception:
                snapshot = {"ready": None, "models": None, "source": "discovery_unavailable"}
            current_generation = self.generation(provider, self.store)
            if generation != current_generation:
                snapshot = {"ready": None, "models": None, "source": "account_changed"}
                generation = current_generation
            result = (generation, now, snapshot)
            self.snapshots[provider] = result
            return result

    def observe(self, model, protocol, generation, error=None):
        if generation != self.generation(model["provider"], self.store):
            return
        if error and error.category not in {"model_not_found", "provider_authentication"}:
            return
        with self.lock:
            self.evidence[(model["provider"], model["native"], protocol)] = (
                generation, self.clock(), error.category if error else None)

    def capabilities(self, caller, *, refresh=False):
        registered = self.store.get("models")
        result = []
        for provider in sorted(set(caller["providers"]) & {"claude", "codex"}):
            generation, checked, snapshot = self._snapshot(provider, refresh)
            models = {m["id"]: dict(m) for m in registered if m["provider"] == provider}
            native_ids = snapshot.get("models")
            if provider == "codex" and native_ids is not None:
                for native in native_ids:
                    if isinstance(native, str) and NATIVE_ID.fullmatch(native):
                        model_id = "openai/" + native
                        if not any(m["id"] == model_id for m in registered):
                            models[model_id] = {"id": model_id, "provider": provider, "native": native}
            for model in models.values():
                state, reason = "unverified", snapshot.get("source", "registration")
                observed_at, expires_at = checked, checked + TTL
                if snapshot.get("ready") is False:
                    state, reason = "unavailable", "provider_authentication"
                # A bundled picker catalog's absence is not a model permission denial.
                with self.lock:
                    proofs = [(p, self.evidence.get((provider, model["native"], p))) for p in ("chat", "decisions")]
                current = [(p, v) for p, v in proofs if v and v[0] == generation and 0 <= self.clock()-v[1] < EVIDENCE_TTL]
                if current and snapshot.get("ready") is not False:
                    _, latest = max(current, key=lambda item: item[1][1])
                    observed_at, expires_at = latest[1], latest[1]+EVIDENCE_TTL
                    state, reason = ("unavailable", latest[2]) if latest[2] else ("verified", "inference_succeeded")
                decisions_verified = any(p == "decisions" and not v[2] for p, v in current) and state == "verified"
                result.append({**model, "availability": {"state": state, "reason": reason,
                    "checked_at": observed_at, "expires_at": expires_at},
                    "catalog_listed": None if native_ids is None else model["native"] in native_ids,
                    "decisions": {"mode": "emulated", "verified": decisions_verified,
                                  "question_types": ["noul", "choice", "score"]}})
        return {"object": "list", "data": copy.deepcopy(result), "inference_performed": False}

    def models(self, caller):
        return {"object": "list", "data": [
            {"id": m["id"], "name": m["id"], "object": "model", "owned_by": m["provider"],
             "supported_parameters": ["response_format", "reasoning", "reasoning_effort", "tools", "tool_choice", "parallel_tool_calls"]}
            for m in self.capabilities(caller)["data"] if m["availability"]["state"] != "unavailable"]}

    def routing_models(self, caller):
        return [{k: m[k] for k in ("id", "provider", "native")} for m in self.capabilities(caller)["data"]
                if m["availability"]["state"] != "unavailable"]
