# Mac 0.9.12 staged preflight metadata

2026-10-24。僅固定 allowlist metadata；不含原始 request／response／事件／Key。[驗收與限制](../qa/2026-10-24-macos-0912-staged-api.md)。

```json
{
  "schema": 1,
  "version": "0.9.12-mac.1",
  "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
  "transport": "original loopback HTTP service",
  "resident": 8,
  "workers": 64,
  "pending": 64,
  "raw_content_saved": false,
  "automatic_inference_retries": 0,
  "cold_warm_comparison": false,
  "full_issue39_gate": false,
  "started_at_unix": 1792839045.1899168,
  "stages": [],
  "before_health": {
    "ok": true,
    "version": "0.9.12-mac.1",
    "accepting": true,
    "max_concurrent_requests": 64,
    "max_execution_workers": 64,
    "queued_requests": 0,
    "running_requests": 0,
    "shared_provider_capacity": true,
    "warm_pool": {
      "starting": 0,
      "idle": 8,
      "active": 0,
      "closing": 0,
      "quarantined": 0,
      "unavailable": false,
      "resident_target": 8,
      "total": 8,
      "limit": 64,
      "peak": 18,
      "created": 481,
      "warm_hits": 48,
      "cold_starts": 48,
      "refill_failures": 0,
      "paused": false,
      "waiting_leases": 0,
      "idle_profiles": {
        "codex-chat-minimal-v1": 4,
        "standard": 4
      }
    },
    "warm_supported_providers": [
      "codex"
    ]
  },
  "success": false,
  "failure_class": "ValueError",
  "resources": {
    "peak_tree_rss_kib": 670208,
    "peak_tree_cpu_percent_one_core": 0.8,
    "peak_descendants": 8,
    "peak_tree_fds": 880,
    "health_failures": 0,
    "sampling_errors": 0,
    "samples": 1,
    "peak_pool_total": 8,
    "peak_running": 0,
    "peak_queued": 0,
    "resource_guard_exceeded": false,
    "control_health_p95_seconds": 0.0007,
    "control_health_max_seconds": 0.0007,
    "cpu_kind": "ps lifetime-average sampled maximum; 100% = one logical core",
    "fd_kind": "sampled proc_pidinfo descriptor bytes / 8; short-lived children may be missed",
    "process_scope": "original service and all descendants; sampler is outside service tree",
    "argv_collected": false
  },
  "temporary_keys_revoked": true,
  "settings_preserved": true,
  "original_key_rows_preserved": true,
  "manifest_preserved": true,
  "finished_at_unix": 1792839045.621742,
  "rows": [

  ]
}
```
