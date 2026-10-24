# Mac 0.9.9 常駐 API：數字證據

僅合成測試 metadata；不含 client KEY、原始 request／response、CLI event 或 stderr。原設定／Key 值不公開，僅比對結果。

```json
{
  "schema": 1,
  "version": "0.9.9-mac.1",
  "source_commit": "2be8195037c304b988c46f8a48697486978b3592",
  "zip_sha256": "f3ac1fb5f028765c50e55c9e2beb2385c8a4ed82649f08eb53fad652c58989ef",
  "release": "https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.9-mac.1",
  "release_workflow_run": 40063639810,
  "pr": 44,
  "reviewed_head": "b62a2e86963e27fcca6cdcb8018f3ebc46211282",
  "ci_runs": {
    "core": 40063091162,
    "mac": 40063091158,
    "windows": 40063091176,
    "windows_installer": 40063091166
  },
  "local_tests": {
    "passed": 454,
    "skipped": 23,
    "worker_passed": 13,
    "native_screen_count": 64,
    "native_console": {
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
      "key_cleared_on_close": true,
      "navigation_bound": true,
      "service_after_viewer_close": true
    }
  },
  "download": {
    "success": true,
    "assets": [
      "aigo-llm-bridge-macos-source-0.9.9-mac.1.zip",
      "aigo-llm-bridge-macos-source-0.9.9-mac.1.zip.sha256",
      "macos-source-manifest.json",
      "macos-source-self-test.json"
    ],
    "anonymous_download": true,
    "authorization_header_used": false,
    "runtime_and_opt_in_tools_match_reviewed_source": true,
    "manifest_clean": true
  },
  "public_package": {
    "success": true,
    "public_zip": true,
    "original_version": "0.9.8-mac.1",
    "version": "0.9.9-mac.1",
    "source_commit": "2be8195037c304b988c46f8a48697486978b3592",
    "download_installed": true,
    "fixed_machine_lock": true,
    "rejected_profile_no_database": true,
    "shutdown_api_closed": true,
    "max_concurrent_requests": 64,
    "credentials_or_power_changed": false,
    "original_restart_command_ok": true,
    "original_restored_healthy": true
  },
  "original_profile_upgrade": [
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
      "version": "0.9.9-mac.1",
      "source_commit": "2be8195037c304b988c46f8a48697486978b3592"
    },
    {
      "check": "device_keys_models_capacity_preserved",
      "passed": true,
      "version": "0.9.9-mac.1",
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
      "seconds": 4.279,
      "locked_before": false,
      "locked_after": false,
      "cost_usd": 0.008454,
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
  ],
  "runtime_acceptance": {
    "version": "0.9.9-mac.1",
    "source_commit": "2be8195037c304b988c46f8a48697486978b3592",
    "before_stop": {
      "ok": true,
      "version": "0.9.9-mac.1",
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
    "observed_owned_processes": 3,
    "observed_empty_cwds": 2,
    "stop_seconds": 0.7116,
    "owned_processes_remaining": 0,
    "old_cwds_remaining": 0,
    "restart_ok": true,
    "final_health": {
      "ok": true,
      "version": "0.9.9-mac.1",
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
    "prior_key_rows": 45,
    "active_keys": 3,
    "effective_capacity": {
      "inference_pending": 64,
      "inference_resident": 2,
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
        "prompt_tokens": 4197,
        "completion_tokens": 6,
        "cost_usd": 0.008454,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4226,
        "completion_tokens": 15,
        "cost_usd": 0.008602,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4436,
        "completion_tokens": 34,
        "cost_usd": 0.009212,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4191,
        "completion_tokens": 5,
        "cost_usd": 0.008432,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4193,
        "completion_tokens": 5,
        "cost_usd": 0.008436,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4193,
        "completion_tokens": 5,
        "cost_usd": 0.008436,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4329,
        "completion_tokens": 29,
        "cost_usd": 0.008948,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4331,
        "completion_tokens": 46,
        "cost_usd": 0.009122,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4335,
        "completion_tokens": 40,
        "cost_usd": 0.00907,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4191,
        "completion_tokens": 5,
        "cost_usd": 0.008432,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4191,
        "completion_tokens": 5,
        "cost_usd": 0.008432,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "chat",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4193,
        "completion_tokens": 5,
        "cost_usd": 0.008436,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4331,
        "completion_tokens": 31,
        "cost_usd": 0.0031352,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4331,
        "completion_tokens": 38,
        "cost_usd": 0.009042,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      },
      {
        "protocol": "decisions",
        "model": "openai/gpt-6.1-sol",
        "status": "completed",
        "prompt_tokens": 4335,
        "completion_tokens": 37,
        "cost_usd": 0.00904,
        "calls_started": 1,
        "calls_completed": 1,
        "billing_complete": 1
      }
    ],
    "new_synthetic_keys_revoked": true,
    "rollback_ready": true,
    "profile_path_preserved": true,
    "success": true
  },
  "initial_helper_failure": {
    "success": false,
    "kind": "test_helper_readiness_race",
    "reason": "Health read immediately after asynchronous LaunchAgent start did not wait for listener.",
    "inference_retried": false,
    "service_restored_healthy": true,
    "resident": 2,
    "idle": 2
  },
  "host_and_cli_versions": {
    "macos": "26.2",
    "architecture": "arm64",
    "logical_cpus": 10,
    "cli_versions": {
      "codex": "codex-cli 0.163.0-alpha.11",
      "claude": "2.1.306 (Claude Code)"
    }
  },
  "cache_metadata": {
    "kind": "post-run read-only numeric SQLite cache metadata",
    "arms": {
      "off": [
        {
          "protocol": "chat",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 0,
          "prompt_tokens": 4193,
          "completion_tokens": 5,
          "cost_usd": 0.008436
        },
        {
          "protocol": "decisions",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 22,
          "prompt_tokens": 4335,
          "completion_tokens": 40,
          "cost_usd": 0.00907
        },
        {
          "protocol": "chat",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 0,
          "prompt_tokens": 4193,
          "completion_tokens": 5,
          "cost_usd": 0.008436
        },
        {
          "protocol": "decisions",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 11,
          "prompt_tokens": 4329,
          "completion_tokens": 29,
          "cost_usd": 0.008948
        },
        {
          "protocol": "chat",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 0,
          "prompt_tokens": 4191,
          "completion_tokens": 5,
          "cost_usd": 0.008432
        },
        {
          "protocol": "decisions",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 28,
          "prompt_tokens": 4331,
          "completion_tokens": 46,
          "cost_usd": 0.009122
        }
      ],
      "on": [
        {
          "protocol": "chat",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 0,
          "prompt_tokens": 4193,
          "completion_tokens": 5,
          "cost_usd": 0.008436
        },
        {
          "protocol": "decisions",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 19,
          "prompt_tokens": 4335,
          "completion_tokens": 37,
          "cost_usd": 0.00904
        },
        {
          "protocol": "chat",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 0,
          "prompt_tokens": 4191,
          "completion_tokens": 5,
          "cost_usd": 0.008432
        },
        {
          "protocol": "decisions",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 3072,
          "cache_write_tokens": 0,
          "reasoning_tokens": 13,
          "prompt_tokens": 4331,
          "completion_tokens": 31,
          "cost_usd": 0.0031352
        },
        {
          "protocol": "chat",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 0,
          "prompt_tokens": 4191,
          "completion_tokens": 5,
          "cost_usd": 0.008432
        },
        {
          "protocol": "decisions",
          "model": "openai/gpt-6.1-sol",
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": 20,
          "prompt_tokens": 4331,
          "completion_tokens": 38,
          "cost_usd": 0.009042
        }
      ]
    }
  },
  "comparison": [
    {
      "protocol": "chat",
      "samples_per_arm": 3,
      "off_median_seconds": 4.3936,
      "on_median_seconds": 4.2353,
      "change_percent_faster": 3.6,
      "off_bridge_median_ms": 3497,
      "on_bridge_median_ms": 3370,
      "off_warm_hits": 0,
      "on_warm_hits": 3,
      "off_cold_starts": 3,
      "on_cold_starts": 0
    },
    {
      "protocol": "decisions",
      "samples_per_arm": 3,
      "off_median_seconds": 5.0333,
      "on_median_seconds": 4.6713,
      "change_percent_faster": 7.19,
      "off_bridge_median_ms": 4137,
      "on_bridge_median_ms": 3779,
      "off_warm_hits": 0,
      "on_warm_hits": 3,
      "off_cold_starts": 3,
      "on_cold_starts": 0
    }
  ],
  "arms": {
    "off": {
      "health_before": {
        "ok": true,
        "version": "0.9.9-mac.1",
        "accepting": true,
        "max_concurrent_requests": 64,
        "max_execution_workers": 64,
        "queued_requests": 0,
        "running_requests": 0,
        "shared_provider_capacity": true,
        "warm_pool": {
          "starting": 0,
          "idle": 0,
          "active": 0,
          "closing": 0,
          "quarantined": 0,
          "unavailable": false,
          "resident_target": 0,
          "total": 0,
          "limit": 64,
          "peak": 0,
          "created": 0,
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
      "health_after": {
        "ok": true,
        "version": "0.9.9-mac.1",
        "accepting": true,
        "max_concurrent_requests": 64,
        "max_execution_workers": 64,
        "queued_requests": 0,
        "running_requests": 0,
        "shared_provider_capacity": true,
        "warm_pool": {
          "starting": 0,
          "idle": 0,
          "active": 0,
          "closing": 0,
          "quarantined": 0,
          "unavailable": false,
          "resident_target": 0,
          "total": 0,
          "limit": 64,
          "peak": 2,
          "created": 7,
          "warm_hits": 0,
          "cold_starts": 7,
          "refill_failures": 0,
          "paused": false,
          "waiting_leases": 0
        },
        "warm_supported_providers": [
          "codex"
        ]
      },
      "metadata": {
        "success": true,
        "version": "0.9.9-mac.1",
        "source_commit": "2be8195037c304b988c46f8a48697486978b3592",
        "transport": "public HTTPS",
        "rounds": 3,
        "inference_retries": 0,
        "concurrent_requests": 1,
        "warm_pool_enabled": false,
        "resident": 0,
        "workers": 64,
        "temporary_key_revoked": true,
        "settings_preserved": true,
        "owner_keys_preserved": true
      },
      "rows": [
        {
          "round": 1,
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "request_bytes": 112,
          "http": 200,
          "seconds": 4.4862,
          "response_valid": true,
          "execution": {
            "warm_hits": 0,
            "cold_starts": 1
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4193,
          "completion_tokens": 5,
          "cost_usd": 0.008436,
          "timings_ms": {
            "validation_ms": 1,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 59,
            "cli_spawn_ms": 5,
            "cli_ready_ms": 72,
            "inference_ms": 3155,
            "output_validation_ms": null,
            "total_ms": 3497
          },
          "passed": true
        },
        {
          "round": 1,
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "request_bytes": 148,
          "http": 200,
          "seconds": 5.0903,
          "response_valid": true,
          "execution": {
            "warm_hits": 0,
            "cold_starts": 1
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4335,
          "completion_tokens": 40,
          "cost_usd": 0.00907,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 66,
            "cli_spawn_ms": 5,
            "cli_ready_ms": 74,
            "inference_ms": 3788,
            "output_validation_ms": 0,
            "total_ms": 4148
          },
          "passed": true
        },
        {
          "round": 2,
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "request_bytes": 112,
          "http": 200,
          "seconds": 4.3936,
          "response_valid": true,
          "execution": {
            "warm_hits": 0,
            "cold_starts": 1
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4193,
          "completion_tokens": 5,
          "cost_usd": 0.008436,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 128,
            "cli_spawn_ms": 4,
            "cli_ready_ms": 73,
            "inference_ms": 3003,
            "output_validation_ms": null,
            "total_ms": 3391
          },
          "passed": true
        },
        {
          "round": 2,
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "request_bytes": 148,
          "http": 200,
          "seconds": 4.6075,
          "response_valid": true,
          "execution": {
            "warm_hits": 0,
            "cold_starts": 1
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4329,
          "completion_tokens": 29,
          "cost_usd": 0.008948,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 101,
            "cli_spawn_ms": 5,
            "cli_ready_ms": 77,
            "inference_ms": 3344,
            "output_validation_ms": 0,
            "total_ms": 3691
          },
          "passed": true
        },
        {
          "round": 3,
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "request_bytes": 112,
          "http": 200,
          "seconds": 4.3837,
          "response_valid": true,
          "execution": {
            "warm_hits": 0,
            "cold_starts": 1
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4191,
          "completion_tokens": 5,
          "cost_usd": 0.008432,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 128,
            "cli_spawn_ms": 5,
            "cli_ready_ms": 73,
            "inference_ms": 3157,
            "output_validation_ms": null,
            "total_ms": 3519
          },
          "passed": true
        },
        {
          "round": 3,
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "request_bytes": 148,
          "http": 200,
          "seconds": 5.0333,
          "response_valid": true,
          "execution": {
            "warm_hits": 0,
            "cold_starts": 1
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4331,
          "completion_tokens": 46,
          "cost_usd": 0.009122,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 128,
            "cli_spawn_ms": 4,
            "cli_ready_ms": 67,
            "inference_ms": 3749,
            "output_validation_ms": 0,
            "total_ms": 4137
          },
          "passed": true
        }
      ],
      "summary": [
        {
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "requests": 3,
          "passed": 3,
          "median_seconds": 4.3936,
          "max_seconds": 4.4862
        },
        {
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "requests": 3,
          "passed": 3,
          "median_seconds": 5.0333,
          "max_seconds": 5.0903
        }
      ]
    },
    "on": {
      "health_before": {
        "ok": true,
        "version": "0.9.9-mac.1",
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
      "health_after": {
        "ok": true,
        "version": "0.9.9-mac.1",
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
          "created": 8,
          "warm_hits": 6,
          "cold_starts": 0,
          "refill_failures": 0,
          "paused": false,
          "waiting_leases": 0
        },
        "warm_supported_providers": [
          "codex"
        ]
      },
      "metadata": {
        "success": true,
        "version": "0.9.9-mac.1",
        "source_commit": "2be8195037c304b988c46f8a48697486978b3592",
        "transport": "public HTTPS",
        "rounds": 3,
        "inference_retries": 0,
        "concurrent_requests": 1,
        "warm_pool_enabled": true,
        "resident": 2,
        "workers": 64,
        "temporary_key_revoked": true,
        "settings_preserved": true,
        "owner_keys_preserved": true
      },
      "rows": [
        {
          "round": 1,
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "request_bytes": 112,
          "ready_residents_before": 2,
          "http": 200,
          "seconds": 4.2353,
          "response_valid": true,
          "execution": {
            "warm_hits": 1,
            "cold_starts": 0
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4193,
          "completion_tokens": 5,
          "cost_usd": 0.008436,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 129,
            "cli_spawn_ms": null,
            "cli_ready_ms": null,
            "inference_ms": 3051,
            "output_validation_ms": null,
            "total_ms": 3370
          },
          "passed": true
        },
        {
          "round": 1,
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "request_bytes": 148,
          "ready_residents_before": 2,
          "http": 200,
          "seconds": 4.3871,
          "response_valid": true,
          "execution": {
            "warm_hits": 1,
            "cold_starts": 0
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4335,
          "completion_tokens": 37,
          "cost_usd": 0.00904,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 98,
            "cli_spawn_ms": null,
            "cli_ready_ms": null,
            "inference_ms": 3316,
            "output_validation_ms": 0,
            "total_ms": 3567
          },
          "passed": true
        },
        {
          "round": 2,
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "request_bytes": 112,
          "ready_residents_before": 2,
          "http": 200,
          "seconds": 3.9647,
          "response_valid": true,
          "execution": {
            "warm_hits": 1,
            "cold_starts": 0
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4191,
          "completion_tokens": 5,
          "cost_usd": 0.008432,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 126,
            "cli_spawn_ms": null,
            "cli_ready_ms": null,
            "inference_ms": 2856,
            "output_validation_ms": null,
            "total_ms": 3123
          },
          "passed": true
        },
        {
          "round": 2,
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "request_bytes": 148,
          "ready_residents_before": 2,
          "http": 200,
          "seconds": 4.6713,
          "response_valid": true,
          "execution": {
            "warm_hits": 1,
            "cold_starts": 0
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4331,
          "completion_tokens": 31,
          "cost_usd": 0.0031352,
          "timings_ms": {
            "validation_ms": 0,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 88,
            "cli_spawn_ms": null,
            "cli_ready_ms": null,
            "inference_ms": 3513,
            "output_validation_ms": 0,
            "total_ms": 3779
          },
          "passed": true
        },
        {
          "round": 3,
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "request_bytes": 112,
          "ready_residents_before": 2,
          "http": 200,
          "seconds": 4.5163,
          "response_valid": true,
          "execution": {
            "warm_hits": 1,
            "cold_starts": 0
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4191,
          "completion_tokens": 5,
          "cost_usd": 0.008432,
          "timings_ms": {
            "validation_ms": 1,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 129,
            "cli_spawn_ms": null,
            "cli_ready_ms": null,
            "inference_ms": 3261,
            "output_validation_ms": null,
            "total_ms": 3550
          },
          "passed": true
        },
        {
          "round": 3,
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "request_bytes": 148,
          "ready_residents_before": 2,
          "http": 200,
          "seconds": 4.7277,
          "response_valid": true,
          "execution": {
            "warm_hits": 1,
            "cold_starts": 0
          },
          "lease_valid": true,
          "receipt_http": 200,
          "receipt_complete": true,
          "cost_matches": true,
          "prompt_tokens": 4331,
          "completion_tokens": 38,
          "cost_usd": 0.009042,
          "timings_ms": {
            "validation_ms": 1,
            "schema_wait_ms": null,
            "schema_execution_ms": null,
            "queue_wait_ms": 0,
            "provider_setup_ms": 107,
            "cli_spawn_ms": null,
            "cli_ready_ms": null,
            "inference_ms": 3666,
            "output_validation_ms": 0,
            "total_ms": 3936
          },
          "passed": true
        }
      ],
      "summary": [
        {
          "model": "openai/gpt-6.1-sol",
          "protocol": "chat",
          "requests": 3,
          "passed": 3,
          "median_seconds": 4.2353,
          "max_seconds": 4.5163
        },
        {
          "model": "openai/gpt-6.1-sol",
          "protocol": "decisions",
          "requests": 3,
          "passed": 3,
          "median_seconds": 4.6713,
          "max_seconds": 4.7277
        }
      ]
    }
  },
  "synthetic_totals": {
    "cli_attempts": 15,
    "unique_requests": 16,
    "expected_zero_inference_rejections": 1,
    "prompt_tokens": 64003,
    "completion_tokens": 306,
    "cost_usd": 0.1252292
  },
  "complete_general_warm_gate": false,
  "claude_warm_supported": false,
  "external_user_benchmark": "pending owner-run independent test"
}
```
