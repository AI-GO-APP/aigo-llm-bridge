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
