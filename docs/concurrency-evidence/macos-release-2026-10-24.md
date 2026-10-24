# Mac 0.9.7-mac.1 發布驗收 metadata

此為已發布 immutable runtime 的文件收據；下列 JSON 只含固定驗收 metadata，不是可執行設定或新發布內容。

```json
{
  "schema": 1,
  "version": "0.9.7-mac.1",
  "source_commit": "66a2c5364d7b7c9ebe29187cd0c2a7f1f48543ce",
  "release_url": "https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.7-mac.1",
  "release_workflow": "https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40054773425",
  "download": {
    "success": true,
    "tag": "macos-source-v0.9.7-mac.1",
    "source_commit": "66a2c5364d7b7c9ebe29187cd0c2a7f1f48543ce",
    "sha256": "adb0a3718d617a42ba457ee4d291421fb2e18aff2278d1f1f3bd345c55b5f9c5",
    "assets": [
      "aigo-llm-bridge-macos-source-0.9.7-mac.1.zip",
      "aigo-llm-bridge-macos-source-0.9.7-mac.1.zip.sha256",
      "macos-source-manifest.json",
      "macos-source-self-test.json"
    ],
    "anonymous_download": true,
    "authorization_header_used": false,
    "runtime_modules_match_live_test": true,
    "manifest_clean": true
  },
  "public_zip_install": {
    "success": true,
    "version": "0.9.7-mac.1",
    "source_commit": "66a2c5364d7b7c9ebe29187cd0c2a7f1f48543ce",
    "download_installed": true,
    "fixed_machine_lock": true,
    "rejected_profile_no_database": true,
    "shutdown_api_closed": true,
    "max_concurrent_requests": 64,
    "credentials_or_power_changed": false
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
      "version": "0.9.7-mac.1",
      "source_commit": "66a2c5364d7b7c9ebe29187cd0c2a7f1f48543ce"
    },
    {
      "check": "device_keys_models_capacity_preserved",
      "passed": true,
      "version": "0.9.7-mac.1",
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
      "seconds": 7.912,
      "locked_before": false,
      "locked_after": false,
      "cost_usd": 0.00845,
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
  "post_upgrade_https": [
    {
      "version": "0.9.7-mac.1",
      "source_commit": "66a2c5364d7b7c9ebe29187cd0c2a7f1f48543ce",
      "inference_retries": 0,
      "success": true,
      "decisions_http": 200,
      "receipt_http": 200,
      "seconds": 8.9241,
      "cost_usd": 0.006742,
      "model": "anthropic/claude-haiku-4.5",
      "temporary_key_revoked": true,
      "settings_preserved": true,
      "all_original_key_rows_preserved": true,
      "original_key_rows": 28,
      "active_key_count": 3,
      "installed_runtime_matches_live_test": true
    },
    {
      "version": "0.9.7-mac.1",
      "source_commit": "66a2c5364d7b7c9ebe29187cd0c2a7f1f48543ce",
      "inference_retries": 0,
      "success": true,
      "decisions_http": 200,
      "receipt_http": 200,
      "seconds": 15.7967,
      "cost_usd": 0.012707,
      "model": "anthropic/claude-haiku-4.5",
      "choice_score_valid": true,
      "cli_calls_completed": 2,
      "temporary_key_revoked": true,
      "settings_preserved": true,
      "all_original_key_rows_preserved": true,
      "original_key_rows": 28,
      "active_key_count": 3,
      "installed_runtime_matches_live_test": true
    }
  ],
  "rollback_baseline": "0.9.5-mac.1",
  "database_restored_or_replaced": false,
  "worker_deployed": false,
  "windows_published": false,
  "free_cloudflare_quota_changed": false,
  "owner_local_files_preserved": true,
  "success": true
}
```
