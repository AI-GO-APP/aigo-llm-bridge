# Mac 0.9.11 CLI token release metadata

固定合成內容；只存 allowlist metadata，無 request／response／event 原文或憑證。UUID 對應同一 Key 的本機計量。估算與 provider usage 分開。

```json
{
  "schema": 1,
  "release": {
    "success": true,
    "tag": "macos-source-v0.9.11-mac.1",
    "source_commit": "f9b481047485a9be8c0351a3b44139064e021c86",
    "sha256": "683107fed3eb457c9a9cf69c8697a47ea8a609a2044de88cbdec88ca9b626c02",
    "assets": [
      "aigo-llm-bridge-macos-source-0.9.11-mac.1.zip",
      "aigo-llm-bridge-macos-source-0.9.11-mac.1.zip.sha256",
      "macos-source-manifest.json",
      "macos-source-self-test.json"
    ],
    "anonymous_download": true,
    "authorization_header_used": false,
    "runtime_and_opt_in_tools_match_reviewed_source": true,
    "package": "/Users/ying/Library/Application Support/AIGO LLM Bridge/sources/macos-source-v0.9.11-mac.1/aigo-llm-bridge-macos-source-0.9.11-mac.1.zip",
    "source": "/Users/ying/Library/Application Support/AIGO LLM Bridge/sources/macos-source-v0.9.11-mac.1/extracted/aigo-llm-bridge",
    "manifest_clean": true
  },
  "package_install": {
    "success": true,
    "public_zip": true,
    "original_version": "0.9.10-mac.1",
    "version": "0.9.11-mac.1",
    "source_commit": "f9b481047485a9be8c0351a3b44139064e021c86",
    "download_installed": true,
    "fixed_machine_lock": true,
    "rejected_profile_no_database": true,
    "shutdown_api_closed": true,
    "max_concurrent_requests": 64,
    "credentials_or_power_changed": false,
    "original_restart_command_ok": true,
    "original_restored_healthy": true
  },
  "runtime_acceptance": {
    "version": "0.9.11-mac.1",
    "source_commit": "f9b481047485a9be8c0351a3b44139064e021c86",
    "before_stop": {
      "ok": true,
      "version": "0.9.11-mac.1",
      "accepting": true,
      "max_concurrent_requests": 64,
      "max_execution_workers": 64,
      "queued_requests": 0,
      "running_requests": 0,
      "shared_provider_capacity": true,
      "warm_pool": {
        "starting": 0,
        "idle": 2,
        "active": 0,
        "closing": 0,
        "quarantined": 0,
        "unavailable": false,
        "resident_target": 2,
        "total": 2,
        "limit": 64,
        "peak": 3,
        "created": 9,
        "warm_hits": 7,
        "cold_starts": 4,
        "refill_failures": 0,
        "paused": false,
        "waiting_leases": 0
      },
      "warm_supported_providers": [
        "codex"
      ]
    },
    "observed_owned_processes": 3,
    "observed_empty_cwds": 2,
    "stop_seconds": 0.6976,
    "owned_processes_remaining": 0,
    "old_cwds_remaining": 0,
    "restart_ok": true,
    "final_health": {
      "ok": true,
      "version": "0.9.11-mac.1",
      "accepting": true,
      "max_concurrent_requests": 64,
      "max_execution_workers": 64,
      "queued_requests": 0,
      "running_requests": 0,
      "shared_provider_capacity": true,
      "warm_pool": {
        "starting": 0,
        "idle": 2,
        "active": 0,
        "closing": 0,
        "quarantined": 0,
        "unavailable": false,
        "resident_target": 2,
        "total": 2,
        "limit": 64,
        "peak": 2,
        "created": 2,
        "warm_hits": 0,
        "cold_starts": 0,
        "refill_failures": 0,
        "paused": false,
        "waiting_leases": 0
      },
      "warm_supported_providers": [
        "codex"
      ]
    },
    "other_settings_preserved": true,
    "all_prior_key_rows_preserved": true,
    "prior_key_rows": 56,
    "active_keys": 3,
    "effective_capacity": {
      "inference_resident": 2,
      "inference_pending": 64,
      "inference_workers": 64
    },
    "synthetic_requests": [
      {
        "protocol": "chat",
        "model": null,
        "status": "rejected",
        "prompt_tokens": null,
        "completion_tokens": null,
        "cost_usd": null,
        "calls_started": 0,
        "calls_completed": 0,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 2637,
        "completion_tokens": 6,
        "cost_usd": 0.005334,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 2664,
        "completion_tokens": 15,
        "cost_usd": 0.005478,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 2874,
        "completion_tokens": 34,
        "cost_usd": 0.006088,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "anthropic/claude-haiku-4.5",
        "status": "completed",
        "prompt_tokens": 562,
        "completion_tokens": 89,
        "cost_usd": 0.001007,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "anthropic/claude-haiku-4.5",
        "status": "completed",
        "prompt_tokens": 564,
        "completion_tokens": 110,
        "cost_usd": 0.001114,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "anthropic/claude-haiku-4.5",
        "status": "completed",
        "prompt_tokens": 1528,
        "completion_tokens": 332,
        "cost_usd": 0.003188,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "anthropic/claude-haiku-4.5",
        "status": "completed",
        "prompt_tokens": 1529,
        "completion_tokens": 347,
        "cost_usd": 0.003264,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 2631,
        "completion_tokens": 5,
        "cost_usd": 0.005312,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 2631,
        "completion_tokens": 5,
        "cost_usd": 0.005312,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 2773,
        "completion_tokens": 41,
        "cost_usd": 0.005956,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 2775,
        "completion_tokens": 37,
        "cost_usd": 0.00592,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      }
    ],
    "new_synthetic_keys_revoked": true,
    "rollback_ready": true,
    "personal_config_preserved": true,
    "profile_path_preserved": true,
    "success": true
  },
  "public_before": {
    "version": "0.9.10-mac.1",
    "source_commit": "26ab468b157747f1de6ea5dc3e934874b2f6bedf",
    "rounds": 2,
    "resident": 2,
    "workers": 64,
    "inference_retries": 0,
    "concurrent_requests": 1,
    "temporary_key_revoked": true,
    "settings_preserved": true,
    "owner_keys_preserved": true,
    "rows": [
      {
        "round": 1,
        "model": "openai/gpt-6.1-sol",
        "protocol": "chat",
        "request_id": "06d2b896-e139-452e-a55f-52f1a1ad1bee",
        "request_bytes": 112,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 6.4869,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 3121,
        "completion_tokens": 5,
        "cost_usd": 0.0016712,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 208,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 4964,
          "output_validation_ms": null,
          "total_ms": 5617
        },
        "cached_tokens": 2432,
        "reasoning_tokens": 0,
        "passed": true
      },
      {
        "round": 1,
        "model": "openai/gpt-6.1-sol",
        "protocol": "decisions",
        "request_id": "16308ce1-cd7d-4cd3-9b5e-9d7dad5955d5",
        "request_bytes": 148,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 5.689,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 3259,
        "completion_tokens": 36,
        "cost_usd": 0.006878,
        "timings_ms": {
          "validation_ms": 1,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 110,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 4340,
          "output_validation_ms": 0,
          "total_ms": 4697
        },
        "cached_tokens": 0,
        "reasoning_tokens": 18,
        "passed": true
      },
      {
        "round": 1,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "chat",
        "request_id": "e80f1354-3c22-43cd-adc7-ff8f6149831c",
        "request_bytes": 120,
        "http": 200,
        "seconds": 2.5758,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 564,
        "completion_tokens": 58,
        "cost_usd": 0.000854,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 148,
          "cli_spawn_ms": 2,
          "cli_ready_ms": null,
          "inference_ms": 1540,
          "output_validation_ms": null,
          "total_ms": 1697
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 1,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "decisions",
        "request_id": "1ca601b9-d23b-4297-9da4-46933bf7a037",
        "request_bytes": 156,
        "http": 200,
        "seconds": 3.9663,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 1485,
        "completion_tokens": 298,
        "cost_usd": 0.002975,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 209,
          "cli_spawn_ms": 3,
          "cli_ready_ms": null,
          "inference_ms": 2883,
          "output_validation_ms": 0,
          "total_ms": 3104
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 2,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "chat",
        "request_id": "d1303a50-cfcb-40e9-a066-0da1577714e6",
        "request_bytes": 120,
        "http": 200,
        "seconds": 2.8525,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 562,
        "completion_tokens": 74,
        "cost_usd": 0.000932,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 181,
          "cli_spawn_ms": 3,
          "cli_ready_ms": null,
          "inference_ms": 1737,
          "output_validation_ms": null,
          "total_ms": 1929
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 2,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "decisions",
        "request_id": "69123493-4368-4400-bd06-01022cba19cc",
        "request_bytes": 156,
        "http": 200,
        "seconds": 7.7767,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 3491,
        "completion_tokens": 633,
        "cost_usd": 0.006656,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 189,
          "cli_spawn_ms": 3,
          "cli_ready_ms": null,
          "inference_ms": 6615,
          "output_validation_ms": 0,
          "total_ms": 6816
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 2,
        "model": "openai/gpt-6.1-sol",
        "protocol": "chat",
        "request_id": "b3b22eab-c458-4e92-be19-e4d53ef19055",
        "request_bytes": 112,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 5.1086,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 3123,
        "completion_tokens": 5,
        "cost_usd": 0.0016752,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 211,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 3759,
          "output_validation_ms": null,
          "total_ms": 4218
        },
        "cached_tokens": 2432,
        "reasoning_tokens": 0,
        "passed": true
      },
      {
        "round": 2,
        "model": "openai/gpt-6.1-sol",
        "protocol": "decisions",
        "request_id": "6650eefa-c708-4da1-a20a-51bba6fd77d1",
        "request_bytes": 148,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 5.9008,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 3259,
        "completion_tokens": 40,
        "cost_usd": 0.006918,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 208,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 4501,
          "output_validation_ms": 0,
          "total_ms": 4989
        },
        "cached_tokens": 0,
        "reasoning_tokens": 22,
        "passed": true
      }
    ]
  },
  "public_after": {
    "version": "0.9.11-mac.1",
    "source_commit": "f9b481047485a9be8c0351a3b44139064e021c86",
    "rounds": 2,
    "resident": 2,
    "workers": 64,
    "inference_retries": 0,
    "concurrent_requests": 1,
    "temporary_key_revoked": true,
    "settings_preserved": true,
    "owner_keys_preserved": true,
    "rows": [
      {
        "round": 1,
        "model": "openai/gpt-6.1-sol",
        "protocol": "chat",
        "request_id": "3bdfd3e5-98e2-4601-8c84-58b2ede9b90e",
        "request_bytes": 112,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 5.1211,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 2631,
        "completion_tokens": 5,
        "cost_usd": 0.005312,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 183,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 3720,
          "output_validation_ms": null,
          "total_ms": 4136
        },
        "cached_tokens": 0,
        "reasoning_tokens": 0,
        "passed": true
      },
      {
        "round": 1,
        "model": "openai/gpt-6.1-sol",
        "protocol": "decisions",
        "request_id": "51e56a74-511d-4532-a427-641a1a638dd5",
        "request_bytes": 148,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 8.7614,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 2773,
        "completion_tokens": 41,
        "cost_usd": 0.005956,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 215,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 5689,
          "output_validation_ms": 0,
          "total_ms": 6143
        },
        "cached_tokens": 0,
        "reasoning_tokens": 23,
        "passed": true
      },
      {
        "round": 1,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "chat",
        "request_id": "9ecd28d5-bf78-4b96-9326-a25ee3299465",
        "request_bytes": 120,
        "http": 200,
        "seconds": 3.6486,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 564,
        "completion_tokens": 110,
        "cost_usd": 0.001114,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 192,
          "cli_spawn_ms": 2,
          "cli_ready_ms": null,
          "inference_ms": 2075,
          "output_validation_ms": null,
          "total_ms": 2279
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 1,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "decisions",
        "request_id": "ab3546b7-1832-4de6-b270-4e02f9cfc70a",
        "request_bytes": 156,
        "http": 200,
        "seconds": 5.0454,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 1528,
        "completion_tokens": 332,
        "cost_usd": 0.003188,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 206,
          "cli_spawn_ms": 3,
          "cli_ready_ms": null,
          "inference_ms": 3825,
          "output_validation_ms": 0,
          "total_ms": 4043
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 2,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "chat",
        "request_id": "b6fde5de-b198-4ac7-b656-7a6a61a0eba0",
        "request_bytes": 120,
        "http": 200,
        "seconds": 2.7865,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 562,
        "completion_tokens": 89,
        "cost_usd": 0.001007,
        "timings_ms": {
          "validation_ms": 1,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 210,
          "cli_spawn_ms": 3,
          "cli_ready_ms": null,
          "inference_ms": 1636,
          "output_validation_ms": null,
          "total_ms": 1858
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 2,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "decisions",
        "request_id": "8564ae8a-7f4a-4255-9735-5b8402292d0b",
        "request_bytes": 156,
        "http": 200,
        "seconds": 5.8193,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 1529,
        "completion_tokens": 347,
        "cost_usd": 0.003264,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 208,
          "cli_spawn_ms": 3,
          "cli_ready_ms": null,
          "inference_ms": 3680,
          "output_validation_ms": 0,
          "total_ms": 3900
        },
        "cached_tokens": 0,
        "reasoning_tokens": null,
        "passed": true
      },
      {
        "round": 2,
        "model": "openai/gpt-6.1-sol",
        "protocol": "chat",
        "request_id": "8cde5a23-8a51-4362-9c99-b5d83db531e7",
        "request_bytes": 112,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 5.7059,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 2631,
        "completion_tokens": 5,
        "cost_usd": 0.005312,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 189,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 3755,
          "output_validation_ms": null,
          "total_ms": 4159
        },
        "cached_tokens": 0,
        "reasoning_tokens": 0,
        "passed": true
      },
      {
        "round": 2,
        "model": "openai/gpt-6.1-sol",
        "protocol": "decisions",
        "request_id": "4e7c143d-68b5-492f-af72-aa93ee821a32",
        "request_bytes": 148,
        "ready_residents_before": 2,
        "http": 200,
        "seconds": 9.3669,
        "response_valid": true,
        "execution": {
          "warm_hits": 1,
          "cold_starts": 0
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 2775,
        "completion_tokens": 37,
        "cost_usd": 0.00592,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 186,
          "cli_spawn_ms": null,
          "cli_ready_ms": null,
          "inference_ms": 5953,
          "output_validation_ms": 0,
          "total_ms": 6352
        },
        "cached_tokens": 0,
        "reasoning_tokens": 19,
        "passed": true
      }
    ]
  },
  "comparison": [
    {
      "model": "openai/gpt-6.1-sol",
      "protocol": "chat",
      "samples_per_version": 2,
      "before_input_tokens": [
        3121,
        3123
      ],
      "after_input_tokens": [
        2631,
        2631
      ],
      "before_output_tokens": [
        5,
        5
      ],
      "after_output_tokens": [
        5,
        5
      ],
      "before_cached_tokens": [
        2432,
        2432
      ],
      "after_cached_tokens": [
        0,
        0
      ],
      "input_reduction_percent": 15.73,
      "before_median_seconds": 5.7978,
      "after_median_seconds": 5.4135,
      "median_time_reduction_percent": 6.63
    },
    {
      "model": "openai/gpt-6.1-sol",
      "protocol": "decisions",
      "samples_per_version": 2,
      "before_input_tokens": [
        3259,
        3259
      ],
      "after_input_tokens": [
        2773,
        2775
      ],
      "before_output_tokens": [
        36,
        40
      ],
      "after_output_tokens": [
        41,
        37
      ],
      "before_cached_tokens": [
        0,
        0
      ],
      "after_cached_tokens": [
        0,
        0
      ],
      "input_reduction_percent": 14.88,
      "before_median_seconds": 5.7949,
      "after_median_seconds": 9.0641,
      "median_time_reduction_percent": -56.42
    },
    {
      "model": "anthropic/claude-haiku-4.5",
      "protocol": "chat",
      "samples_per_version": 2,
      "before_input_tokens": [
        564,
        562
      ],
      "after_input_tokens": [
        564,
        562
      ],
      "before_output_tokens": [
        58,
        74
      ],
      "after_output_tokens": [
        110,
        89
      ],
      "before_cached_tokens": [
        0,
        0
      ],
      "after_cached_tokens": [
        0,
        0
      ],
      "input_reduction_percent": 0.0,
      "before_median_seconds": 2.7142,
      "after_median_seconds": 3.2176,
      "median_time_reduction_percent": -18.55
    },
    {
      "model": "anthropic/claude-haiku-4.5",
      "protocol": "decisions",
      "samples_per_version": 2,
      "before_input_tokens": [
        1485,
        3491
      ],
      "after_input_tokens": [
        1528,
        1529
      ],
      "before_output_tokens": [
        298,
        633
      ],
      "after_output_tokens": [
        332,
        347
      ],
      "before_cached_tokens": [
        0,
        0
      ],
      "after_cached_tokens": [
        0,
        0
      ],
      "input_reduction_percent": 38.57,
      "before_median_seconds": 5.8715,
      "after_median_seconds": 5.4323,
      "median_time_reduction_percent": 7.48
    }
  ],
  "native_types_and_untrusted_state": {
    "schema": 1,
    "concurrent_calls": 1,
    "inference_retries": 0,
    "raw_content_saved": false,
    "rows": [
      {
        "provider": "codex",
        "kind": "noul",
        "valid": true,
        "usage": {
          "prompt_tokens": 2792,
          "completion_tokens": 51,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 33
          }
        },
        "seconds": 8.265
      },
      {
        "provider": "codex",
        "kind": "choice",
        "valid": true,
        "usage": {
          "prompt_tokens": 2818,
          "completion_tokens": 44,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 24
          }
        },
        "seconds": 5.8494
      },
      {
        "provider": "codex",
        "kind": "score",
        "valid": true,
        "usage": {
          "prompt_tokens": 2801,
          "completion_tokens": 55,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 35
          }
        },
        "seconds": 5.819
      },
      {
        "provider": "claude",
        "kind": "noul",
        "valid": true,
        "usage": {
          "prompt_tokens": 1553,
          "completion_tokens": 822,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 7.9126,
        "native": {
          "num_turns": 2,
          "native_output": true,
          "assistant_messages": 1,
          "tool_names": [
            "StructuredOutput"
          ],
          "text_characters": 0
        }
      },
      {
        "provider": "claude",
        "kind": "choice",
        "valid": true,
        "usage": {
          "prompt_tokens": 1620,
          "completion_tokens": 517,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 4.6556,
        "native": {
          "num_turns": 2,
          "native_output": true,
          "assistant_messages": 1,
          "tool_names": [
            "StructuredOutput"
          ],
          "text_characters": 0
        }
      },
      {
        "provider": "claude",
        "kind": "score",
        "valid": true,
        "usage": {
          "prompt_tokens": 1601,
          "completion_tokens": 2095,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 16.9972,
        "native": {
          "num_turns": 2,
          "native_output": true,
          "assistant_messages": 1,
          "tool_names": [
            "StructuredOutput"
          ],
          "text_characters": 0
        }
      }
    ],
    "success": true
  },
  "release_attempt1": {
    "workflow": 40072496562,
    "attempt": 1,
    "failed_job": 120808756795,
    "core_passed": 311,
    "core_skipped": 18,
    "failure": "key_cleared_on_close_false",
    "publish_skipped": true,
    "release_created": false,
    "same_probe_local_and_pr_ci_passed": true,
    "analysis": "Probe reads key immediately after dialog.close; close listener that clears key runs as a queued browser event. Race is a source-based hypothesis; no gate bypass. Rerun failed job once at identical source; retain failure.",
    "raw_logs_saved": false,
    "production_changed": false
  },
  "close_event_probe": {
    "success": true,
    "old_worker_warning": true,
    "route_is_not_inference": true,
    "capacity_requires_pause": true,
    "capacity_rejects_invalid_pair": true,
    "capacity_zero_saved": true,
    "native_clipboard": true,
    "cancelled_export": true,
    "csv_export": true,
    "real_save_panel_cancel": true,
    "real_save_panel_save": true,
    "key_clear_immediate": true,
    "key_cleared_on_close": true,
    "synthetic_close_event_immediate": false,
    "synthetic_close_event_cleared": true,
    "navigation_bound": true,
    "service_after_viewer_close": true
  },
  "mock_summary": [
    {
      "case": "0911-False",
      "completed": true,
      "session_closed": true,
      "rollout_files": 0,
      "owned_processes_closed": null,
      "session_jsonl_files": null,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      }
    },
    {
      "case": "0911-True",
      "completed": true,
      "session_closed": true,
      "rollout_files": 0,
      "owned_processes_closed": null,
      "session_jsonl_files": null,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      }
    },
    {
      "case": "0911-False",
      "completed": true,
      "session_closed": null,
      "rollout_files": null,
      "owned_processes_closed": true,
      "session_jsonl_files": 0,
      "sent": null
    },
    {
      "case": "0911-True",
      "completed": true,
      "session_closed": null,
      "rollout_files": null,
      "owned_processes_closed": true,
      "session_jsonl_files": 0,
      "sent": null
    }
  ],
  "continuation_research": {
    "schema-dedup-mock.json": {
      "success": true,
      "real_inference_calls": 0,
      "results": [
        {
          "case": "schema-dedup-False-False",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.4063,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "context_management",
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 521,
                "o200k_estimate": 118,
                "sha256": "32dd9e0d710386beb14a4503f252b16ad64db5f52179c45c858e180bf839c038"
              },
              "messages": {
                "characters": 1421,
                "o200k_estimate": 378,
                "sha256": "88c28d9bc5fec58f31287f729f24c328a97eb46b5fceb1d81c8710826ad3ad21"
              },
              "tools": {
                "characters": 2,
                "o200k_estimate": 1,
                "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
              },
              "tool_names": [],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "d2b56ab9b4e7cf99208acb351991739dc4d60a4f80cfdbe047ea2b625a34cbba"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 232,
                  "o200k_estimate": 38,
                  "sha256": "4a63c88a851dbf74e78d2d6bc59f130498316d371ed234e565758a1827581d1e"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 2386,
                "o200k_estimate": 650,
                "sha256": "7093026a693f4b2993ca5db282fbaa9667930e28e38c5c0b5e70386f2b29e0f4"
              }
            }
          ],
          "routes": [
            "messages"
          ]
        },
        {
          "case": "schema-dedup-False-True",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.2919,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "context_management",
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 521,
                "o200k_estimate": 118,
                "sha256": "32dd9e0d710386beb14a4503f252b16ad64db5f52179c45c858e180bf839c038"
              },
              "messages": {
                "characters": 1421,
                "o200k_estimate": 380,
                "sha256": "059dadd91b0ababb571e418128c1d026daeae830363f7486d2cf84fd0788e537"
              },
              "tools": {
                "characters": 2,
                "o200k_estimate": 1,
                "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
              },
              "tool_names": [],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "d2b56ab9b4e7cf99208acb351991739dc4d60a4f80cfdbe047ea2b625a34cbba"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 232,
                  "o200k_estimate": 38,
                  "sha256": "4a63c88a851dbf74e78d2d6bc59f130498316d371ed234e565758a1827581d1e"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 2386,
                "o200k_estimate": 647,
                "sha256": "0c02c5c121fb7fd495449809628476e652ba678896dc3f44c0be25d16ef8e137"
              }
            }
          ],
          "routes": [
            "messages"
          ]
        },
        {
          "case": "schema-dedup-True-False",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.2882,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "context_management",
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 730,
                "o200k_estimate": 155,
                "sha256": "adcdf5dd07c3c1e3e51e425b57caec371c6cc49a5b7a6f0324b862952834b2c4"
              },
              "messages": {
                "characters": 2257,
                "o200k_estimate": 545,
                "sha256": "9cd2eab68b77a43c545fa63346db7d65d38daca534a190e51c80d1532f8b52c1"
              },
              "tools": {
                "characters": 370,
                "o200k_estimate": 79,
                "sha256": "1de21c784fbc689f747cbcd2afac358ed36a8693eb0be504126956f8928ecdf0"
              },
              "tool_names": [
                "StructuredOutput"
              ],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "424a969bed327b8bfe4d011b5c6068edbf4e4cf215af19d7bc3aa225fdcc7345"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 441,
                  "o200k_estimate": 75,
                  "sha256": "3b9c2afac7d1aa63db29f107e2ddd852eac701a7f454d44050a15c7f616f0e87"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 3799,
                "o200k_estimate": 926,
                "sha256": "24d32c896ce408387618d3432405ab745dd8f369f1eb391f67ec9dfdb2c91b6f"
              }
            }
          ],
          "routes": [
            "messages"
          ]
        },
        {
          "case": "schema-dedup-True-True",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.3079,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "context_management",
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 730,
                "o200k_estimate": 155,
                "sha256": "adcdf5dd07c3c1e3e51e425b57caec371c6cc49a5b7a6f0324b862952834b2c4"
              },
              "messages": {
                "characters": 2074,
                "o200k_estimate": 501,
                "sha256": "c7c13682358a49d38b85e573e0bdd416a2df7827fc75d3c1106b6fa6ac72f858"
              },
              "tools": {
                "characters": 370,
                "o200k_estimate": 79,
                "sha256": "1de21c784fbc689f747cbcd2afac358ed36a8693eb0be504126956f8928ecdf0"
              },
              "tool_names": [
                "StructuredOutput"
              ],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "424a969bed327b8bfe4d011b5c6068edbf4e4cf215af19d7bc3aa225fdcc7345"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 441,
                  "o200k_estimate": 75,
                  "sha256": "3b9c2afac7d1aa63db29f107e2ddd852eac701a7f454d44050a15c7f616f0e87"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 3616,
                "o200k_estimate": 885,
                "sha256": "ab63a1252da5f7e7167d6eb5323a60bd81146744025358ff464d2b3409c7f070"
              }
            }
          ],
          "routes": [
            "messages"
          ]
        }
      ]
    },
    "schema-dedup-research.json": {
      "schema": 1,
      "concurrent_calls": 1,
      "inference_retries": 0,
      "raw_content_saved": false,
      "candidate": "remove only duplicate generated schema from Claude stdin; keep native schema and all semantic instructions",
      "production_changed": false,
      "rows": [
        {
          "provider": "claude",
          "kind": "noul",
          "synthetic_semantic_check": true,
          "valid": true,
          "usage": {
            "prompt_tokens": 1508,
            "completion_tokens": 646,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 6.6684,
          "native": {
            "payload_bytes_before": 983,
            "payload_bytes_after": 824,
            "num_turns": 2,
            "native_output": true,
            "assistant_messages": 1,
            "tool_names": [
              "StructuredOutput"
            ],
            "text_characters": 0
          }
        },
        {
          "provider": "claude",
          "kind": "choice",
          "synthetic_semantic_check": true,
          "valid": true,
          "usage": {
            "prompt_tokens": 1557,
            "completion_tokens": 632,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 6.2391,
          "native": {
            "payload_bytes_before": 1130,
            "payload_bytes_after": 902,
            "num_turns": 2,
            "native_output": true,
            "assistant_messages": 1,
            "tool_names": [
              "StructuredOutput"
            ],
            "text_characters": 0
          }
        },
        {
          "provider": "claude",
          "kind": "score",
          "synthetic_semantic_check": true,
          "valid": true,
          "usage": {
            "prompt_tokens": 1539,
            "completion_tokens": 470,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 4.2477,
          "native": {
            "payload_bytes_before": 1069,
            "payload_bytes_after": 841,
            "num_turns": 2,
            "native_output": true,
            "assistant_messages": 1,
            "tool_names": [
              "StructuredOutput"
            ],
            "text_characters": 0
          }
        }
      ],
      "success": true
    },
    "thinking-off-research.json": {
      "schema": 1,
      "concurrent_calls": 1,
      "inference_retries": 0,
      "raw_content_saved": false,
      "candidate": "Haiku 4.5 native child MAX_THINKING_TOKENS=0; reasoning behavior changes, quality not established",
      "production_changed": false,
      "rows": [
        {
          "provider": "claude",
          "kind": "noul",
          "synthetic_semantic_check": true,
          "valid": true,
          "usage": {
            "prompt_tokens": 1376,
            "completion_tokens": 58,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 1.9513,
          "native": {
            "num_turns": 2,
            "native_output": true,
            "assistant_messages": 1,
            "tool_names": [
              "StructuredOutput"
            ],
            "text_characters": 0
          }
        },
        {
          "provider": "claude",
          "kind": "choice",
          "synthetic_semantic_check": true,
          "valid": true,
          "usage": {
            "prompt_tokens": 1441,
            "completion_tokens": 65,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 1.6522,
          "native": {
            "num_turns": 2,
            "native_output": true,
            "assistant_messages": 1,
            "tool_names": [
              "StructuredOutput"
            ],
            "text_characters": 0
          }
        },
        {
          "provider": "claude",
          "kind": "score",
          "synthetic_semantic_check": true,
          "valid": true,
          "usage": {
            "prompt_tokens": 1424,
            "completion_tokens": 61,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 2.0833,
          "native": {
            "num_turns": 2,
            "native_output": true,
            "assistant_messages": 1,
            "tool_names": [
              "StructuredOutput"
            ],
            "text_characters": 0
          }
        }
      ],
      "success": true
    },
    "thinking-mock.json": {
      "success": true,
      "real_inference_calls": 0,
      "results": [
        {
          "case": "current",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.2433,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "context_management",
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 730,
                "o200k_estimate": 155,
                "sha256": "adcdf5dd07c3c1e3e51e425b57caec371c6cc49a5b7a6f0324b862952834b2c4"
              },
              "messages": {
                "characters": 2257,
                "o200k_estimate": 546,
                "sha256": "51300467ab301a0a050e6eba380f8435473a3920b70ec80cbf5fe0841ea59f6d"
              },
              "tools": {
                "characters": 370,
                "o200k_estimate": 79,
                "sha256": "1de21c784fbc689f747cbcd2afac358ed36a8693eb0be504126956f8928ecdf0"
              },
              "tool_names": [
                "StructuredOutput"
              ],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "424a969bed327b8bfe4d011b5c6068edbf4e4cf215af19d7bc3aa225fdcc7345"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 441,
                  "o200k_estimate": 75,
                  "sha256": "3b9c2afac7d1aa63db29f107e2ddd852eac701a7f454d44050a15c7f616f0e87"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 3799,
                "o200k_estimate": 925,
                "sha256": "ab96dc74de58f383388cfc216a8d9925edff3c967be7a26f1815b0aed7ad0d8d"
              },
              "thinking": {
                "budget_tokens": 31999,
                "type": "enabled"
              },
              "effort": null
            }
          ],
          "routes": [
            "messages"
          ]
        },
        {
          "case": "thinking_off",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.2888,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "temperature",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 730,
                "o200k_estimate": 155,
                "sha256": "adcdf5dd07c3c1e3e51e425b57caec371c6cc49a5b7a6f0324b862952834b2c4"
              },
              "messages": {
                "characters": 2257,
                "o200k_estimate": 545,
                "sha256": "fc080c8aa6ba70a296640585a8519eb9c6e4cd861bbcd81ef16549134433f286"
              },
              "tools": {
                "characters": 370,
                "o200k_estimate": 79,
                "sha256": "1de21c784fbc689f747cbcd2afac358ed36a8693eb0be504126956f8928ecdf0"
              },
              "tool_names": [
                "StructuredOutput"
              ],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "424a969bed327b8bfe4d011b5c6068edbf4e4cf215af19d7bc3aa225fdcc7345"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 441,
                  "o200k_estimate": 75,
                  "sha256": "3b9c2afac7d1aa63db29f107e2ddd852eac701a7f454d44050a15c7f616f0e87"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 3693,
                "o200k_estimate": 898,
                "sha256": "020836dcfcd5ceb6ce055e0d1b62c5dfbd8b5ca22a28a5615c8bb7765c08b828"
              },
              "thinking": {
                "type": "disabled"
              },
              "effort": null
            }
          ],
          "routes": [
            "messages"
          ]
        },
        {
          "case": "simple_system",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.3095,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "context_management",
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 730,
                "o200k_estimate": 155,
                "sha256": "adcdf5dd07c3c1e3e51e425b57caec371c6cc49a5b7a6f0324b862952834b2c4"
              },
              "messages": {
                "characters": 2257,
                "o200k_estimate": 545,
                "sha256": "0419358ac4f6612cfd1da5722c0096f48a653a930190a37e5934233d6503931b"
              },
              "tools": {
                "characters": 370,
                "o200k_estimate": 79,
                "sha256": "1de21c784fbc689f747cbcd2afac358ed36a8693eb0be504126956f8928ecdf0"
              },
              "tool_names": [
                "StructuredOutput"
              ],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "424a969bed327b8bfe4d011b5c6068edbf4e4cf215af19d7bc3aa225fdcc7345"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 441,
                  "o200k_estimate": 75,
                  "sha256": "3b9c2afac7d1aa63db29f107e2ddd852eac701a7f454d44050a15c7f616f0e87"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 3799,
                "o200k_estimate": 931,
                "sha256": "b119322af5468a0b3ba86536d9ebd0bdb7ea2a4356f772c98de43fddd8e2102d"
              },
              "thinking": {
                "budget_tokens": 31999,
                "type": "enabled"
              },
              "effort": null
            }
          ],
          "routes": [
            "messages"
          ]
        },
        {
          "case": "thinking_off_simple",
          "real_inference_calls": 0,
          "raw_payload_saved": false,
          "fixture_auth_only": true,
          "completed": true,
          "seconds": 0.3119,
          "returned_model_matches": true,
          "session_jsonl_files": 0,
          "owned_processes_closed": true,
          "captures": [
            {
              "keys": [
                "max_tokens",
                "messages",
                "metadata",
                "model",
                "stream",
                "system",
                "temperature",
                "thinking",
                "tools"
              ],
              "system": {
                "characters": 730,
                "o200k_estimate": 155,
                "sha256": "adcdf5dd07c3c1e3e51e425b57caec371c6cc49a5b7a6f0324b862952834b2c4"
              },
              "messages": {
                "characters": 2257,
                "o200k_estimate": 545,
                "sha256": "46bcce4cd926d387ab16eae09a41f7f442b0e2d03103de0e5f8a8f2e146eb143"
              },
              "tools": {
                "characters": 370,
                "o200k_estimate": 79,
                "sha256": "1de21c784fbc689f747cbcd2afac358ed36a8693eb0be504126956f8928ecdf0"
              },
              "tool_names": [
                "StructuredOutput"
              ],
              "system_blocks": [
                {
                  "characters": 74,
                  "o200k_estimate": 26,
                  "sha256": "424a969bed327b8bfe4d011b5c6068edbf4e4cf215af19d7bc3aa225fdcc7345"
                },
                {
                  "characters": 62,
                  "o200k_estimate": 15,
                  "sha256": "0d7062851dd7bd7e66d4be4f12ac4951e3d2f587ec408295333a49963bd3f6b7"
                },
                {
                  "characters": 441,
                  "o200k_estimate": 75,
                  "sha256": "3b9c2afac7d1aa63db29f107e2ddd852eac701a7f454d44050a15c7f616f0e87"
                }
              ],
              "markers": {
                "CLAUDE.md": false,
                "SKILL.md": false,
                "available_skills": false,
                "system-reminder": true,
                "You are Claude Code": false,
                "Bash": false,
                "TodoWrite": false,
                "TaskCreate": false,
                "EndConversation": false
              },
              "body": {
                "characters": 3693,
                "o200k_estimate": 897,
                "sha256": "1563d1415af16a27fe81fe13197b88b4d04de6876c7dce3edfff55579c566db6"
              },
              "thinking": {
                "type": "disabled"
              },
              "effort": null
            }
          ],
          "routes": [
            "messages"
          ]
        }
      ]
    }
  },
  "raw_content_or_credentials_saved": false,
  "worker_deployed": false,
  "windows_release_published": false,
  "final_state_after_research": {
    "installed_version": "0.9.11-mac.1",
    "source_commit": "f9b481047485a9be8c0351a3b44139064e021c86",
    "health_version": "0.9.11-mac.1",
    "accepting": true,
    "resident": 2,
    "idle": 2,
    "workers": 64,
    "pending": 64,
    "running": 0,
    "queued": 0,
    "refill_failures": 0,
    "installed_core_files": 49,
    "installed_public_reviewed_core_match": true,
    "profile_path_preserved": true,
    "prior_key_rows_preserved": true,
    "key_rows": 58,
    "active_owner_keys": 3,
    "new_test_key_rows": 2,
    "new_test_keys_revoked": true,
    "personal_codex_config_preserved": true,
    "cli_versions": {
      "codex": "0.163.0-alpha.11",
      "claude": "2.1.306"
    },
    "research_candidate_persisted": false,
    "success": true
  },
  "inference_totals_and_research_summary": {
    "real_inference_calls": 31,
    "input_tokens": 64062,
    "output_tokens": 7686,
    "research": [
      {
        "candidate": "schema-dedup-research",
        "type": "noul",
        "baseline_input": 1553,
        "candidate_input": 1508,
        "input_reduction_percent": 2.9,
        "baseline_output": 822,
        "candidate_output": 646,
        "output_reduction_percent": 21.41,
        "baseline_seconds": 7.9126,
        "candidate_seconds": 6.6684,
        "synthetic_semantic_check": true
      },
      {
        "candidate": "thinking-off-research",
        "type": "noul",
        "baseline_input": 1553,
        "candidate_input": 1376,
        "input_reduction_percent": 11.4,
        "baseline_output": 822,
        "candidate_output": 58,
        "output_reduction_percent": 92.94,
        "baseline_seconds": 7.9126,
        "candidate_seconds": 1.9513,
        "synthetic_semantic_check": true
      },
      {
        "candidate": "schema-dedup-research",
        "type": "choice",
        "baseline_input": 1620,
        "candidate_input": 1557,
        "input_reduction_percent": 3.89,
        "baseline_output": 517,
        "candidate_output": 632,
        "output_reduction_percent": -22.24,
        "baseline_seconds": 4.6556,
        "candidate_seconds": 6.2391,
        "synthetic_semantic_check": true
      },
      {
        "candidate": "thinking-off-research",
        "type": "choice",
        "baseline_input": 1620,
        "candidate_input": 1441,
        "input_reduction_percent": 11.05,
        "baseline_output": 517,
        "candidate_output": 65,
        "output_reduction_percent": 87.43,
        "baseline_seconds": 4.6556,
        "candidate_seconds": 1.6522,
        "synthetic_semantic_check": true
      },
      {
        "candidate": "schema-dedup-research",
        "type": "score",
        "baseline_input": 1601,
        "candidate_input": 1539,
        "input_reduction_percent": 3.87,
        "baseline_output": 2095,
        "candidate_output": 470,
        "output_reduction_percent": 77.57,
        "baseline_seconds": 16.9972,
        "candidate_seconds": 4.2477,
        "synthetic_semantic_check": true
      },
      {
        "candidate": "thinking-off-research",
        "type": "score",
        "baseline_input": 1601,
        "candidate_input": 1424,
        "input_reduction_percent": 11.06,
        "baseline_output": 2095,
        "candidate_output": 61,
        "output_reduction_percent": 97.09,
        "baseline_seconds": 16.9972,
        "candidate_seconds": 2.0833,
        "synthetic_semantic_check": true
      }
    ]
  },
  "upgrade_checks": [
    {
      "check": "original_key_before_update",
      "passed": true,
      "http": 200
    },
    {
      "check": "source_update",
      "passed": true
    },
    {
      "check": "installed_release_provenance",
      "passed": true,
      "version": "0.9.11-mac.1",
      "source_commit": "f9b481047485a9be8c0351a3b44139064e021c86"
    },
    {
      "check": "device_keys_models_capacity_preserved",
      "passed": true,
      "version": "0.9.11-mac.1",
      "inference_workers": 64
    },
    {
      "check": "same_key_after_update",
      "passed": true,
      "http": 200
    },
    {
      "check": "https_chat_cost_locked",
      "passed": true,
      "http": 200,
      "seconds": 5.922,
      "locked_before": true,
      "locked_after": true,
      "cost_usd": 0.005334,
      "model": "openai/gpt-6.1-sol"
    },
    {
      "check": "deduplicated_same_request",
      "passed": true
    },
    {
      "check": "https_structured_output",
      "passed": true,
      "http": 200
    },
    {
      "check": "https_tool_proposal_only",
      "passed": true,
      "http": 200
    },
    {
      "check": "unsupported_parameter",
      "passed": true,
      "http": 400
    },
    {
      "check": "handoff_complete",
      "passed": true
    },
    {
      "check": "completed",
      "passed": true,
      "owner_service_keys_preserved": true
    },
    {
      "check": "temporary_key_revoked",
      "passed": true,
      "owner_service_keys_preserved": true
    }
  ]
}
```
