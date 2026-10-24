# Mac 0.9.12 純 Chat pre-release metadata

2026-10-24；合成內容只在 RAM／管線，以下為 allowlist metadata。公開 API／發布／正式部署證據於完成後另補，不以候選測試代替。

## credential-free native mock

```json
{
  "real_inference_calls": 0,
  "raw_content_saved": false,
  "rows": [
    {
      "arm": "cold",
      "caller_estimate": 500,
      "completed": true,
      "error_category": null,
      "pre_lease_sent": [
        {
          "initialize": 1,
          "initialized": 1,
          "skills/list": 0,
          "thread/start": 0,
          "turn/start": 0,
          "config/read": 0
        }
      ],
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "rollout_files": 0,
      "closed": true,
      "auth_header_present": false,
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        0
      ],
      "caller_hash_matches": true,
      "valid": true
    },
    {
      "arm": "warm",
      "caller_estimate": 500,
      "completed": true,
      "error_category": null,
      "pre_lease_sent": [
        {
          "initialize": 1,
          "initialized": 1,
          "skills/list": 0,
          "thread/start": 0,
          "turn/start": 0,
          "config/read": 1
        }
      ],
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 2
      },
      "rollout_files": 0,
      "closed": true,
      "auth_header_present": false,
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        0
      ],
      "caller_hash_matches": true,
      "valid": true
    },
    {
      "arm": "cold",
      "caller_estimate": 1000,
      "completed": true,
      "error_category": null,
      "pre_lease_sent": [
        {
          "initialize": 1,
          "initialized": 1,
          "skills/list": 0,
          "thread/start": 0,
          "turn/start": 0,
          "config/read": 0
        }
      ],
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "rollout_files": 0,
      "closed": true,
      "auth_header_present": false,
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        0
      ],
      "caller_hash_matches": true,
      "valid": true
    },
    {
      "arm": "cold",
      "caller_estimate": 2000,
      "completed": true,
      "error_category": null,
      "pre_lease_sent": [
        {
          "initialize": 1,
          "initialized": 1,
          "skills/list": 0,
          "thread/start": 0,
          "turn/start": 0,
          "config/read": 0
        }
      ],
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "rollout_files": 0,
      "closed": true,
      "auth_header_present": false,
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        0
      ],
      "caller_hash_matches": true,
      "valid": true
    },
    {
      "arm": "zh",
      "caller_estimate": 500,
      "completed": true,
      "error_category": null,
      "pre_lease_sent": [
        {
          "initialize": 1,
          "initialized": 1,
          "skills/list": 0,
          "thread/start": 0,
          "turn/start": 0,
          "config/read": 0
        }
      ],
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "rollout_files": 0,
      "closed": true,
      "auth_header_present": false,
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        0
      ],
      "caller_hash_matches": true,
      "valid": true
    },
    {
      "arm": "standard_decisions",
      "caller_estimate": null,
      "completed": true,
      "error_category": null,
      "pre_lease_sent": [
        {
          "initialize": 1,
          "initialized": 1,
          "skills/list": 0,
          "thread/start": 0,
          "turn/start": 0
        }
      ],
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "rollout_files": 0,
      "closed": true,
      "auth_header_present": false,
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        1
      ],
      "caller_hash_matches": null,
      "valid": true
    }
  ],
  "success": true
}
```

## native subscription, sequential calls

```json
{
  "real_cli_calls": 6,
  "bridge_inference_retries": 0,
  "raw_content_saved": false,
  "rows": [
    {
      "case": "en_500",
      "caller_estimate": 500,
      "profile": "codex-chat-minimal-v1",
      "valid": true,
      "usage": {
        "prompt_tokens": 506,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 6.2584,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "closed": true
    },
    {
      "case": "en_1000",
      "caller_estimate": 1000,
      "profile": "codex-chat-minimal-v1",
      "valid": true,
      "usage": {
        "prompt_tokens": 1006,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 4.3233,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "closed": true
    },
    {
      "case": "en_2000",
      "caller_estimate": 2000,
      "profile": "codex-chat-minimal-v1",
      "valid": true,
      "usage": {
        "prompt_tokens": 2006,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 5.0084,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "closed": true
    },
    {
      "case": "zh_500",
      "caller_estimate": 500,
      "profile": "codex-chat-minimal-v1",
      "valid": true,
      "usage": {
        "prompt_tokens": 506,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 6.8652,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "closed": true
    },
    {
      "case": "history",
      "caller_estimate": 14,
      "profile": "codex-chat-minimal-v1",
      "valid": true,
      "usage": {
        "prompt_tokens": 30,
        "completion_tokens": 19,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 11
        }
      },
      "seconds": 4.1157,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "closed": true
    },
    {
      "case": "untrusted",
      "caller_estimate": 31,
      "profile": "codex-chat-minimal-v1",
      "valid": true,
      "usage": {
        "prompt_tokens": 41,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 5.3398,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1,
        "config/read": 1
      },
      "closed": true
    }
  ],
  "success": true
}
```


## 公開HTTPS：同Key前4後6與清理修復

```json
{
  "raw_content_saved": false,
  "temporary_key_revoked": true,
  "same_key_across_update": true,
  "bridge_inference_retries": 0,
  "rows": [
    {
      "phase": "before",
      "installed_version": "0.9.11-mac.1",
      "provider": "codex",
      "kind": "chat",
      "request_id": "65bdc216-75cd-4348-930b-bf7d464cd028",
      "request_bytes": 2584,
      "request_sha256": "c963468f80a86f89e7d6009e222d619687c053ce962ae139d56decef0aaa2a50",
      "seconds": 9.9703,
      "model": "openai/gpt-6.1-sol",
      "usage": {
        "prompt_tokens": 3129,
        "completion_tokens": 6,
        "total_tokens": 3135,
        "cost": 0.006318,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "execution": {
        "warm_hits": 1,
        "cold_starts": 0
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "cost_usd": 0.006318
      }
    },
    {
      "phase": "before",
      "installed_version": "0.9.11-mac.1",
      "provider": "codex",
      "kind": "decisions",
      "request_id": "f11fc8a6-6884-462f-8ec0-b8bfe5b4bfd0",
      "request_bytes": 200,
      "request_sha256": "2e7fc62cc863c24b85e5074f80da29987b7b85d9a2047075a85f91deb4d5a5ea",
      "seconds": 11.6548,
      "model": "openai/gpt-6.1-sol",
      "usage": {
        "input_tokens": 2789,
        "output_tokens": 41,
        "cost": 0.005988
      },
      "execution": {
        "warm_hits": 1,
        "cold_starts": 0
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 23,
        "cost_usd": 0.005988
      }
    },
    {
      "phase": "before",
      "installed_version": "0.9.11-mac.1",
      "provider": "claude",
      "kind": "chat",
      "request_id": "1a31f317-77e1-4252-86a2-304f8de6a370",
      "request_bytes": 2592,
      "request_sha256": "655f30df5dc37fac5e7cc07abbf033c3b9532920fd8263d003ab084f0808b033",
      "seconds": 8.1055,
      "model": "anthropic/claude-haiku-4.5",
      "usage": {
        "prompt_tokens": 1060,
        "completion_tokens": 85,
        "total_tokens": 1145,
        "cost": 0.001485,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0
        }
      },
      "execution": {
        "warm_hits": 0,
        "cold_starts": 1
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": null,
        "cost_usd": 0.001485
      }
    },
    {
      "phase": "before",
      "installed_version": "0.9.11-mac.1",
      "provider": "claude",
      "kind": "decisions",
      "request_id": "13e81ddd-a549-411d-90ef-eb5a4771bb50",
      "request_bytes": 208,
      "request_sha256": "74f5b28647774bdaa3901e956d6fe8893957e1e4afbc72c24d3b810d9c8cb7c9",
      "seconds": 8.0527,
      "model": "anthropic/claude-haiku-4.5",
      "usage": {
        "input_tokens": 1546,
        "output_tokens": 358,
        "cost": 0.003336
      },
      "execution": {
        "warm_hits": 0,
        "cold_starts": 1
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": null,
        "cost_usd": 0.003336
      }
    },
    {
      "phase": "after",
      "installed_version": "0.9.12-mac.1",
      "provider": "codex",
      "kind": "chat",
      "request_id": "8eb11caa-54b7-4159-9604-2e2548fa94e9",
      "request_bytes": 2584,
      "request_sha256": "c963468f80a86f89e7d6009e222d619687c053ce962ae139d56decef0aaa2a50",
      "seconds": 9.1517,
      "model": "openai/gpt-6.1-sol",
      "usage": {
        "prompt_tokens": 506,
        "completion_tokens": 6,
        "total_tokens": 512,
        "cost": 0.001072,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "execution": {
        "warm_hits": 1,
        "cold_starts": 0,
        "inference_profile": "codex-chat-minimal-v1",
        "profile_reason": "verified"
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "cost_usd": 0.001072
      }
    },
    {
      "phase": "after",
      "installed_version": "0.9.12-mac.1",
      "provider": "codex",
      "kind": "decisions",
      "request_id": "53960eaa-5a75-4576-931e-059aa67906df",
      "request_bytes": 200,
      "request_sha256": "2e7fc62cc863c24b85e5074f80da29987b7b85d9a2047075a85f91deb4d5a5ea",
      "seconds": 6.9002,
      "model": "openai/gpt-6.1-sol",
      "usage": {
        "input_tokens": 2791,
        "output_tokens": 50,
        "cost": 0.006082
      },
      "execution": {
        "warm_hits": 1,
        "cold_starts": 0,
        "inference_profile": "standard",
        "profile_reason": "request_standard"
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 32,
        "cost_usd": 0.006082
      }
    },
    {
      "phase": "after",
      "installed_version": "0.9.12-mac.1",
      "provider": "claude",
      "kind": "chat",
      "request_id": "2915f49c-db76-464e-a536-62745ae42719",
      "request_bytes": 2592,
      "request_sha256": "655f30df5dc37fac5e7cc07abbf033c3b9532920fd8263d003ab084f0808b033",
      "seconds": 4.2366,
      "model": "anthropic/claude-haiku-4.5",
      "usage": {
        "prompt_tokens": 1062,
        "completion_tokens": 104,
        "total_tokens": 1166,
        "cost": 0.001582,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0
        }
      },
      "execution": {
        "warm_hits": 0,
        "cold_starts": 1,
        "inference_profile": "standard",
        "profile_reason": "provider_standard"
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": null,
        "cost_usd": 0.001582
      }
    },
    {
      "phase": "after",
      "installed_version": "0.9.12-mac.1",
      "provider": "claude",
      "kind": "decisions",
      "request_id": "005249b8-adf9-479b-9867-155b50753327",
      "request_bytes": 208,
      "request_sha256": "74f5b28647774bdaa3901e956d6fe8893957e1e4afbc72c24d3b810d9c8cb7c9",
      "seconds": 8.6464,
      "model": "anthropic/claude-haiku-4.5",
      "usage": {
        "input_tokens": 3674,
        "output_tokens": 711,
        "cost": 0.007229
      },
      "execution": {
        "warm_hits": 0,
        "cold_starts": 1,
        "inference_profile": "standard",
        "profile_reason": "provider_standard"
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": null,
        "cost_usd": 0.007229
      }
    },
    {
      "phase": "after",
      "installed_version": "0.9.12-mac.1",
      "provider": "codex",
      "kind": "schema",
      "request_id": "ed3f07a7-9535-46c1-8525-2275eb7c09e4",
      "request_bytes": 310,
      "request_sha256": "7293b1808f99b1e28fe5cf85b3b503c64664fc9c8cbd10a87faec515dd5eccc4",
      "seconds": 5.8373,
      "model": "openai/gpt-6.1-sol",
      "usage": {
        "prompt_tokens": 2658,
        "completion_tokens": 15,
        "total_tokens": 2673,
        "cost": 0.005466,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "execution": {
        "warm_hits": 1,
        "cold_starts": 0,
        "inference_profile": "standard",
        "profile_reason": "request_standard"
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "cost_usd": 0.005466
      }
    },
    {
      "phase": "after",
      "installed_version": "0.9.12-mac.1",
      "provider": "codex",
      "kind": "tool",
      "request_id": "9001ec0d-dc6a-4c53-8785-7c4f7f8d1eea",
      "request_bytes": 424,
      "request_sha256": "b02955007b940ce49f6bf5c3dcde69c4d61de9590d740c16ec7d431d363122e8",
      "seconds": 8.0454,
      "model": "openai/gpt-6.1-sol",
      "usage": {
        "prompt_tokens": 2869,
        "completion_tokens": 56,
        "total_tokens": 2925,
        "cost": 0.006298,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 21
        }
      },
      "execution": {
        "warm_hits": 1,
        "cold_starts": 0,
        "inference_profile": "standard",
        "profile_reason": "request_standard"
      },
      "billing_status": {
        "complete": true,
        "calls_started": 1,
        "calls_completed": 1
      },
      "valid": true,
      "local_metadata": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 21,
        "cost_usd": 0.006298
      }
    }
  ],
  "before_success": true,
  "after_success": true,
  "test_harness_cleanup_error": "Incorrect method name revoke_key; repaired using Store.revoke after all API calls",
  "cleanup_repaired": true,
  "active_owner_keys_preserved": true,
  "success": true
}
```

## 公開四附件匿名回讀

```json
{
  "success": true,
  "tag": "macos-source-v0.9.12-mac.1",
  "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
  "sha256": "87e07553a5f53bbbc57f7a1797a068cd8b37be9ed32f0e1abcdef0e360a664ba",
  "assets": [
    "aigo-llm-bridge-macos-source-0.9.12-mac.1.zip",
    "aigo-llm-bridge-macos-source-0.9.12-mac.1.zip.sha256",
    "macos-source-manifest.json",
    "macos-source-self-test.json"
  ],
  "anonymous_download": true,
  "authorization_header_used": false,
  "runtime_and_opt_in_tools_match_reviewed_source": true,
  "manifest_clean": true
}
```

## 從公開ZIP真安裝／互斥／關閉

```json
{
  "success": true,
  "public_zip": true,
  "original_version": "0.9.11-mac.1",
  "version": "0.9.12-mac.1",
  "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
  "download_installed": true,
  "fixed_machine_lock": true,
  "rejected_profile_no_database": true,
  "shutdown_api_closed": true,
  "max_concurrent_requests": 64,
  "credentials_or_power_changed": false,
  "original_restart_command_ok": true,
  "original_restored_healthy": true
}
```

## 原profile更新

```json
{
  "command_returncode": 0,
  "seconds": 1.4174,
  "updated": true,
  "previous_version": "0.9.11-mac.1",
  "version": "0.9.12-mac.1",
  "profile_preserved": true,
  "loaded": true,
  "source_commit_matches": true,
  "data_dir_preserved": true,
  "health_version": "0.9.12-mac.1",
  "accepting": true,
  "idle_profiles": {
    "codex-chat-minimal-v1": 1,
    "standard": 1
  },
  "resident": 2,
  "workers": 64,
  "pending": 64,
  "refill_failures": 0,
  "success": true
}
```

## 正式程序停止／重啟與資料保留

```json
{
  "version": "0.9.12-mac.1",
  "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
  "before_stop": {
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
      "idle": 2,
      "active": 0,
      "closing": 0,
      "quarantined": 0,
      "unavailable": false,
      "resident_target": 2,
      "total": 2,
      "limit": 64,
      "peak": 3,
      "created": 7,
      "warm_hits": 4,
      "cold_starts": 2,
      "refill_failures": 0,
      "paused": false,
      "waiting_leases": 0,
      "idle_profiles": {
        "codex-chat-minimal-v1": 1,
        "standard": 1
      }
    },
    "warm_supported_providers": [
      "codex"
    ]
  },
  "observed_owned_processes": 3,
  "observed_empty_cwds": 2,
  "stop_seconds": 0.6892,
  "owned_processes_remaining": 0,
  "old_cwds_remaining": 0,
  "restart_ok": true,
  "final_health": {
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
      "waiting_leases": 0,
      "idle_profiles": {
        "codex-chat-minimal-v1": 1,
        "standard": 1
      }
    },
    "warm_supported_providers": [
      "codex"
    ]
  },
  "other_settings_preserved": true,
  "all_prior_key_rows_preserved": true,
  "prior_key_rows": 58,
  "active_keys": 3,
  "effective_capacity": {
    "inference_resident": 2,
    "inference_workers": 64,
    "inference_pending": 64
  },
  "synthetic_requests": [
    {
      "protocol": "chat",
      "model": "anthropic/claude-haiku-4.5",
      "status": "completed",
      "prompt_tokens": 1060,
      "completion_tokens": 85,
      "cost_usd": 0.001485,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "chat",
      "model": "anthropic/claude-haiku-4.5",
      "status": "completed",
      "prompt_tokens": 1062,
      "completion_tokens": 104,
      "cost_usd": 0.001582,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "decisions",
      "model": "anthropic/claude-haiku-4.5",
      "status": "completed",
      "prompt_tokens": 1546,
      "completion_tokens": 358,
      "cost_usd": 0.003336,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "decisions",
      "model": "anthropic/claude-haiku-4.5",
      "status": "completed",
      "prompt_tokens": 3674,
      "completion_tokens": 711,
      "cost_usd": 0.007229,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "chat",
      "model": "openai/gpt-6.1-sol",
      "status": "completed",
      "prompt_tokens": 506,
      "completion_tokens": 6,
      "cost_usd": 0.001072,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "chat",
      "model": "openai/gpt-6.1-sol",
      "status": "completed",
      "prompt_tokens": 2658,
      "completion_tokens": 15,
      "cost_usd": 0.005466,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "decisions",
      "model": "openai/gpt-6.1-sol",
      "status": "completed",
      "prompt_tokens": 2789,
      "completion_tokens": 41,
      "cost_usd": 0.005988,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "decisions",
      "model": "openai/gpt-6.1-sol",
      "status": "completed",
      "prompt_tokens": 2791,
      "completion_tokens": 50,
      "cost_usd": 0.006082,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "chat",
      "model": "openai/gpt-6.1-sol",
      "status": "completed",
      "prompt_tokens": 2869,
      "completion_tokens": 56,
      "cost_usd": 0.006298,
      "calls_started": 1,
      "calls_completed": 1,
      "billing_complete": 1
    },
    {
      "protocol": "chat",
      "model": "openai/gpt-6.1-sol",
      "status": "completed",
      "prompt_tokens": 3129,
      "completion_tokens": 6,
      "cost_usd": 0.006318,
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
}
```

## 最終正式狀態

```json
{
  "installed_version": "0.9.12-mac.1",
  "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
  "health_version": "0.9.12-mac.1",
  "accepting": true,
  "resident": 2,
  "idle": 2,
  "idle_profiles": {
    "codex-chat-minimal-v1": 1,
    "standard": 1
  },
  "workers": 64,
  "pending": 64,
  "running": 0,
  "queued": 0,
  "refill_failures": 0,
  "pool_peak": 2,
  "pool_limit": 64,
  "installed_core_files": 50,
  "installed_public_reviewed_core_and_data_match": true,
  "native_cli_profile_gate": "verified",
  "profile_columns_present": true,
  "profile_path_preserved": true,
  "all_settings_preserved": true,
  "all_prior_key_rows_preserved": true,
  "key_rows": 59,
  "prior_key_rows": 58,
  "active_owner_keys": 3,
  "new_test_key_rows": 1,
  "new_test_keys_revoked": true,
  "personal_codex_config_preserved": true,
  "candidate_now_formal": true,
  "success": true
}
```

## 重新啟動後公開路由，非推論證據

```json
{
  "http_status": 200,
  "device_online": true,
  "worker_version": "0.9.4-relay",
  "not_inference_evidence": true
}
```
