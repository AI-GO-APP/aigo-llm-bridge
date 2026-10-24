# 一般 LLM 結構性研究 metadata

2026-10-24。Refs #46；只含合成測試 allowlist metadata，原始內容／事件／憑證不落檔。解讀與限制見 [QA](../qa/2026-10-24-macos-llm-structural-context.md)。正式 0.9.11 未變更。

## Codex 真訂閱小量對照

```json
{
  "schema": 1,
  "transport": "direct native subscribed CLI, no proxy or public API",
  "cli_version": "0.163.0-alpha.11",
  "production_changed": false,
  "decisions_changed": false,
  "concurrent_calls": 1,
  "inference_retries": 0,
  "caller_estimator": "o200k_base; not an actual OpenRouter receipt",
  "rows": [
    {
      "arm": "current",
      "case": "short",
      "caller_estimated_tokens": 5,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 2634,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 4.2372
    },
    {
      "arm": "pure_chat",
      "case": "short",
      "caller_estimated_tokens": 5,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 52,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 4.5095
    },
    {
      "arm": "current",
      "case": "caller_500",
      "caller_estimated_tokens": 500,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 3127,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 3.8583
    },
    {
      "arm": "pure_chat",
      "case": "caller_500",
      "caller_estimated_tokens": 500,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 547,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 3.8434
    },
    {
      "arm": "pure_chat",
      "case": "history",
      "caller_estimated_tokens": 14,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 71,
        "completion_tokens": 18,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 10
        }
      },
      "seconds": 4.3406
    },
    {
      "arm": "pure_chat",
      "case": "untrusted_data",
      "caller_estimated_tokens": 32,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 79,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 3.6221
    }
  ],
  "raw_content_or_credentials_saved": false,
  "settings_preserved": true,
  "all_key_rows_preserved": true,
  "personal_config_preserved": true,
  "success": true
}
```

## Codex initialize-only／caller schema

```json
{
  "concurrent_calls": 1,
  "real_inference_calls": 2,
  "inference_retries": 0,
  "production_changed": false,
  "decisions_changed": false,
  "rows": [
    {
      "case": "initialized_single_use",
      "before_lease_sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 0,
        "thread/start": 0,
        "turn/start": 0
      },
      "valid": true,
      "usage": {
        "prompt_tokens": 547,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 3.026,
      "closed": true,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      }
    },
    {
      "case": "caller_json_schema",
      "before_lease_sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 0,
        "thread/start": 0,
        "turn/start": 0
      },
      "valid": true,
      "usage": {
        "prompt_tokens": 80,
        "completion_tokens": 15,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 7.3208,
      "closed": true,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      }
    }
  ],
  "success": true
}
```

## Claude 真訂閱小量對照

```json
{
  "schema": 1,
  "transport": "direct native subscribed CLI",
  "cli_version": "2.1.306",
  "production_changed": false,
  "decisions_changed": false,
  "concurrent_calls": 1,
  "inference_retries": 0,
  "caller_estimator": "o200k_base, not Claude tokenizer or OpenRouter receipt",
  "raw_content_or_credentials_saved": false,
  "rows": [
    {
      "arm": "current",
      "case": "short",
      "caller_estimated_tokens": 5,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 565,
        "completion_tokens": 70,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "cache_write_1h_tokens": 0
        }
      },
      "seconds": 1.7519,
      "owned_processes_closed": true
    },
    {
      "arm": "minimal_text",
      "case": "short",
      "caller_estimated_tokens": 5,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 527,
        "completion_tokens": 47,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "cache_write_1h_tokens": 0
        }
      },
      "seconds": 1.4555,
      "owned_processes_closed": true
    },
    {
      "arm": "current",
      "case": "caller_500",
      "caller_estimated_tokens": 500,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 1061,
        "completion_tokens": 104,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "cache_write_1h_tokens": 0
        }
      },
      "seconds": 1.9602,
      "owned_processes_closed": true
    },
    {
      "arm": "minimal_text",
      "case": "caller_500",
      "caller_estimated_tokens": 500,
      "completed": true,
      "valid": true,
      "usage": {
        "prompt_tokens": 1022,
        "completion_tokens": 77,
        "prompt_tokens_details": {
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "cache_write_1h_tokens": 0
        }
      },
      "seconds": 1.7963,
      "owned_processes_closed": true
    }
  ],
  "settings_preserved": true,
  "all_key_rows_preserved": true,
  "success": true
}
```

## 500 caller wire 完整性，credential-free mock

```json
{
  "success": true,
  "real_inference_calls": 0,
  "raw_content_saved": false,
  "rows": [
    {
      "arm": "current",
      "completed": true,
      "caller_blocks": 1,
      "caller_metadata": [
        {
          "characters": 2497,
          "utf8_bytes": 2497,
          "o200k_estimate": 500,
          "sha256": "42d278f79ca7749939bc2648c9ef2cb44a28087355a42ec5b58800197cc7efc3"
        }
      ],
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        1
      ],
      "authorization_header_present": false,
      "session_closed": true,
      "rollout_files": 0
    },
    {
      "arm": "pure_chat",
      "completed": true,
      "caller_blocks": 1,
      "caller_metadata": [
        {
          "characters": 2497,
          "utf8_bytes": 2497,
          "o200k_estimate": 500,
          "sha256": "42d278f79ca7749939bc2648c9ef2cb44a28087355a42ec5b58800197cc7efc3"
        }
      ],
      "tools_count": [
        0
      ],
      "additional_tools_count": [
        0
      ],
      "authorization_header_present": false,
      "session_closed": true,
      "rollout_files": 0
    }
  ]
}
```

## 正式安裝唯讀覆核

prior_release_test_key_rows 為前輪 0.9.11 發布建立且已撤銷的兩筆；本輪沒有建立 API Key。

```json
{
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
  "personal_codex_config_preserved": true,
  "cli_versions": {
    "codex": "0.163.0-alpha.11",
    "claude": "2.1.306"
  },
  "research_candidate_persisted": false,
  "success": true,
  "prior_release_test_key_rows": 2,
  "prior_release_test_keys_revoked": true,
  "new_test_key_rows_this_research": 0
}
```

## Codex caller-only：移除 Bridge 固定提示，保留 caller 原文

首段模型工具／context 已清空；本段只移除固定 Bridge base/developer 前綴，保持 caller system／歷史及實際隔離限制。

```json
{
  "candidate": "caller-only; zero Bridge fixed prompt; native subscription auth",
  "production_changed": false,
  "decisions_changed": false,
  "inference_retries": 0,
  "raw_content_saved": false,
  "mock_calls": 1,
  "rows": [
    {
      "case": "short",
      "caller_estimated_tokens": 5,
      "valid": true,
      "completed": true,
      "usage": {
        "prompt_tokens": 11,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 3.609
    },
    {
      "case": "caller_500",
      "caller_estimated_tokens": 500,
      "valid": true,
      "completed": true,
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
      "seconds": 3.7786
    },
    {
      "case": "untrusted_data",
      "caller_estimated_tokens": 32,
      "valid": true,
      "completed": true,
      "usage": {
        "prompt_tokens": 42,
        "completion_tokens": 6,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 0
        }
      },
      "seconds": 3.4978
    },
    {
      "case": "history",
      "caller_estimated_tokens": 14,
      "valid": true,
      "completed": true,
      "usage": {
        "prompt_tokens": 30,
        "completion_tokens": 20,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 12
        }
      },
      "seconds": 3.6789
    }
  ],
  "mock": {
    "completed": true,
    "session_closed": true,
    "rollout_files": 0,
    "tools_count": [
      0
    ],
    "additional_tools_count": [
      0
    ],
    "caller": [
      {
        "role": "user",
        "kind": "caller",
        "characters": 2497,
        "utf8_bytes": 2497,
        "o200k_estimate": 500,
        "sha256": "42d278f79ca7749939bc2648c9ef2cb44a28087355a42ec5b58800197cc7efc3",
        "parts": [
          {
            "category": "remainder",
            "characters": 2497,
            "utf8_bytes": 2497,
            "o200k_estimate": 500,
            "sha256": "42d278f79ca7749939bc2648c9ef2cb44a28087355a42ec5b58800197cc7efc3"
          }
        ]
      }
    ],
    "fields": [
      {
        "input": {
          "characters": 2623,
          "utf8_bytes": 2623,
          "o200k_estimate": 549,
          "sha256": "2d80ead94918d8458110e2ce4883c5233e45c608ba207a2f4455d38f7f15b201"
        },
        "text": {
          "characters": 19,
          "utf8_bytes": 19,
          "o200k_estimate": 5,
          "sha256": "ea2f7b2aec9b8322dfc4147fc30009def7ae33633895485ca85dadbcde2e0eef"
        }
      }
    ]
  },
  "real_inference_calls": 4,
  "success": true
}
```
