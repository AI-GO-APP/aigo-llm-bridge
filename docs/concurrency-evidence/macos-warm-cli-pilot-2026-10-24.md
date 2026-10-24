# Mac warm CLI pilot metadata

Synthetic-only feasibility evidence. No request, answer, event, stderr, credential or client Key is retained. These small sequential arms do not establish the #39 burst or sustained gates.

```json
{
  "schema": 1,
  "date": "2026-10-24",
  "platform": "macOS",
  "release_gates_passed": false,
  "confirmation_commit": "0b94385f44c6fe6158f7e92d924bd394e5011184",
  "initial_provenance": "Initial working-tree prototype before commit; hashes not captured. Idle/feasibility only, not an immutable acceptance run.",
  "initial_report_limitation": "Usage field names were filtered incorrectly and empty in first report. No token/cost claim from that run. Fixed and confirmed separately.",
  "initial_report": {
    "schema": 1,
    "experiment": "single-use Codex initialize-only pilot",
    "installed_version": "0.9.7-mac.1",
    "production_changed": false,
    "release_gates_passed": false,
    "resident": 2,
    "concurrency": 8,
    "automatic_inference_retries": 0,
    "raw_content_saved": false,
    "rows": [
      {
        "arm": "cold",
        "index": 0,
        "correct": true,
        "model_match": true,
        "usage": {},
        "seconds": 3.7135,
        "timings_ms": {
          "cli_spawn_ms": 4,
          "cli_ready_ms": 71,
          "provider_setup_ms": 62,
          "inference_ms": 3479
        }
      },
      {
        "arm": "warm",
        "index": 0,
        "correct": true,
        "model_match": true,
        "usage": {},
        "seconds": 4.4271,
        "timings_ms": {
          "provider_setup_ms": 57,
          "inference_ms": 4296
        }
      },
      {
        "arm": "warm",
        "index": 1,
        "correct": true,
        "model_match": true,
        "usage": {},
        "seconds": 3.4759,
        "timings_ms": {
          "provider_setup_ms": 58,
          "inference_ms": 3316
        }
      },
      {
        "arm": "cold",
        "index": 1,
        "correct": true,
        "model_match": true,
        "usage": {},
        "seconds": 3.2856,
        "timings_ms": {
          "cli_spawn_ms": 1,
          "cli_ready_ms": 41,
          "provider_setup_ms": 60,
          "inference_ms": 3097
        }
      },
      {
        "arm": "cold",
        "index": 2,
        "correct": true,
        "model_match": true,
        "usage": {},
        "seconds": 3.5616,
        "timings_ms": {
          "cli_spawn_ms": 3,
          "cli_ready_ms": 62,
          "provider_setup_ms": 62,
          "inference_ms": 3344
        }
      },
      {
        "arm": "warm",
        "index": 2,
        "correct": true,
        "model_match": true,
        "usage": {},
        "seconds": 3.4355,
        "timings_ms": {
          "provider_setup_ms": 62,
          "inference_ms": 3299
        }
      }
    ],
    "resources": [],
    "idle": {
      "seconds": 600.103,
      "thread_starts": 0,
      "turn_starts": 0,
      "work_events": 0
    },
    "experiment_wall_seconds_including_idle_refill": 622.5208,
    "pool": {
      "starting": 0,
      "idle": 2,
      "active": 0,
      "closing": 0,
      "total": 2,
      "limit": 8,
      "peak": 3,
      "created": 14,
      "warm_hits": 3,
      "cold_starts": 3,
      "refill_failures": 0,
      "paused": false
    },
    "after_close": {
      "starting": 0,
      "idle": 0,
      "active": 0,
      "closing": 0,
      "total": 0,
      "limit": 8,
      "peak": 3,
      "created": 14,
      "warm_hits": 3,
      "cold_starts": 3,
      "refill_failures": 0,
      "paused": false
    },
    "cleanup_seconds": 0.0762,
    "owned_clis_stopped": true,
    "owned_cwds_removed": true
  },
  "initial_sampler_limited_coverage": "Started about one minute into idle; missing initial startup; no argv collected.",
  "initial_observed_resources": {
    "pid_scope": "owned pilot descendants only; no argv",
    "peak_rss_kib": 289376,
    "peak_cpu_percent_lifetime_average": 39.5,
    "peak_descendants": 3,
    "peak_tree_fds": 255,
    "samples": 2261
  },
  "confirmation": {
    "schema": 1,
    "experiment": "single-use Codex initialize-only pilot",
    "installed_version": "0.9.7-mac.1",
    "production_changed": false,
    "release_gates_passed": false,
    "resident": 2,
    "concurrency": 8,
    "automatic_inference_retries": 0,
    "raw_content_saved": false,
    "rows": [
      {
        "arm": "cold",
        "index": 0,
        "correct": true,
        "model_match": true,
        "usage": {
          "prompt_tokens": 4206,
          "completion_tokens": 9,
          "prompt_tokens_details": {
            "cached_tokens": 3072
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        },
        "seconds": 3.6514,
        "timings_ms": {
          "cli_spawn_ms": 1,
          "cli_ready_ms": 38,
          "provider_setup_ms": 54,
          "inference_ms": 3486
        }
      },
      {
        "arm": "warm",
        "index": 0,
        "correct": true,
        "model_match": true,
        "usage": {
          "prompt_tokens": 4210,
          "completion_tokens": 9,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        },
        "seconds": 2.8825,
        "timings_ms": {
          "provider_setup_ms": 61,
          "inference_ms": 2747
        }
      },
      {
        "arm": "warm",
        "index": 1,
        "correct": true,
        "model_match": true,
        "usage": {
          "prompt_tokens": 4206,
          "completion_tokens": 9,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        },
        "seconds": 4.0329,
        "timings_ms": {
          "provider_setup_ms": 58,
          "inference_ms": 3899
        }
      },
      {
        "arm": "cold",
        "index": 1,
        "correct": true,
        "model_match": true,
        "usage": {
          "prompt_tokens": 4208,
          "completion_tokens": 9,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        },
        "seconds": 3.9234,
        "timings_ms": {
          "cli_spawn_ms": 2,
          "cli_ready_ms": 52,
          "provider_setup_ms": 62,
          "inference_ms": 3740
        }
      },
      {
        "arm": "cold",
        "index": 2,
        "correct": true,
        "model_match": true,
        "usage": {
          "prompt_tokens": 4206,
          "completion_tokens": 9,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        },
        "seconds": 3.1618,
        "timings_ms": {
          "cli_spawn_ms": 1,
          "cli_ready_ms": 40,
          "provider_setup_ms": 62,
          "inference_ms": 2992
        }
      },
      {
        "arm": "warm",
        "index": 2,
        "correct": true,
        "model_match": true,
        "usage": {
          "prompt_tokens": 4206,
          "completion_tokens": 9,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        },
        "seconds": 3.3202,
        "timings_ms": {
          "provider_setup_ms": 56,
          "inference_ms": 3195
        }
      }
    ],
    "source_sha256": {
      "desktop_bridge/providers.py": "fe0f34a01f36e28aa088e386875f31553992cf89b078b833027618449ca921b0",
      "desktop_bridge/codex_session.py": "c4c67d25566b235e37fcb1b09aac658082552ef43640c1ad6b01b521674565bf",
      "tools/warm_cli_pool.py": "f57d8dde122192d0b93826b924f1fb6b55a0aac72a23ac92097843a74bc35bbc",
      "tools/benchmark_warm_cli.py": "cea6dd5c79e9f7dbc97b2793753007a21f91981ce10a38a08cbb67159d9c1c3a"
    },
    "cli_version": "codex-cli 0.163.0-alpha.11",
    "idle": {
      "seconds": 0.0,
      "thread_starts": 0,
      "turn_starts": 0,
      "work_events": 0
    },
    "experiment_wall_seconds_including_idle_refill": 21.4435,
    "pool": {
      "starting": 0,
      "idle": 2,
      "active": 0,
      "closing": 0,
      "quarantined": 0,
      "total": 2,
      "limit": 8,
      "peak": 3,
      "created": 14,
      "warm_hits": 3,
      "cold_starts": 3,
      "refill_failures": 0,
      "paused": false,
      "waiting_leases": 0
    },
    "after_close": {
      "starting": 0,
      "idle": 0,
      "active": 0,
      "closing": 0,
      "quarantined": 0,
      "total": 0,
      "limit": 8,
      "peak": 3,
      "created": 14,
      "warm_hits": 3,
      "cold_starts": 3,
      "refill_failures": 0,
      "paused": false,
      "waiting_leases": 0
    },
    "handshake_seconds_total": 0.6121,
    "cleanup_seconds": 0.0231,
    "owned_clis_stopped": true,
    "owned_cwds_removed": true,
    "resources": {
      "peak_tree_rss_kib": 289088,
      "peak_tree_cpu_percent_lifetime_average": 38.9,
      "peak_descendants": 4,
      "peak_tree_fds": 255,
      "samples": 161,
      "sampling_errors": 0,
      "cpu_kind": "ps lifetime-average sampled maximum; 100% is one logical core",
      "includes": "experiment, all owned descendants, refill and sampler ps process"
    },
    "single_request_summary": {
      "cold": {
        "requests": 3,
        "correct": 3,
        "median_seconds": 3.6514
      },
      "warm": {
        "requests": 3,
        "correct": 3,
        "median_seconds": 3.3202
      }
    }
  },
  "claude_ready_observation": {
    "cli_version": "2.1.306",
    "mode": "restricted print stream-json with stdin held open",
    "input_bytes_sent": 0,
    "observed_seconds": 3.005,
    "alive_before_close": true,
    "event_type_counts": {},
    "cleanup_seconds": 0.019,
    "process_stopped": true,
    "inference_requests_sent": 0,
    "validated_ready_boundary": false
  }
}
```
