# Mac optimization probe metadata

2026-10-24。固定allowlist metadata；[結果及限制](../qa/2026-10-24-macos-optimization-probes.md)。不含原始request／response／事件／Key。

```json
{
  "experiment": "Mac optimization research; no production deployment",
  "source_version": "0.9.12-mac.1",
  "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
  "cli_version": "2.1.306 (Claude Code)",
  "production_modified": false,
  "raw_content_saved": false,
  "native_cli_calls": 24,
  "input_tokens": 36948,
  "output_tokens": 13485,
  "native_first_12": {
    "source_version": "0.9.12-mac.1",
    "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
    "raw_events_saved": false,
    "automatic_inference_retries": 0,
    "production_modified": false,
    "structured_output_unchanged": true,
    "thinking_unchanged": true,
    "rows": [
      {
        "pair": 0,
        "kind": "noul",
        "arm": "baseline",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 936,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1547,
              "output_tokens": 1,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1547,
          "output_tokens": 628,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 5992,
        "native_duration_api_ms": 5973,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1547,
          "output_tokens": 1,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1547,
          "completion_tokens": 628,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 6.3407,
        "execution": {
          "provider_setup_ms": 123,
          "cli_spawn_ms": 2,
          "inference_ms": 6214,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 0,
        "kind": "noul",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 713,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1488,
              "output_tokens": 6,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1488,
          "output_tokens": 642,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 6266,
        "native_duration_api_ms": 6245,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1488,
          "output_tokens": 6,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1488,
          "completion_tokens": 642,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 6.6952,
        "execution": {
          "provider_setup_ms": 186,
          "cli_spawn_ms": 2,
          "inference_ms": 6505,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 1,
        "kind": "choice",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "63e3b8a4471461db3ff0ebb97ce26aae195f840707c32ffb2568d5ae4ae3ee8f",
        "original_stdin_bytes": 1120,
        "effective_stdin_bytes": 828,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1543,
              "output_tokens": 4,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 1,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1543,
          "output_tokens": 576,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 5349,
        "native_duration_api_ms": 5327,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1543,
          "output_tokens": 4,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1543,
          "completion_tokens": 576,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 5.77,
        "execution": {
          "provider_setup_ms": 182,
          "cli_spawn_ms": 2,
          "inference_ms": 5585,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 1,
        "kind": "choice",
        "arm": "baseline",
        "caller_payload_sha256": "63e3b8a4471461db3ff0ebb97ce26aae195f840707c32ffb2568d5ae4ae3ee8f",
        "original_stdin_bytes": 1120,
        "effective_stdin_bytes": 1120,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1620,
              "output_tokens": 3,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1620,
          "output_tokens": 828,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 7413,
        "native_duration_api_ms": 7393,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1620,
          "output_tokens": 3,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1620,
          "completion_tokens": 828,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 7.84,
        "execution": {
          "provider_setup_ms": 177,
          "cli_spawn_ms": 2,
          "inference_ms": 7659,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 2,
        "kind": "score",
        "arm": "baseline",
        "caller_payload_sha256": "fbc2b472d186071638847284eb5077bc15744dcfe40475384676930c6a9bd305",
        "original_stdin_bytes": 1037,
        "effective_stdin_bytes": 1037,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1596,
              "output_tokens": 4,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1596,
          "output_tokens": 536,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 4701,
        "native_duration_api_ms": 4680,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1596,
          "output_tokens": 4,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1596,
          "completion_tokens": 536,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 5.0362,
        "execution": {
          "provider_setup_ms": 123,
          "cli_spawn_ms": 2,
          "inference_ms": 4910,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 2,
        "kind": "score",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "fbc2b472d186071638847284eb5077bc15744dcfe40475384676930c6a9bd305",
        "original_stdin_bytes": 1037,
        "effective_stdin_bytes": 745,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1520,
              "output_tokens": 1,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 1,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1520,
          "output_tokens": 781,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 6772,
        "native_duration_api_ms": 6751,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1520,
          "output_tokens": 1,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1520,
          "completion_tokens": 781,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 7.1821,
        "execution": {
          "provider_setup_ms": 185,
          "cli_spawn_ms": 3,
          "inference_ms": 6993,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 3,
        "kind": "noul",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 713,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1486,
              "output_tokens": 1,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1486,
          "output_tokens": 510,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 4490,
        "native_duration_api_ms": 4468,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1486,
          "output_tokens": 1,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1486,
          "completion_tokens": 510,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 4.8815,
        "execution": {
          "provider_setup_ms": 186,
          "cli_spawn_ms": 3,
          "inference_ms": 4692,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 3,
        "kind": "noul",
        "arm": "baseline",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 936,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1546,
              "output_tokens": 1,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1546,
          "output_tokens": 302,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 3045,
        "native_duration_api_ms": 3025,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1546,
          "output_tokens": 1,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1546,
          "completion_tokens": 302,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 3.441,
        "execution": {
          "provider_setup_ms": 176,
          "cli_spawn_ms": 2,
          "inference_ms": 3261,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 4,
        "kind": "choice",
        "arm": "baseline",
        "caller_payload_sha256": "63e3b8a4471461db3ff0ebb97ce26aae195f840707c32ffb2568d5ae4ae3ee8f",
        "original_stdin_bytes": 1120,
        "effective_stdin_bytes": 1120,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1622,
              "output_tokens": 6,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 1,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1622,
          "output_tokens": 742,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 6456,
        "native_duration_api_ms": 6435,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1622,
          "output_tokens": 6,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1622,
          "completion_tokens": 742,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 6.8412,
        "execution": {
          "provider_setup_ms": 185,
          "cli_spawn_ms": 3,
          "inference_ms": 6653,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 4,
        "kind": "choice",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "63e3b8a4471461db3ff0ebb97ce26aae195f840707c32ffb2568d5ae4ae3ee8f",
        "original_stdin_bytes": 1120,
        "effective_stdin_bytes": 828,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1546,
              "output_tokens": 5,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1546,
          "output_tokens": 499,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 4253,
        "native_duration_api_ms": 4233,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1546,
          "output_tokens": 5,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1546,
          "completion_tokens": 499,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 4.6235,
        "execution": {
          "provider_setup_ms": 185,
          "cli_spawn_ms": 2,
          "inference_ms": 4436,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 5,
        "kind": "score",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "fbc2b472d186071638847284eb5077bc15744dcfe40475384676930c6a9bd305",
        "original_stdin_bytes": 1037,
        "effective_stdin_bytes": 745,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1519,
              "output_tokens": 6,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1519,
          "output_tokens": 496,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 4238,
        "native_duration_api_ms": 4218,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1519,
          "output_tokens": 6,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1519,
          "completion_tokens": 496,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 4.6399,
        "execution": {
          "provider_setup_ms": 184,
          "cli_spawn_ms": 3,
          "inference_ms": 4453,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 5,
        "kind": "score",
        "arm": "baseline",
        "caller_payload_sha256": "fbc2b472d186071638847284eb5077bc15744dcfe40475384676930c6a9bd305",
        "original_stdin_bytes": 1037,
        "effective_stdin_bytes": 1037,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1594,
              "output_tokens": 6,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1594,
          "output_tokens": 712,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 5974,
        "native_duration_api_ms": 5953,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1594,
          "output_tokens": 6,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1594,
          "completion_tokens": 712,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 6.3816,
        "execution": {
          "provider_setup_ms": 183,
          "cli_spawn_ms": 2,
          "inference_ms": 6195,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      }
    ],
    "success": true,
    "cli_calls": 12,
    "input_tokens": 18627,
    "output_tokens": 7252
  },
  "native_partial_8": {
    "source_version": "0.9.12-mac.1",
    "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
    "raw_events_saved": false,
    "automatic_inference_retries": 0,
    "production_modified": false,
    "structured_output_unchanged": true,
    "thinking_unchanged": true,
    "rows": [
      {
        "pair": 0,
        "kind": "noul",
        "arm": "baseline",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 936,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1547,
              "output_tokens": 425,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1547,
          "output_tokens": 425,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1547,
              "output_tokens": 1,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1547,
          "output_tokens": 425,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 4525,
        "native_duration_api_ms": 4505,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1547,
          "output_tokens": 1,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1547,
          "completion_tokens": 425,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 4.8855,
        "execution": {
          "provider_setup_ms": 120,
          "cli_spawn_ms": 2,
          "inference_ms": 4761,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 0,
        "kind": "noul",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 713,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1487,
              "output_tokens": 524,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "text",
              "2": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1487,
          "output_tokens": 524,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1487,
              "output_tokens": 1,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 1,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1487,
          "output_tokens": 524,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 4505,
        "native_duration_api_ms": 4485,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1487,
          "output_tokens": 1,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1487,
          "completion_tokens": 524,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 4.9021,
        "execution": {
          "provider_setup_ms": 183,
          "cli_spawn_ms": 3,
          "inference_ms": 4715,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 1,
        "kind": "noul",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 713,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1487,
              "output_tokens": 320,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1487,
          "output_tokens": 320,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1487,
              "output_tokens": 1,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1487,
          "output_tokens": 320,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 3048,
        "native_duration_api_ms": 3027,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1487,
          "output_tokens": 1,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1487,
          "completion_tokens": 320,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 3.4832,
        "execution": {
          "provider_setup_ms": 179,
          "cli_spawn_ms": 2,
          "inference_ms": 3301,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 1,
        "kind": "noul",
        "arm": "baseline",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 936,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1546,
              "output_tokens": 349,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1546,
          "output_tokens": 349,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1546,
              "output_tokens": 5,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1546,
          "output_tokens": 349,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 3272,
        "native_duration_api_ms": 3252,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1546,
          "output_tokens": 5,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1546,
          "completion_tokens": 349,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 3.646,
        "execution": {
          "provider_setup_ms": 177,
          "cli_spawn_ms": 2,
          "inference_ms": 3465,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 2,
        "kind": "noul",
        "arm": "baseline",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 936,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1545,
              "output_tokens": 465,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1545,
          "output_tokens": 465,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1545,
              "output_tokens": 6,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1545,
          "output_tokens": 465,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 3855,
        "native_duration_api_ms": 3835,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1545,
          "output_tokens": 6,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1545,
          "completion_tokens": 465,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 4.2259,
        "execution": {
          "provider_setup_ms": 126,
          "cli_spawn_ms": 2,
          "inference_ms": 4097,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 2,
        "kind": "noul",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 713,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1488,
              "output_tokens": 723,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "text",
              "2": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1488,
          "output_tokens": 723,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1488,
              "output_tokens": 5,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 1,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1488,
          "output_tokens": 723,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 6493,
        "native_duration_api_ms": 6474,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1488,
          "output_tokens": 5,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1488,
          "completion_tokens": 723,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 6.8823,
        "execution": {
          "provider_setup_ms": 188,
          "cli_spawn_ms": 2,
          "inference_ms": 6690,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 3,
        "kind": "noul",
        "arm": "deduplicate_schema",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 713,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1487,
              "output_tokens": 1090,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "text",
              "2": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1487,
          "output_tokens": 1090,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1487,
              "output_tokens": 3,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 1,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1487,
          "output_tokens": 1090,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 9656,
        "native_duration_api_ms": 9635,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1487,
          "output_tokens": 3,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1487,
          "completion_tokens": 1090,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 10.0567,
        "execution": {
          "provider_setup_ms": 181,
          "cli_spawn_ms": 2,
          "inference_ms": 9872,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      },
      {
        "pair": 3,
        "kind": "noul",
        "arm": "baseline",
        "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
        "original_stdin_bytes": 936,
        "effective_stdin_bytes": 936,
        "stream_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1547,
              "output_tokens": 381,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "block_types": {
              "0": "thinking",
              "1": "structured_output"
            },
            "stop_reason": "tool_use"
          }
        ],
        "stream_usage_sum": {
          "input_tokens": 1547,
          "output_tokens": 381,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_api_retries": [],
        "partial_messages_enabled": true,
        "assistant_messages": [
          {
            "index": 0,
            "usage": {
              "input_tokens": 1547,
              "output_tokens": 6,
              "cache_read_input_tokens": 0,
              "cache_creation_input_tokens": 0
            },
            "blocks": {
              "text": 0,
              "thinking": 1,
              "structured_output": 1,
              "other_tools": 0,
              "other_blocks": 0
            }
          }
        ],
        "unique_assistant_messages": 1,
        "native_result_usage": {
          "input_tokens": 1547,
          "output_tokens": 381,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "native_num_turns": 2,
        "native_duration_ms": 3484,
        "native_duration_api_ms": 3465,
        "has_structured_output": true,
        "unique_assistant_usage_sum": {
          "input_tokens": 1547,
          "output_tokens": 6,
          "cache_read_input_tokens": 0,
          "cache_creation_input_tokens": 0
        },
        "other_tool_uses": 0,
        "valid": true,
        "usage": {
          "prompt_tokens": 1547,
          "completion_tokens": 381,
          "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "cache_write_1h_tokens": 0
          }
        },
        "seconds": 3.8923,
        "execution": {
          "provider_setup_ms": 176,
          "cli_spawn_ms": 3,
          "inference_ms": 3712,
          "warm_hits": 0,
          "cold_starts": 0,
          "inference_profile": "standard",
          "profile_reason": "provider_standard"
        }
      }
    ],
    "success": true,
    "cli_calls": 8,
    "input_tokens": 12134,
    "output_tokens": 4277
  },
  "native_concurrent_4": [
    {
      "source_version": "0.9.12-mac.1",
      "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
      "raw_events_saved": false,
      "automatic_inference_retries": 0,
      "production_modified": false,
      "structured_output_unchanged": true,
      "thinking_unchanged": true,
      "rows": [
        {
          "pair": 0,
          "kind": "noul",
          "arm": "baseline",
          "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
          "original_stdin_bytes": 936,
          "effective_stdin_bytes": 936,
          "stream_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1546,
                "output_tokens": 715,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "block_types": {
                "0": "thinking",
                "1": "structured_output"
              },
              "stop_reason": "tool_use"
            }
          ],
          "stream_usage_sum": {
            "input_tokens": 1546,
            "output_tokens": 715,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_api_retries": [],
          "partial_messages_enabled": true,
          "assistant_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1546,
                "output_tokens": 6,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "blocks": {
                "text": 0,
                "thinking": 1,
                "structured_output": 1,
                "other_tools": 0,
                "other_blocks": 0
              }
            }
          ],
          "unique_assistant_messages": 1,
          "native_result_usage": {
            "input_tokens": 1546,
            "output_tokens": 715,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_num_turns": 2,
          "native_duration_ms": 6963,
          "native_duration_api_ms": 6936,
          "has_structured_output": true,
          "unique_assistant_usage_sum": {
            "input_tokens": 1546,
            "output_tokens": 6,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "other_tool_uses": 0,
          "valid": true,
          "usage": {
            "prompt_tokens": 1546,
            "completion_tokens": 715,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 7.4228,
          "execution": {
            "provider_setup_ms": 184,
            "cli_spawn_ms": 1,
            "inference_ms": 7236,
            "warm_hits": 0,
            "cold_starts": 0,
            "inference_profile": "standard",
            "profile_reason": "provider_standard"
          }
        }
      ],
      "success": true,
      "cli_calls": 1,
      "input_tokens": 1546,
      "output_tokens": 715
    },
    {
      "source_version": "0.9.12-mac.1",
      "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
      "raw_events_saved": false,
      "automatic_inference_retries": 0,
      "production_modified": false,
      "structured_output_unchanged": true,
      "thinking_unchanged": true,
      "rows": [
        {
          "pair": 0,
          "kind": "noul",
          "arm": "baseline",
          "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
          "original_stdin_bytes": 936,
          "effective_stdin_bytes": 936,
          "stream_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1547,
                "output_tokens": 472,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "block_types": {
                "0": "thinking",
                "1": "structured_output"
              },
              "stop_reason": "tool_use"
            }
          ],
          "stream_usage_sum": {
            "input_tokens": 1547,
            "output_tokens": 472,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_api_retries": [],
          "partial_messages_enabled": true,
          "assistant_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1547,
                "output_tokens": 6,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "blocks": {
                "text": 0,
                "thinking": 1,
                "structured_output": 1,
                "other_tools": 0,
                "other_blocks": 0
              }
            }
          ],
          "unique_assistant_messages": 1,
          "native_result_usage": {
            "input_tokens": 1547,
            "output_tokens": 472,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_num_turns": 2,
          "native_duration_ms": 4102,
          "native_duration_api_ms": 4076,
          "has_structured_output": true,
          "unique_assistant_usage_sum": {
            "input_tokens": 1547,
            "output_tokens": 6,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "other_tool_uses": 0,
          "valid": true,
          "usage": {
            "prompt_tokens": 1547,
            "completion_tokens": 472,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 4.5354,
          "execution": {
            "provider_setup_ms": 174,
            "cli_spawn_ms": 2,
            "inference_ms": 4357,
            "warm_hits": 0,
            "cold_starts": 0,
            "inference_profile": "standard",
            "profile_reason": "provider_standard"
          }
        }
      ],
      "success": true,
      "cli_calls": 1,
      "input_tokens": 1547,
      "output_tokens": 472
    },
    {
      "source_version": "0.9.12-mac.1",
      "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
      "raw_events_saved": false,
      "automatic_inference_retries": 0,
      "production_modified": false,
      "structured_output_unchanged": true,
      "thinking_unchanged": true,
      "rows": [
        {
          "pair": 0,
          "kind": "noul",
          "arm": "baseline",
          "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
          "original_stdin_bytes": 936,
          "effective_stdin_bytes": 936,
          "stream_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1546,
                "output_tokens": 306,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "block_types": {
                "0": "thinking",
                "1": "structured_output"
              },
              "stop_reason": "tool_use"
            }
          ],
          "stream_usage_sum": {
            "input_tokens": 1546,
            "output_tokens": 306,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_api_retries": [],
          "partial_messages_enabled": true,
          "assistant_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1546,
                "output_tokens": 6,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "blocks": {
                "text": 0,
                "thinking": 1,
                "structured_output": 1,
                "other_tools": 0,
                "other_blocks": 0
              }
            }
          ],
          "unique_assistant_messages": 1,
          "native_result_usage": {
            "input_tokens": 1546,
            "output_tokens": 306,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_num_turns": 2,
          "native_duration_ms": 2972,
          "native_duration_api_ms": 2948,
          "has_structured_output": true,
          "unique_assistant_usage_sum": {
            "input_tokens": 1546,
            "output_tokens": 6,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "other_tool_uses": 0,
          "valid": true,
          "usage": {
            "prompt_tokens": 1546,
            "completion_tokens": 306,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 3.3768,
          "execution": {
            "provider_setup_ms": 182,
            "cli_spawn_ms": 1,
            "inference_ms": 3191,
            "warm_hits": 0,
            "cold_starts": 0,
            "inference_profile": "standard",
            "profile_reason": "provider_standard"
          }
        }
      ],
      "success": true,
      "cli_calls": 1,
      "input_tokens": 1546,
      "output_tokens": 306
    },
    {
      "source_version": "0.9.12-mac.1",
      "source_commit": "fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12",
      "raw_events_saved": false,
      "automatic_inference_retries": 0,
      "production_modified": false,
      "structured_output_unchanged": true,
      "thinking_unchanged": true,
      "rows": [
        {
          "pair": 0,
          "kind": "noul",
          "arm": "baseline",
          "caller_payload_sha256": "0bfccc31ecd86c50c5f93bb200101ece8f0735f935151f2e7402738a452ffd59",
          "original_stdin_bytes": 936,
          "effective_stdin_bytes": 936,
          "stream_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1548,
                "output_tokens": 463,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "block_types": {
                "0": "thinking",
                "1": "structured_output"
              },
              "stop_reason": "tool_use"
            }
          ],
          "stream_usage_sum": {
            "input_tokens": 1548,
            "output_tokens": 463,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_api_retries": [],
          "partial_messages_enabled": true,
          "assistant_messages": [
            {
              "index": 0,
              "usage": {
                "input_tokens": 1548,
                "output_tokens": 1,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
              },
              "blocks": {
                "text": 0,
                "thinking": 1,
                "structured_output": 1,
                "other_tools": 0,
                "other_blocks": 0
              }
            }
          ],
          "unique_assistant_messages": 1,
          "native_result_usage": {
            "input_tokens": 1548,
            "output_tokens": 463,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "native_num_turns": 2,
          "native_duration_ms": 4393,
          "native_duration_api_ms": 4360,
          "has_structured_output": true,
          "unique_assistant_usage_sum": {
            "input_tokens": 1548,
            "output_tokens": 1,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0
          },
          "other_tool_uses": 0,
          "valid": true,
          "usage": {
            "prompt_tokens": 1548,
            "completion_tokens": 463,
            "prompt_tokens_details": {
              "cached_tokens": 0,
              "cache_write_tokens": 0,
              "cache_write_1h_tokens": 0
            }
          },
          "seconds": 4.839,
          "execution": {
            "provider_setup_ms": 183,
            "cli_spawn_ms": 1,
            "inference_ms": 4653,
            "warm_hits": 0,
            "cold_starts": 0,
            "inference_profile": "standard",
            "profile_reason": "provider_standard"
          }
        }
      ],
      "success": true,
      "cli_calls": 1,
      "input_tokens": 1548,
      "output_tokens": 463
    }
  ],
  "public_health_only": {
    "request_path": "/health",
    "model_inference_calls": 0,
    "authorization_used": false,
    "production_changed": false,
    "rows": [
      {
        "arm": "fresh",
        "index": 0,
        "status": 200,
        "seconds": 0.6606,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 0,
        "status": 200,
        "seconds": 0.5836,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 1,
        "status": 200,
        "seconds": 0.2851,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "fresh",
        "index": 1,
        "status": 200,
        "seconds": 0.4195,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "fresh",
        "index": 2,
        "status": 200,
        "seconds": 1.4656,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 2,
        "status": 200,
        "seconds": 0.2567,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 3,
        "status": 200,
        "seconds": 0.5865,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "fresh",
        "index": 3,
        "status": 200,
        "seconds": 1.1557,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "fresh",
        "index": 4,
        "status": 200,
        "seconds": 0.452,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 4,
        "status": 200,
        "seconds": 0.3369,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 5,
        "status": 200,
        "seconds": 0.2821,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "fresh",
        "index": 5,
        "status": 200,
        "seconds": 2.438,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "fresh",
        "index": 6,
        "status": 200,
        "seconds": 0.4226,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 6,
        "status": 200,
        "seconds": 0.3377,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "persistent",
        "index": 7,
        "status": 200,
        "seconds": 0.3071,
        "same_live_socket": true,
        "will_close": false,
        "device_online": true,
        "valid": true
      },
      {
        "arm": "fresh",
        "index": 7,
        "status": 200,
        "seconds": 1.7061,
        "same_live_socket": false,
        "will_close": false,
        "device_online": true,
        "valid": true
      }
    ],
    "pairs": 8,
    "raw_content_saved": false,
    "primer": {
      "arm": "persistent_primer",
      "index": -1,
      "status": 200,
      "seconds": 0.4179,
      "same_live_socket": false,
      "will_close": false,
      "device_online": true,
      "valid": true
    },
    "summary": {
      "fresh": {
        "requests": 8,
        "correct": 8,
        "median_seconds": 0.9082,
        "max_seconds": 2.438,
        "total_seconds": 8.7201,
        "same_live_socket_count": 0
      },
      "persistent": {
        "requests": 8,
        "correct": 8,
        "median_seconds": 0.322,
        "max_seconds": 0.5865,
        "total_seconds": 2.9757,
        "same_live_socket_count": 8
      }
    },
    "persistent_total_including_primer_seconds": 3.3936,
    "success": true
  },
  "batch_simulation_only": {
    "experiment": "buffered burst transport; actual Worker state machine, imposed RTT",
    "production_changed": false,
    "real_network": false,
    "model_inference_calls": 0,
    "raw_content_saved": false,
    "rows": [
      {
        "arm": "single",
        "count": 16,
        "rtt_ms": 100,
        "round": 1,
        "polls": 16,
        "maximum_batch": 1,
        "delivered_once": 16,
        "dispatch_p50_ms": 845.264,
        "dispatch_p95_ms": 1688.198,
        "dispatch_max_ms": 1688.198
      },
      {
        "arm": "batch8",
        "count": 16,
        "rtt_ms": 100,
        "round": 1,
        "polls": 2,
        "maximum_batch": 8,
        "delivered_once": 16,
        "dispatch_p50_ms": 109.294,
        "dispatch_p95_ms": 215.447,
        "dispatch_max_ms": 215.447
      },
      {
        "arm": "batch8",
        "count": 16,
        "rtt_ms": 100,
        "round": 2,
        "polls": 2,
        "maximum_batch": 8,
        "delivered_once": 16,
        "dispatch_p50_ms": 107.55,
        "dispatch_p95_ms": 215.48,
        "dispatch_max_ms": 215.48
      },
      {
        "arm": "single",
        "count": 16,
        "rtt_ms": 100,
        "round": 2,
        "polls": 16,
        "maximum_batch": 1,
        "delivered_once": 16,
        "dispatch_p50_ms": 842.27,
        "dispatch_p95_ms": 1683.562,
        "dispatch_max_ms": 1683.562
      },
      {
        "arm": "single",
        "count": 16,
        "rtt_ms": 100,
        "round": 3,
        "polls": 16,
        "maximum_batch": 1,
        "delivered_once": 16,
        "dispatch_p50_ms": 837.413,
        "dispatch_p95_ms": 1682.716,
        "dispatch_max_ms": 1682.716
      },
      {
        "arm": "batch8",
        "count": 16,
        "rtt_ms": 100,
        "round": 3,
        "polls": 2,
        "maximum_batch": 8,
        "delivered_once": 16,
        "dispatch_p50_ms": 105.883,
        "dispatch_p95_ms": 214.468,
        "dispatch_max_ms": 214.468
      },
      {
        "arm": "single",
        "count": 64,
        "rtt_ms": 100,
        "round": 1,
        "polls": 64,
        "maximum_batch": 1,
        "delivered_once": 64,
        "dispatch_p50_ms": 3363.047,
        "dispatch_p95_ms": 6411.916,
        "dispatch_max_ms": 6726.231
      },
      {
        "arm": "batch8",
        "count": 64,
        "rtt_ms": 100,
        "round": 1,
        "polls": 8,
        "maximum_batch": 8,
        "delivered_once": 64,
        "dispatch_p50_ms": 427.981,
        "dispatch_p95_ms": 854.951,
        "dispatch_max_ms": 855.558
      },
      {
        "arm": "batch8",
        "count": 64,
        "rtt_ms": 100,
        "round": 2,
        "polls": 8,
        "maximum_batch": 8,
        "delivered_once": 64,
        "dispatch_p50_ms": 429.413,
        "dispatch_p95_ms": 853.372,
        "dispatch_max_ms": 854.089
      },
      {
        "arm": "single",
        "count": 64,
        "rtt_ms": 100,
        "round": 2,
        "polls": 64,
        "maximum_batch": 1,
        "delivered_once": 64,
        "dispatch_p50_ms": 3369.694,
        "dispatch_p95_ms": 6422.027,
        "dispatch_max_ms": 6737.604
      },
      {
        "arm": "single",
        "count": 64,
        "rtt_ms": 100,
        "round": 3,
        "polls": 64,
        "maximum_batch": 1,
        "delivered_once": 64,
        "dispatch_p50_ms": 3370.564,
        "dispatch_p95_ms": 6425.811,
        "dispatch_max_ms": 6745.014
      },
      {
        "arm": "batch8",
        "count": 64,
        "rtt_ms": 100,
        "round": 3,
        "polls": 8,
        "maximum_batch": 8,
        "delivered_once": 64,
        "dispatch_p50_ms": 425.225,
        "dispatch_p95_ms": 854.403,
        "dispatch_max_ms": 855.116
      },
      {
        "arm": "single",
        "count": 64,
        "rtt_ms": 500,
        "round": 1,
        "polls": 64,
        "maximum_batch": 1,
        "delivered_once": 64,
        "dispatch_p50_ms": 16182.125,
        "dispatch_p95_ms": 30841.547,
        "dispatch_max_ms": 32361.044
      },
      {
        "arm": "batch8",
        "count": 64,
        "rtt_ms": 500,
        "round": 1,
        "polls": 8,
        "maximum_batch": 8,
        "delivered_once": 64,
        "dispatch_p50_ms": 2029.188,
        "dispatch_p95_ms": 4060.939,
        "dispatch_max_ms": 4061.441
      }
    ],
    "success": true
  },
  "harness_sha256": {
    "ltbb-claude-round-probe.py": "1c9513bcb25411c2b8c9b3215717d35fa68615ff11a39accd8644688bdc3a043",
    "ltbb-claude-partial-probe.py": "fa06827615a8513614416eda3527a6cd774241885b060915df195afc5a14e75c",
    "ltbb-claude-concurrent-driver.py": "8a3dcc74b0caac560d4543602b1236bce086d48ede2ef2af33f60d36ac2a2e7a",
    "ltbb-https-reuse-probe.py": "8dfad9fc31fea0420e6dfff86a2708d2fd235df074e16ec7610f9d49fa94699c"
  },
  "candidate_source_sha256": "d21fe481affe22ca4db8b039c51695b90ee31a380b7215154fb34d7d617815a7"
}
```
