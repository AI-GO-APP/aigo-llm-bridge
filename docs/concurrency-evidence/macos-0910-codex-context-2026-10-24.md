# Mac 0.9.10 Codex 上下文：數字證據

僅合成測試的 allowlist metadata；不含 KEY、原始內容、CLI events／stderr 或個人設定值。mock token 估算不作計費證明；真 API 每版各兩筆／端點，cache 與時間一併揭露。

```json
{
  "schema": 1,
  "version": "0.9.10-mac.1",
  "source_commit": "26ab468b157747f1de6ea5dc3e934874b2f6bedf",
  "zip_sha256": "122b6e1f1fd2fcee433c1521f71febb56dd59367ad14e50d13ea6a56d5689f8c",
  "release_workflow_run": 40067596369,
  "pr": 47,
  "reviewed_head": "a754324ce9dc73614abe97a544f85c95faa49c90",
  "ci_runs": {
    "core": 40067147998,
    "mac": 40067147947,
    "windows": 40067147988,
    "windows_installer": 40067148031
  },
  "local_tests": {
    "passed": 469,
    "skipped": 23,
    "worker_passed": 13,
    "native_screen_count": 64,
    "native_console_success": true
  },
  "download": {
    "success": true,
    "assets": [
      "aigo-llm-bridge-macos-source-0.9.10-mac.1.zip",
      "aigo-llm-bridge-macos-source-0.9.10-mac.1.zip.sha256",
      "macos-source-manifest.json",
      "macos-source-self-test.json"
    ],
    "anonymous_download": true,
    "authorization_header_used": false,
    "runtime_and_opt_in_tools_match_reviewed_source": true,
    "manifest_clean": true
  },
  "public_zip_install": {
    "success": true,
    "public_zip": true,
    "original_version": "0.9.9-mac.1",
    "version": "0.9.10-mac.1",
    "download_installed": true,
    "fixed_machine_lock": true,
    "rejected_profile_no_database": true,
    "shutdown_api_closed": true,
    "max_concurrent_requests": 64,
    "credentials_or_power_changed": false,
    "original_restart_command_ok": true,
    "original_restored_healthy": true
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
      "version": "0.9.10-mac.1",
      "source_commit": "26ab468b157747f1de6ea5dc3e934874b2f6bedf"
    },
    {
      "check": "device_keys_models_capacity_preserved",
      "passed": true,
      "version": "0.9.10-mac.1",
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
      "seconds": 4.696,
      "locked_before": false,
      "locked_after": false,
      "cost_usd": 0.0016932,
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
  "runtime": {
    "success": true,
    "stop_seconds": 1.1648,
    "observed_owned_processes": 3,
    "observed_empty_cwds": 2,
    "owned_processes_remaining": 0,
    "old_cwds_remaining": 0,
    "restart_ok": true,
    "other_settings_preserved": true,
    "all_prior_key_rows_preserved": true,
    "prior_key_rows": 49,
    "active_keys": 3,
    "effective_capacity": {
      "inference_workers": 64,
      "inference_resident": 2,
      "inference_pending": 64
    },
    "new_synthetic_keys_revoked": true,
    "rollback_ready": true,
    "profile_path_preserved": true,
    "personal_config_preserved": true
  },
  "final_health": {
    "ok": true,
    "version": "0.9.10-mac.1",
    "accepting": true,
    "running_requests": 0,
    "queued_requests": 0,
    "max_concurrent_requests": 64,
    "max_execution_workers": 64,
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
    }
  },
  "controlled_loopback": {
    "cli_version": "0.163.0-alpha.11",
    "real_inference_calls": 0,
    "raw_payload_saved": false,
    "session_closed": true,
    "sent": {
      "initialize": 1,
      "initialized": 1,
      "skills/list": 1,
      "thread/start": 1,
      "turn/start": 1
    },
    "rollout_files": 0,
    "markers": {
      "additional_tools": true,
      "functions.exec": false,
      "functions.wait": false,
      "request_user_input": true,
      "apply_patch": true,
      "create_goal": false,
      "update_goal": false,
      "get_goal": false,
      "list_mcp_resources": true,
      "skills_instructions": false,
      "SKILL.md": false,
      "environment_context": true,
      "permissions instructions": true,
      "collaboration_mode": true
    },
    "serialized_input_o200k_estimate": 3719,
    "estimated_tokens_are_billing": false
  },
  "comparison": {
    "success": true,
    "schema": 1,
    "comparison": "context before/after, warm held at 2/64; not warm off/on",
    "causal_latency_effect_established": false,
    "input_estimate_used_for_billing": false,
    "versions": {
      "before": {
        "version": "0.9.9-mac.1",
        "source_commit": "2be8195037c304b988c46f8a48697486978b3592",
        "transport": "public HTTPS",
        "rounds": 2,
        "inference_retries": 0,
        "concurrent_requests": 1,
        "resident": 2,
        "workers": 64,
        "temporary_key_revoked": true,
        "settings_preserved": true,
        "owner_keys_preserved": true,
        "runtime_sha256": {
          "__init__.py": "542d9fc20ad24b6234174293e8e14b2e8f4e6fe57097b35be06c2f2152318532",
          "__main__.py": "e7a30ffe22f0d8397036ee2d27ef70e4f789b747137dd6116662aac7972d0b31",
          "byo.py": "b09347f1e3b63606b296e5ae59e33e8c221f20622c7260db3b5dc60960a0b2a1",
          "capacity.py": "06b9e06bcae78b15ddf08658f9d63017ddb7d0b654c8dcc8f92b7484aa122e92",
          "codex_session.py": "c4c67d25566b235e37fcb1b09aac658082552ef43640c1ad6b01b521674565bf",
          "connection_test.py": "2e603301bc0338e50da08cbdf9cc66016a3621fa4fb2738ea43b0a0996c2a35a",
          "contract.py": "57f4ea3df9753886c81d6d716b355ec22096ca21f8a171e3fbcf5a274ea6ef26",
          "decision_contract.py": "8d2be19b8f132ecee902593979990168caf6a976a70fa12a01e3a4eefdb62387",
          "decisions.py": "4077ef9449424e19c58aad3a9e4059276186403ee8c703db801bc8a794844544",
          "errors.py": "e7b166eadf7b4e19e584ac2b553a7759cb1fecbac4433208655e3cfc65f72b5f",
          "execution_budget.py": "cef4b63ebbb79f43796b01e34bc1468dbd946cbbce13adcf3cb4702d81979800",
          "handoff.py": "e43754953f7df835c598462287373acf6cd7b864a6539b494cb5d0d623d96269",
          "keychain.py": "427aaf083e8574b07dad56d33a8b2a21d378fb7e3121dd2f73c4f7ec365e8b64",
          "launcher.py": "48f7c488409e2ea3f3b22fd2f8a945366d4b44a917b79930fb2140132d3147fe",
          "macos_console.py": "4d4391b4a5e0b6b1bfc7b9a527b22b0cdacc8a189044f56dfd927e4e2cb07a87",
          "macos_instance.py": "0f87120e2f2c22d11a16ab90190d91fe27eb291f7ee8225b5f2ef0c3ae41fd1c",
          "macos_management.py": "06597f1d851b178c004d4d0266da19d47c0ca4d02ccf04f8512c8cbe4dc8c283",
          "macos_onboarding.py": "bdfba5a269a0127d78f79e3287b1cd8d523143656f6415d5e1b1cac33611cd2e",
          "macos_power.py": "a7ba913f619429cf1cfe3e76b0231586f617c1adc727ea80b20246987fb719fd",
          "management.py": "3761b7d2505e1f6150e3502f9f36aaaa68a44f998fe77b12b125408fee5f3a87",
          "model_catalog.py": "3a33482ad51a89ab83afeb0978e7fc781d4763ec8567f481d0ad284a405c8f6c",
          "paths.py": "d8627d788bf5496c49cd4c647d96d65dabc0edcc0ded1f1873c8d209a752e11f",
          "pricing.py": "c4a9ad54ce70fc114511b2cd8baca1cc24a03fc2a598fab6f0178bb2dbbd4f81",
          "process.py": "63ccab2bd50761283f83e982749064ee74492c9c530ed98eb1e89f5b7247f20f",
          "providers.py": "f848d4396942f6a001141b1c0bd441e7afaf6b01c2b4d91664280c5b1f33ce8b",
          "public_endpoint.py": "b28d2077890f583290ba22df212762ff5dc23364e8a06d8c414da7dbf2fcabba",
          "relay.py": "2c3be2e5ad61771df11608292aead5752dd178e280fb75339a98ad69785cd35a",
          "schema_guard.py": "10fcef332675b10b84d50dfbddeb93a7a761642cb11d46096d9850fe480c0b90",
          "secret.py": "2dd0904a3fbe4c0c47d634e855bca7bd7e2914dd142192e575599871800467c2",
          "service.py": "ff01678a6d7b3f83e1b10d91de20df000d5694cc8b90b4103c5d9f011bb510c9",
          "setup_launcher.py": "aa38dc325dfd7b510905adcec5f159d9de4ee369dde19b240c4fcd32f6f4459c",
          "store.py": "8db21ecf765381452a590f9b5080a93ae612f268f4d30914e159a9cc78124487",
          "tool_contract.py": "ab9af1dc89dd74b67ee3ebb012c9d3cbf0cbcfda68c5cc71c5c60e9af6181d47",
          "tunnel.py": "99ad70af6beb0bb35c87bbbbbfb41cedd1bbe09262c9f0d1d955cfa015b5bc9c",
          "ui.py": "f3a6f3d5e56a0d3d5f2afcacc4286f7697c07244aa638f574291b4553ecbd0ee",
          "warm_pool.py": "caa5c4415ff5d13cf919dcd61188afa6d97ff3bbbe6cafef228a5b49252497e5",
          "warm_runtime.py": "41ccd363e215687e2ca77feb28f1ce3c753b926c092bbad0693ed3f957dfde30",
          "windows.py": "3dd80dd873aedc54ad5479f33ec075f44a017b2a12bfd10f0c98bd948b6beec2",
          "windows_cli.py": "6b82c7c9e812bbd64d0ee2546e7cd01e64a9dce90f5ab34e2308a9e99b43260e",
          "windows_console.py": "67d2dab538fe897564ec40dbe0dc4a4eaf1470d1c9ab0b9f79ea6c10fb0013e7",
          "windows_console_probe.py": "db36090d59a0a0580c8ac1f1a571bef4a1526487d6923ff7bbab1b22f0708356",
          "windows_http.py": "5a7332c7b264d9ed616ddac181e72f2a2e8b3ab8d41f3ba7bcbadd893e8e1116",
          "windows_instance.py": "5d7efaeefb7e2e48fbff06fa667d1a0357a8a75434946e911181df7cfd8f09db",
          "windows_management.py": "c726237affbe20d42b5b69d90f5bb471e2d86a3fac27369a2c267ba1241a1091",
          "windows_onboarding.py": "2416d4facc77bb8051d77732f8f249d457c7ff15c45260bd4b9f5f95e85b03d1",
          "windows_power.py": "d7a6d52e0e4b016b38d686c2aece571ed413bfd4c2a1989311dc9879c43b36a7",
          "windows_power_admin.py": "1912048f8d57708eda7f87787961273c7b3fa4343f5a7ec1a45f687d1d19f28b",
          "windows_release.py": "bed18352285fae3f7b4e3ae273fd0c83bbefc09819b1eaaeb048a63fc61ef59b",
          "windows_updates.py": "bc98b6198f83bc9280b533770ee0e5318215041f0d98b35700894fe71e2596b7"
        },
        "rows": [
          {
            "round": 1,
            "model": "openai/gpt-6.1-sol",
            "protocol": "chat",
            "request_bytes": 112,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 6.2419,
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
              "provider_setup_ms": 131,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 3103,
              "output_validation_ms": null,
              "total_ms": 4300
            },
            "passed": true,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "request_id": "61abdfae-624e-49c8-a4f8-b0df4832ec05"
          },
          {
            "round": 1,
            "model": "openai/gpt-6.1-sol",
            "protocol": "decisions",
            "request_bytes": 148,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 7.587,
            "response_valid": true,
            "execution": {
              "warm_hits": 1,
              "cold_starts": 0
            },
            "lease_valid": true,
            "receipt_http": 200,
            "receipt_complete": true,
            "cost_matches": true,
            "prompt_tokens": 4333,
            "completion_tokens": 39,
            "cost_usd": 0.0032192,
            "timings_ms": {
              "validation_ms": 1,
              "schema_wait_ms": null,
              "schema_execution_ms": null,
              "queue_wait_ms": 0,
              "provider_setup_ms": 108,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 6437,
              "output_validation_ms": 0,
              "total_ms": 6740
            },
            "passed": true,
            "cached_tokens": 3072,
            "reasoning_tokens": 21,
            "request_id": "2fcf3451-40dc-4455-9c3d-d4a25c40f653"
          },
          {
            "round": 2,
            "model": "openai/gpt-6.1-sol",
            "protocol": "chat",
            "request_bytes": 112,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 3.8151,
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
            "cost_usd": 0.0025992,
            "timings_ms": {
              "validation_ms": 0,
              "schema_wait_ms": null,
              "schema_execution_ms": null,
              "queue_wait_ms": 0,
              "provider_setup_ms": 131,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 2583,
              "output_validation_ms": null,
              "total_ms": 2916
            },
            "passed": true,
            "cached_tokens": 3072,
            "reasoning_tokens": 0,
            "request_id": "96c5979d-e65c-4a7e-920e-0192c8588810"
          },
          {
            "round": 2,
            "model": "openai/gpt-6.1-sol",
            "protocol": "decisions",
            "request_bytes": 148,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 4.45,
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
            "completion_tokens": 31,
            "cost_usd": 0.00898,
            "timings_ms": {
              "validation_ms": 0,
              "schema_wait_ms": null,
              "schema_execution_ms": null,
              "queue_wait_ms": 0,
              "provider_setup_ms": 111,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 3252,
              "output_validation_ms": 0,
              "total_ms": 3567
            },
            "passed": true,
            "cached_tokens": 0,
            "reasoning_tokens": 13,
            "request_id": "d778c9c7-9424-4614-be8b-2d2d80c30bda"
          }
        ],
        "summary": [
          {
            "model": "openai/gpt-6.1-sol",
            "protocol": "chat",
            "requests": 2,
            "passed": 2,
            "median_seconds": 5.0285,
            "max_seconds": 6.2419
          },
          {
            "model": "openai/gpt-6.1-sol",
            "protocol": "decisions",
            "requests": 2,
            "passed": 2,
            "median_seconds": 6.0185,
            "max_seconds": 7.587
          }
        ]
      },
      "after": {
        "version": "0.9.10-mac.1",
        "source_commit": "26ab468b157747f1de6ea5dc3e934874b2f6bedf",
        "transport": "public HTTPS",
        "rounds": 2,
        "inference_retries": 0,
        "concurrent_requests": 1,
        "resident": 2,
        "workers": 64,
        "temporary_key_revoked": true,
        "settings_preserved": true,
        "owner_keys_preserved": true,
        "runtime_sha256": {
          "__init__.py": "cbbba475e0efe2a0726e6869af5696886ea994628008c179c5e17d4b7a9d9fe6",
          "__main__.py": "e7a30ffe22f0d8397036ee2d27ef70e4f789b747137dd6116662aac7972d0b31",
          "byo.py": "b09347f1e3b63606b296e5ae59e33e8c221f20622c7260db3b5dc60960a0b2a1",
          "capacity.py": "06b9e06bcae78b15ddf08658f9d63017ddb7d0b654c8dcc8f92b7484aa122e92",
          "codex_session.py": "3e8bcc886edb47427140ccf80e5b77ac5af9294dcb1d389a6c93180fe2229f73",
          "connection_test.py": "2e603301bc0338e50da08cbdf9cc66016a3621fa4fb2738ea43b0a0996c2a35a",
          "contract.py": "57f4ea3df9753886c81d6d716b355ec22096ca21f8a171e3fbcf5a274ea6ef26",
          "decision_contract.py": "8d2be19b8f132ecee902593979990168caf6a976a70fa12a01e3a4eefdb62387",
          "decisions.py": "4077ef9449424e19c58aad3a9e4059276186403ee8c703db801bc8a794844544",
          "errors.py": "e7b166eadf7b4e19e584ac2b553a7759cb1fecbac4433208655e3cfc65f72b5f",
          "execution_budget.py": "cef4b63ebbb79f43796b01e34bc1468dbd946cbbce13adcf3cb4702d81979800",
          "handoff.py": "e43754953f7df835c598462287373acf6cd7b864a6539b494cb5d0d623d96269",
          "keychain.py": "427aaf083e8574b07dad56d33a8b2a21d378fb7e3121dd2f73c4f7ec365e8b64",
          "launcher.py": "48f7c488409e2ea3f3b22fd2f8a945366d4b44a917b79930fb2140132d3147fe",
          "macos_console.py": "4d4391b4a5e0b6b1bfc7b9a527b22b0cdacc8a189044f56dfd927e4e2cb07a87",
          "macos_instance.py": "0f87120e2f2c22d11a16ab90190d91fe27eb291f7ee8225b5f2ef0c3ae41fd1c",
          "macos_management.py": "06597f1d851b178c004d4d0266da19d47c0ca4d02ccf04f8512c8cbe4dc8c283",
          "macos_onboarding.py": "bdfba5a269a0127d78f79e3287b1cd8d523143656f6415d5e1b1cac33611cd2e",
          "macos_power.py": "a7ba913f619429cf1cfe3e76b0231586f617c1adc727ea80b20246987fb719fd",
          "management.py": "3761b7d2505e1f6150e3502f9f36aaaa68a44f998fe77b12b125408fee5f3a87",
          "model_catalog.py": "3a33482ad51a89ab83afeb0978e7fc781d4763ec8567f481d0ad284a405c8f6c",
          "paths.py": "d8627d788bf5496c49cd4c647d96d65dabc0edcc0ded1f1873c8d209a752e11f",
          "pricing.py": "c4a9ad54ce70fc114511b2cd8baca1cc24a03fc2a598fab6f0178bb2dbbd4f81",
          "process.py": "63ccab2bd50761283f83e982749064ee74492c9c530ed98eb1e89f5b7247f20f",
          "providers.py": "f22f4ba286c9e7464f83da2e07661f97d5997e1387329f47b64c96458692bbc7",
          "public_endpoint.py": "b28d2077890f583290ba22df212762ff5dc23364e8a06d8c414da7dbf2fcabba",
          "relay.py": "2c3be2e5ad61771df11608292aead5752dd178e280fb75339a98ad69785cd35a",
          "schema_guard.py": "10fcef332675b10b84d50dfbddeb93a7a761642cb11d46096d9850fe480c0b90",
          "secret.py": "2dd0904a3fbe4c0c47d634e855bca7bd7e2914dd142192e575599871800467c2",
          "service.py": "ff01678a6d7b3f83e1b10d91de20df000d5694cc8b90b4103c5d9f011bb510c9",
          "setup_launcher.py": "aa38dc325dfd7b510905adcec5f159d9de4ee369dde19b240c4fcd32f6f4459c",
          "store.py": "8db21ecf765381452a590f9b5080a93ae612f268f4d30914e159a9cc78124487",
          "tool_contract.py": "ab9af1dc89dd74b67ee3ebb012c9d3cbf0cbcfda68c5cc71c5c60e9af6181d47",
          "tunnel.py": "99ad70af6beb0bb35c87bbbbbfb41cedd1bbe09262c9f0d1d955cfa015b5bc9c",
          "ui.py": "f3a6f3d5e56a0d3d5f2afcacc4286f7697c07244aa638f574291b4553ecbd0ee",
          "warm_pool.py": "caa5c4415ff5d13cf919dcd61188afa6d97ff3bbbe6cafef228a5b49252497e5",
          "warm_runtime.py": "41ccd363e215687e2ca77feb28f1ce3c753b926c092bbad0693ed3f957dfde30",
          "windows.py": "3dd80dd873aedc54ad5479f33ec075f44a017b2a12bfd10f0c98bd948b6beec2",
          "windows_cli.py": "6b82c7c9e812bbd64d0ee2546e7cd01e64a9dce90f5ab34e2308a9e99b43260e",
          "windows_console.py": "67d2dab538fe897564ec40dbe0dc4a4eaf1470d1c9ab0b9f79ea6c10fb0013e7",
          "windows_console_probe.py": "db36090d59a0a0580c8ac1f1a571bef4a1526487d6923ff7bbab1b22f0708356",
          "windows_http.py": "5a7332c7b264d9ed616ddac181e72f2a2e8b3ab8d41f3ba7bcbadd893e8e1116",
          "windows_instance.py": "5d7efaeefb7e2e48fbff06fa667d1a0357a8a75434946e911181df7cfd8f09db",
          "windows_management.py": "c726237affbe20d42b5b69d90f5bb471e2d86a3fac27369a2c267ba1241a1091",
          "windows_onboarding.py": "2416d4facc77bb8051d77732f8f249d457c7ff15c45260bd4b9f5f95e85b03d1",
          "windows_power.py": "d7a6d52e0e4b016b38d686c2aece571ed413bfd4c2a1989311dc9879c43b36a7",
          "windows_power_admin.py": "1912048f8d57708eda7f87787961273c7b3fa4343f5a7ec1a45f687d1d19f28b",
          "windows_release.py": "bed18352285fae3f7b4e3ae273fd0c83bbefc09819b1eaaeb048a63fc61ef59b",
          "windows_updates.py": "bc98b6198f83bc9280b533770ee0e5318215041f0d98b35700894fe71e2596b7"
        },
        "rows": [
          {
            "round": 1,
            "model": "openai/gpt-6.1-sol",
            "protocol": "chat",
            "request_id": "5beb8e2a-a683-4cac-8d37-99abd80e1cb0",
            "request_bytes": 112,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 5.6791,
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
            "cost_usd": 0.006292,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "timings_ms": {
              "validation_ms": 0,
              "schema_wait_ms": null,
              "schema_execution_ms": null,
              "queue_wait_ms": 0,
              "provider_setup_ms": 210,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 3012,
              "output_validation_ms": null,
              "total_ms": 3485
            },
            "passed": true,
            "cache_reasoning_source": "local SQLite allowlist metadata; compact receipt omits subsets"
          },
          {
            "round": 1,
            "model": "openai/gpt-6.1-sol",
            "protocol": "decisions",
            "request_id": "39fd63a4-ab06-42eb-b025-b6ac5422ea2f",
            "request_bytes": 148,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 6.7029,
            "response_valid": true,
            "execution": {
              "warm_hits": 1,
              "cold_starts": 0
            },
            "lease_valid": true,
            "receipt_http": 200,
            "receipt_complete": true,
            "cost_matches": true,
            "prompt_tokens": 3263,
            "completion_tokens": 37,
            "cost_usd": 0.006896,
            "cached_tokens": 0,
            "reasoning_tokens": 19,
            "timings_ms": {
              "validation_ms": 1,
              "schema_wait_ms": null,
              "schema_execution_ms": null,
              "queue_wait_ms": 0,
              "provider_setup_ms": 214,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 4298,
              "output_validation_ms": 0,
              "total_ms": 4688
            },
            "passed": true,
            "cache_reasoning_source": "local SQLite allowlist metadata; compact receipt omits subsets"
          },
          {
            "round": 2,
            "model": "openai/gpt-6.1-sol",
            "protocol": "chat",
            "request_id": "6c0e757f-2ebe-4a60-8143-ed9d5a1bb3dc",
            "request_bytes": 112,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 5.3082,
            "response_valid": true,
            "execution": {
              "warm_hits": 1,
              "cold_starts": 0
            },
            "lease_valid": true,
            "receipt_http": 200,
            "receipt_complete": true,
            "cost_matches": true,
            "prompt_tokens": 3119,
            "completion_tokens": 5,
            "cost_usd": 0.0016672,
            "cached_tokens": 2432,
            "reasoning_tokens": 0,
            "timings_ms": {
              "validation_ms": 0,
              "schema_wait_ms": null,
              "schema_execution_ms": null,
              "queue_wait_ms": 0,
              "provider_setup_ms": 122,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 3048,
              "output_validation_ms": null,
              "total_ms": 3404
            },
            "passed": true,
            "cache_reasoning_source": "local SQLite allowlist metadata; compact receipt omits subsets"
          },
          {
            "round": 2,
            "model": "openai/gpt-6.1-sol",
            "protocol": "decisions",
            "request_id": "028bec7a-37fa-4186-9e86-c75137e22402",
            "request_bytes": 148,
            "ready_residents_before": 2,
            "http": 200,
            "seconds": 5.3462,
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
            "cached_tokens": 0,
            "reasoning_tokens": 18,
            "timings_ms": {
              "validation_ms": 0,
              "schema_wait_ms": null,
              "schema_execution_ms": null,
              "queue_wait_ms": 0,
              "provider_setup_ms": 171,
              "cli_spawn_ms": null,
              "cli_ready_ms": null,
              "inference_ms": 3906,
              "output_validation_ms": 0,
              "total_ms": 4401
            },
            "passed": true,
            "cache_reasoning_source": "local SQLite allowlist metadata; compact receipt omits subsets"
          }
        ],
        "summary": [
          {
            "model": "openai/gpt-6.1-sol",
            "protocol": "chat",
            "requests": 2,
            "passed": 2,
            "median_seconds": 5.4937,
            "max_seconds": 5.6791
          },
          {
            "model": "openai/gpt-6.1-sol",
            "protocol": "decisions",
            "requests": 2,
            "passed": 2,
            "median_seconds": 6.0245,
            "max_seconds": 6.7029
          }
        ]
      }
    },
    "results": [
      {
        "protocol": "chat",
        "samples_per_version": 2,
        "before_input_tokens": [
          4191,
          4193
        ],
        "after_input_tokens": [
          3121,
          3119
        ],
        "before_cached_tokens": [
          0,
          3072
        ],
        "after_cached_tokens": [
          0,
          2432
        ],
        "input_reduction_percent": 25.57,
        "before_median_seconds": 5.0285,
        "after_median_seconds": 5.4937,
        "median_time_reduction_percent": -9.25
      },
      {
        "protocol": "decisions",
        "samples_per_version": 2,
        "before_input_tokens": [
          4333,
          4335
        ],
        "after_input_tokens": [
          3263,
          3259
        ],
        "before_cached_tokens": [
          3072,
          0
        ],
        "after_cached_tokens": [
          0,
          0
        ],
        "input_reduction_percent": 24.76,
        "before_median_seconds": 6.0185,
        "after_median_seconds": 6.0245,
        "median_time_reduction_percent": -0.1
      }
    ]
  },
  "synthetic_usage_this_task": {
    "cli_attempts": 11,
    "baseline_calls": 4,
    "post_update_calls": 7,
    "zero_inference_expected_400": 1,
    "prompt_tokens": 39451,
    "completion_tokens": 218,
    "cost_usd": 0.060166800000000006
  },
  "owner_catalog_preflight": {
    "inference_calls": 0,
    "raw_catalog_or_paths_saved": false,
    "skill_paths_disabled": 5,
    "sent": {
      "initialize": 1,
      "initialized": 1,
      "skills/list": 1,
      "thread/start": 0,
      "turn/start": 0
    },
    "metadata_valid": true,
    "owned_process_closed": true,
    "personal_config_preserved": true
  },
  "remaining_builtin_context": true,
  "complete_general_warm_gate": false,
  "windows_native_subscription_acceptance": false,
  "raw_requests_responses_events_stderr_or_credentials_saved": false
}
```
