# Mac CLI 上下文續測：數字證據

合成內容、allowlist metadata；mock 近似估算與訂閱真 usage 分開，沒有原始封包／CLI 原文／憑證。純實驗，正式 runtime 維持 0.9.10。

```json
{
  "schema": 1,
  "date": "2026-10-24",
  "issue": 46,
  "product": "Local Token Buffet Bridge",
  "source_commit": "26ab468b157747f1de6ea5dc3e934874b2f6bedf",
  "installed_version": "0.9.10-mac.1",
  "scope": "experiments only; no runtime or deployment changes",
  "codex_cli_version": "0.163.0-alpha.11",
  "claude_cli_version": "2.1.306",
  "token_estimator": "o200k_base approximation for mock JSON only; actual usage uses provider CLI counts",
  "mock_turns": 24,
  "mock_real_inference_calls": 0,
  "raw_requests_responses_events_headers_or_credentials_saved": false,
  "codex_mock": [
    {
      "case": "current_0910",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3712,
        "sha256": "912bec9be575635eb4cd2257aea4162398deb7bd1eaa5d25ed172ec78ef30440"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "personality_none",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3714,
        "sha256": "8e4285e68e4d09bf33025c35ec6a32efb3c00b08948fdf5d9928982229639a8d"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "code_mode_host_on",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3721,
        "sha256": "a88367eee136c5c28d25c58520372ea9a6437c6a2411029db018da31f49cec35"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "code_mode_on",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3717,
        "sha256": "1070dea0555dd1faee0e999c1d7e23141d297baa6ce0c9c7ca3679a337264a67"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "code_mode_only_on",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3716,
        "sha256": "331a012bca92c5eb9799d4f46fe2a54cae3f1d6267b539aa20e09541c04fd583"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "code_mode_nested_off",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3723,
        "sha256": "5211b1c4bd827e3c03ff507b2385d1e3ce475538e677c59eabf09bc7b3c4bea0"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "code_mode_nested_exclude_functions",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 12939,
        "utf8_bytes": 12939,
        "o200k_estimate": 3242,
        "sha256": "37d2ac875e3ff8d2daf8eb13d11e8de525794d6cd3ac8309f8fd5e196fdb8fd1"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 10240,
            "utf8_bytes": 10240,
            "o200k_estimate": 2516,
            "sha256": "b98d33920445459b8874d41fa560cb5c8af87bc340d3e935e98046e2f9094f59"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
      "markers": {
        "additional_tools": true,
        "functions.exec": false,
        "functions.wait": false,
        "request_user_input": true,
        "apply_patch": false,
        "create_goal": false,
        "update_goal": false,
        "get_goal": false,
        "list_mcp_resources": false,
        "skills_instructions": false,
        "SKILL.md": false,
        "environment_context": true,
        "permissions instructions": true,
        "collaboration_mode": true
      },
      "tool_description_stats": null
    },
    {
      "case": "code_mode_interrupt_off",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3719,
        "sha256": "0321188705daf9d9680754abe8e183df569a6a686cb12f5ef039a64ec88ab0cd"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "current",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 14901,
        "utf8_bytes": 14901,
        "o200k_estimate": 3720,
        "sha256": "f558541ba7bcdfbebd2917e5f45a64d4f98f5d58ae7eb358685b1b8ee8e66b46"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": [
        {
          "name": "functions",
          "description_stats": {
            "characters": 0,
            "utf8_bytes": 0,
            "o200k_estimate": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "exec",
          "description_stats": {
            "characters": 7406,
            "utf8_bytes": 7406,
            "o200k_estimate": 1776,
            "sha256": "f5805eaf94530ca0ff793d1ed51cb934de8c255fcb329e22a817b0136573d391"
          },
          "referenced_methods": [
            "exec_command",
            "mcp__ologs__get_profile"
          ],
          "namespace_words": {
            "functions": false,
            "clock": true,
            "exec_command": true,
            "write_stdin": false,
            "apply_patch": true,
            "mcp": true,
            "tool_search": false
          }
        },
        {
          "name": "wait",
          "description_stats": {
            "characters": 769,
            "utf8_bytes": 769,
            "o200k_estimate": 181,
            "sha256": "582eb96e50ee4481cf30b33ad2358e7e24e7368aeb2cbe5122cef1912ad75385"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input",
          "description_stats": {
            "characters": 120,
            "utf8_bytes": 120,
            "o200k_estimate": 24,
            "sha256": "783ea374eaba01b1c7d453ff177ba9f27f45a6cb9c33a6f5fb1bed00251f00c7"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input_async",
          "description_stats": {
            "characters": 556,
            "utf8_bytes": 556,
            "o200k_estimate": 102,
            "sha256": "f7f47603a91513a78276c4091cd758ee99ca47e625bd7b0f4a8b305cebfa575c"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        }
      ]
    },
    {
      "case": "exclude_functions_clock",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 12634,
        "utf8_bytes": 12634,
        "o200k_estimate": 3159,
        "sha256": "7a3a169eec5419d895dda1eac3d88b92b7d8d6c5e0ece75db941c97c31fea76b"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 9935,
            "utf8_bytes": 9935,
            "o200k_estimate": 2426,
            "sha256": "e3a1fde6117036f528d56c9f532e873ed6f7b6db7da5fc63a8a21867dc674577"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
      "markers": {
        "additional_tools": true,
        "functions.exec": false,
        "functions.wait": false,
        "request_user_input": true,
        "apply_patch": false,
        "create_goal": false,
        "update_goal": false,
        "get_goal": false,
        "list_mcp_resources": false,
        "skills_instructions": false,
        "SKILL.md": false,
        "environment_context": true,
        "permissions instructions": true,
        "collaboration_mode": true
      },
      "tool_description_stats": [
        {
          "name": "functions",
          "description_stats": {
            "characters": 0,
            "utf8_bytes": 0,
            "o200k_estimate": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "exec",
          "description_stats": {
            "characters": 5200,
            "utf8_bytes": 5200,
            "o200k_estimate": 1282,
            "sha256": "6ed8fae71b1b4cd46ef7a598a8038eb04ffacdb095fe910d221e70fdcd521471"
          },
          "referenced_methods": [
            "exec_command",
            "mcp__ologs__get_profile"
          ],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": true,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": true,
            "tool_search": false
          }
        },
        {
          "name": "wait",
          "description_stats": {
            "characters": 769,
            "utf8_bytes": 769,
            "o200k_estimate": 181,
            "sha256": "582eb96e50ee4481cf30b33ad2358e7e24e7368aeb2cbe5122cef1912ad75385"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input",
          "description_stats": {
            "characters": 120,
            "utf8_bytes": 120,
            "o200k_estimate": 24,
            "sha256": "783ea374eaba01b1c7d453ff177ba9f27f45a6cb9c33a6f5fb1bed00251f00c7"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input_async",
          "description_stats": {
            "characters": 556,
            "utf8_bytes": 556,
            "o200k_estimate": 102,
            "sha256": "f7f47603a91513a78276c4091cd758ee99ca47e625bd7b0f4a8b305cebfa575c"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        }
      ]
    },
    {
      "case": "exclude_functions_only_without_enabled",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 12939,
        "utf8_bytes": 12939,
        "o200k_estimate": 3248,
        "sha256": "40c2eef4ae9fe75db141bb37d65feb87a88fa08450a51de2161daaec70d41049"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 10240,
            "utf8_bytes": 10240,
            "o200k_estimate": 2516,
            "sha256": "b98d33920445459b8874d41fa560cb5c8af87bc340d3e935e98046e2f9094f59"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
      "markers": {
        "additional_tools": true,
        "functions.exec": false,
        "functions.wait": false,
        "request_user_input": true,
        "apply_patch": false,
        "create_goal": false,
        "update_goal": false,
        "get_goal": false,
        "list_mcp_resources": false,
        "skills_instructions": false,
        "SKILL.md": false,
        "environment_context": true,
        "permissions instructions": true,
        "collaboration_mode": true
      },
      "tool_description_stats": [
        {
          "name": "functions",
          "description_stats": {
            "characters": 0,
            "utf8_bytes": 0,
            "o200k_estimate": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "exec",
          "description_stats": {
            "characters": 5491,
            "utf8_bytes": 5491,
            "o200k_estimate": 1358,
            "sha256": "2e05224c14d548fe74cf52af3c60e21391b4b60498489ef86d3200c4d9f3a49c"
          },
          "referenced_methods": [
            "exec_command",
            "mcp__ologs__get_profile"
          ],
          "namespace_words": {
            "functions": false,
            "clock": true,
            "exec_command": true,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": true,
            "tool_search": false
          }
        },
        {
          "name": "wait",
          "description_stats": {
            "characters": 769,
            "utf8_bytes": 769,
            "o200k_estimate": 181,
            "sha256": "582eb96e50ee4481cf30b33ad2358e7e24e7368aeb2cbe5122cef1912ad75385"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input",
          "description_stats": {
            "characters": 120,
            "utf8_bytes": 120,
            "o200k_estimate": 24,
            "sha256": "783ea374eaba01b1c7d453ff177ba9f27f45a6cb9c33a6f5fb1bed00251f00c7"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input_async",
          "description_stats": {
            "characters": 556,
            "utf8_bytes": 556,
            "o200k_estimate": 102,
            "sha256": "f7f47603a91513a78276c4091cd758ee99ca47e625bd7b0f4a8b305cebfa575c"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        }
      ]
    },
    {
      "case": "direct_only_functions",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 15634,
        "utf8_bytes": 15634,
        "o200k_estimate": 3842,
        "sha256": "bbfa0570c08436f3bbbce240d743812ce7f329ef213de3ce30fd6937216b1687"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12935,
            "utf8_bytes": 12935,
            "o200k_estimate": 3107,
            "sha256": "ade918d5ca6e742db2608593f4aa8608070f103c7fd0040def0a5ab02bb26222"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "list_mcp_resources",
            "list_mcp_resource_templates",
            "read_mcp_resource",
            "request_user_input",
            "request_user_input_async",
            "apply_patch",
            "clock",
            "curr_time"
          ]
        }
      ],
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
      "tool_description_stats": [
        {
          "name": "functions",
          "description_stats": {
            "characters": 0,
            "utf8_bytes": 0,
            "o200k_estimate": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "exec",
          "description_stats": {
            "characters": 5200,
            "utf8_bytes": 5200,
            "o200k_estimate": 1282,
            "sha256": "6ed8fae71b1b4cd46ef7a598a8038eb04ffacdb095fe910d221e70fdcd521471"
          },
          "referenced_methods": [
            "exec_command",
            "mcp__ologs__get_profile"
          ],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": true,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": true,
            "tool_search": false
          }
        },
        {
          "name": "wait",
          "description_stats": {
            "characters": 769,
            "utf8_bytes": 769,
            "o200k_estimate": 181,
            "sha256": "582eb96e50ee4481cf30b33ad2358e7e24e7368aeb2cbe5122cef1912ad75385"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "list_mcp_resources",
          "description_stats": {
            "characters": 238,
            "utf8_bytes": 238,
            "o200k_estimate": 40,
            "sha256": "1aa9c29d996c24678f1b5874625e38a88ff3a55ec9045e962c45966ad0a2f819"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "list_mcp_resource_templates",
          "description_stats": {
            "characters": 300,
            "utf8_bytes": 300,
            "o200k_estimate": 48,
            "sha256": "d526b412c36fa13f2086fc3445afc5d0551b6034149b81df611fe0981512ea07"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "read_mcp_resource",
          "description_stats": {
            "characters": 83,
            "utf8_bytes": 83,
            "o200k_estimate": 16,
            "sha256": "cd9ae972c351ecec00064fb69205c739bcee77f7c6569e033f0f55112c1ba576"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input",
          "description_stats": {
            "characters": 120,
            "utf8_bytes": 120,
            "o200k_estimate": 24,
            "sha256": "783ea374eaba01b1c7d453ff177ba9f27f45a6cb9c33a6f5fb1bed00251f00c7"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input_async",
          "description_stats": {
            "characters": 556,
            "utf8_bytes": 556,
            "o200k_estimate": 102,
            "sha256": "f7f47603a91513a78276c4091cd758ee99ca47e625bd7b0f4a8b305cebfa575c"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "apply_patch",
          "description_stats": {
            "characters": 108,
            "utf8_bytes": 108,
            "o200k_estimate": 29,
            "sha256": "1d2e0992b289d9389b4e765287dd932db0b2937cb4abfe422d6323c717293ebe"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": true,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "clock",
          "description_stats": {
            "characters": 38,
            "utf8_bytes": 38,
            "o200k_estimate": 8,
            "sha256": "f287aff2056ea5b9b6134dac7af8e75cd59d5417950ab73190c1b0e5c54dc211"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "curr_time",
          "description_stats": {
            "characters": 31,
            "utf8_bytes": 31,
            "o200k_estimate": 7,
            "sha256": "4d309e80bc8991f8f95bf9a437d7e7d431573adc7245cae9050c62dd45470eb4"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        }
      ]
    },
    {
      "case": "exclude_both_with_enabled_false",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": {
        "initialize": 1,
        "initialized": 1,
        "skills/list": 1,
        "thread/start": 1,
        "turn/start": 1
      },
      "input_stats": {
        "characters": 13279,
        "utf8_bytes": 13279,
        "o200k_estimate": 3278,
        "sha256": "997b19e0ff3471570f9fc32f473f85cdf6e93f15eb81e38fb722635422e8580c"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 9935,
            "utf8_bytes": 9935,
            "o200k_estimate": 2426,
            "sha256": "e3a1fde6117036f528d56c9f532e873ed6f7b6db7da5fc63a8a21867dc674577"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
      "markers": {
        "additional_tools": true,
        "functions.exec": false,
        "functions.wait": false,
        "request_user_input": true,
        "apply_patch": false,
        "create_goal": false,
        "update_goal": false,
        "get_goal": false,
        "list_mcp_resources": false,
        "skills_instructions": false,
        "SKILL.md": false,
        "environment_context": true,
        "permissions instructions": true,
        "collaboration_mode": true
      },
      "tool_description_stats": [
        {
          "name": "functions",
          "description_stats": {
            "characters": 0,
            "utf8_bytes": 0,
            "o200k_estimate": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "exec",
          "description_stats": {
            "characters": 5200,
            "utf8_bytes": 5200,
            "o200k_estimate": 1282,
            "sha256": "6ed8fae71b1b4cd46ef7a598a8038eb04ffacdb095fe910d221e70fdcd521471"
          },
          "referenced_methods": [
            "exec_command",
            "mcp__ologs__get_profile"
          ],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": true,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": true,
            "tool_search": false
          }
        },
        {
          "name": "wait",
          "description_stats": {
            "characters": 769,
            "utf8_bytes": 769,
            "o200k_estimate": 181,
            "sha256": "582eb96e50ee4481cf30b33ad2358e7e24e7368aeb2cbe5122cef1912ad75385"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input",
          "description_stats": {
            "characters": 120,
            "utf8_bytes": 120,
            "o200k_estimate": 24,
            "sha256": "783ea374eaba01b1c7d453ff177ba9f27f45a6cb9c33a6f5fb1bed00251f00c7"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        },
        {
          "name": "request_user_input_async",
          "description_stats": {
            "characters": 556,
            "utf8_bytes": 556,
            "o200k_estimate": 102,
            "sha256": "f7f47603a91513a78276c4091cd758ee99ca47e625bd7b0f4a8b305cebfa575c"
          },
          "referenced_methods": [],
          "namespace_words": {
            "functions": false,
            "clock": false,
            "exec_command": false,
            "write_stdin": false,
            "apply_patch": false,
            "mcp": false,
            "tool_search": false
          }
        }
      ]
    },
    {
      "case": "codex_exec_current",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": null,
      "input_stats": {
        "characters": 14826,
        "utf8_bytes": 14826,
        "o200k_estimate": 3708,
        "sha256": "a1dbd3416eaace59e399e89b85ff94893875e2e041752863189b36400ab41095"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 12202,
            "utf8_bytes": 12202,
            "o200k_estimate": 2985,
            "sha256": "e9625fceceaba07ac4ac47210ac47bc795d816b9c8dc8692a36ad5096134416c"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
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
      "tool_description_stats": null
    },
    {
      "case": "codex_exec_excluded",
      "completed": true,
      "real_inference_calls": 0,
      "session_closed": true,
      "rollout_files": 0,
      "sent": null,
      "input_stats": {
        "characters": 12559,
        "utf8_bytes": 12559,
        "o200k_estimate": 3145,
        "sha256": "6fe9cb4b9fddbd1192796de1295787c6b4453202b03bd3f427f281b4378c853a"
      },
      "additional_tools": [
        {
          "stats": {
            "characters": 9935,
            "utf8_bytes": 9935,
            "o200k_estimate": 2426,
            "sha256": "e3a1fde6117036f528d56c9f532e873ed6f7b6db7da5fc63a8a21867dc674577"
          },
          "names": [
            "functions",
            "exec",
            "wait",
            "request_user_input",
            "request_user_input_async"
          ]
        }
      ],
      "markers": {
        "additional_tools": true,
        "functions.exec": false,
        "functions.wait": false,
        "request_user_input": true,
        "apply_patch": false,
        "create_goal": false,
        "update_goal": false,
        "get_goal": false,
        "list_mcp_resources": false,
        "skills_instructions": false,
        "SKILL.md": false,
        "environment_context": true,
        "permissions instructions": true,
        "collaboration_mode": true
      },
      "tool_description_stats": null
    }
  ],
  "claude_mock": [
    {
      "case": "current_0910",
      "completed": true,
      "seconds": 0.4642,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 521,
            "o200k_estimate": 118,
            "sha256": "32dd9e0d710386beb14a4503f252b16ad64db5f52179c45c858e180bf839c038"
          },
          "messages": {
            "characters": 1421,
            "o200k_estimate": 379,
            "sha256": "f59414781f942227aaa01c868a199f9fdb432401e496ea023625f5779595a157"
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
          }
        }
      ]
    },
    {
      "case": "disable_skills",
      "completed": true,
      "seconds": 0.3063,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 521,
            "o200k_estimate": 118,
            "sha256": "32dd9e0d710386beb14a4503f252b16ad64db5f52179c45c858e180bf839c038"
          },
          "messages": {
            "characters": 1421,
            "o200k_estimate": 376,
            "sha256": "d32339d209eee4178429f1dc0cbc89b3acbe6f13fbc514e9e3d56b334bb17e16"
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
          }
        }
      ]
    },
    {
      "case": "bare_mock_only",
      "completed": true,
      "seconds": 0.2496,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 521,
            "o200k_estimate": 118,
            "sha256": "32dd9e0d710386beb14a4503f252b16ad64db5f52179c45c858e180bf839c038"
          },
          "messages": {
            "characters": 176,
            "o200k_estimate": 44,
            "sha256": "588b77c737ef69eaa9a5a23918f4b1b58338849134e4341bb91262555dc1ef21"
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
            "system-reminder": false,
            "You are Claude Code": false,
            "Bash": false,
            "TodoWrite": false,
            "TaskCreate": false,
            "EndConversation": false
          }
        }
      ]
    },
    {
      "case": "default_system_control",
      "completed": true,
      "seconds": 0.2889,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 13897,
            "o200k_estimate": 2901,
            "sha256": "fb4f9a7c34413780b99ea8c80337659b8cf550c46b2daa23eba5b2cbcdfebc06"
          },
          "messages": {
            "characters": 1421,
            "o200k_estimate": 380,
            "sha256": "5ef927e16935ce6367f5119d10d48db79fe4c7416750bda59687b93ab915439b"
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
              "characters": 13511,
              "o200k_estimate": 2750,
              "sha256": "f189f6b8525516cb9ba4bf9aef384bc2cf3408cbefeb98d6545331be57e78f39"
            }
          ],
          "markers": {
            "CLAUDE.md": true,
            "SKILL.md": false,
            "available_skills": false,
            "system-reminder": true,
            "You are Claude Code": false,
            "Bash": false,
            "TodoWrite": false,
            "TaskCreate": false,
            "EndConversation": false
          }
        }
      ]
    },
    {
      "case": "default_system_tools_control",
      "completed": true,
      "seconds": 0.2936,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 14582,
            "o200k_estimate": 3048,
            "sha256": "3ef00fc961c2c147e9ff5c3d1da004f1d870816ba3152274989ee85cce12dd54"
          },
          "messages": {
            "characters": 9931,
            "o200k_estimate": 2335,
            "sha256": "3c99655a5c04a0d939ccd9a6fe847e75900c389c525631e1d35aa75f574aa8ee"
          },
          "tools": {
            "characters": 32287,
            "o200k_estimate": 7276,
            "sha256": "dcd21565c1ba5da5aac8dc8d32dd1e96b37f7ccea8f67ee797b5ad6a9e9e651f"
          },
          "tool_names": [
            "Agent",
            "Edit",
            "Glob",
            "Grep",
            "ListAgents",
            "Read",
            "ReportFindings",
            "ScheduleWakeup",
            "Skill",
            "ToolSearch",
            "DeferredToolPlaceholder",
            "Write"
          ],
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
              "characters": 14189,
              "o200k_estimate": 2893,
              "sha256": "3f77105d1ecda328ab2c212a330cf1fa967e525bd2906481b0d4eade047f736f"
            }
          ],
          "markers": {
            "CLAUDE.md": true,
            "SKILL.md": false,
            "available_skills": false,
            "system-reminder": true,
            "You are Claude Code": false,
            "Bash": true,
            "TodoWrite": false,
            "TaskCreate": true,
            "EndConversation": false
          }
        }
      ]
    },
    {
      "case": "current_decisions",
      "completed": true,
      "seconds": 0.2938,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 521,
            "o200k_estimate": 118,
            "sha256": "6a5d2ad0e6e78c17fc4fb105af6f16bcb511f4cd68496957f8f18b1b419fea06"
          },
          "messages": {
            "characters": 2257,
            "o200k_estimate": 546,
            "sha256": "ee645a79a2c8fd4d0f98600cbd22bbcae8043f366f53793f2c4a0f84aeaf410c"
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
          }
        }
      ]
    },
    {
      "case": "bare_decisions_mock_only",
      "completed": true,
      "seconds": 0.2388,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 521,
            "o200k_estimate": 118,
            "sha256": "6a5d2ad0e6e78c17fc4fb105af6f16bcb511f4cd68496957f8f18b1b419fea06"
          },
          "messages": {
            "characters": 1012,
            "o200k_estimate": 210,
            "sha256": "59811674b6a891806024804a47a3b0ae557b95e20703b78a7df8f513ca134cc0"
          },
          "tools": {
            "characters": 236,
            "o200k_estimate": 54,
            "sha256": "709508a6b510e67038276977a169c810b3f813a10685adedfec27aadba652fbc"
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
              "characters": 232,
              "o200k_estimate": 38,
              "sha256": "4a63c88a851dbf74e78d2d6bc59f130498316d371ed234e565758a1827581d1e"
            }
          ],
          "markers": {
            "CLAUDE.md": false,
            "SKILL.md": false,
            "available_skills": false,
            "system-reminder": false,
            "You are Claude Code": false,
            "Bash": false,
            "TodoWrite": false,
            "TaskCreate": false,
            "EndConversation": false
          }
        }
      ]
    },
    {
      "case": "skill_fixture_current",
      "completed": true,
      "seconds": 0.2381,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 521,
            "o200k_estimate": 118,
            "sha256": "32dd9e0d710386beb14a4503f252b16ad64db5f52179c45c858e180bf839c038"
          },
          "messages": {
            "characters": 1421,
            "o200k_estimate": 380,
            "sha256": "2b272f0616c80b65a07c83b158e664ba740a211e86081b291764f05d377a52c9"
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
            "EndConversation": false,
            "SYNTHETIC_SKILL_CATALOG_MARKER": false
          }
        }
      ]
    },
    {
      "case": "skill_fixture_disabled",
      "completed": true,
      "seconds": 0.3095,
      "real_inference_calls": 0,
      "raw_payload_saved": false,
      "fixture_auth_only": true,
      "routes": [
        "messages"
      ],
      "session_jsonl_files": 0,
      "owned_processes_closed": true,
      "captures": [
        {
          "system": {
            "characters": 521,
            "o200k_estimate": 118,
            "sha256": "32dd9e0d710386beb14a4503f252b16ad64db5f52179c45c858e180bf839c038"
          },
          "messages": {
            "characters": 1421,
            "o200k_estimate": 379,
            "sha256": "df4967f4f76fa4216af8e569b84b2c24385563d61d335a1f08b3809ffc07b1b8"
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
            "EndConversation": false,
            "SYNTHETIC_SKILL_CATALOG_MARKER": false
          }
        }
      ]
    }
  ],
  "codex_real": {
    "schema": 1,
    "transport": "direct native subscribed CLI; not public API or warm pool",
    "cli_version": "0.163.0-alpha.11",
    "model": "openai/gpt-6.1-sol",
    "concurrent_calls": 1,
    "failed_cli_calls_retried": 0,
    "production_settings_changed": false,
    "production_code_changed": false,
    "raw_content_events_or_credentials_saved": false,
    "rows": [
      {
        "arm": "current",
        "protocol": "chat",
        "started": true,
        "seconds": 3.3303,
        "completed": true,
        "valid": true,
        "actual_model_matches": true,
        "finish_stop": true,
        "usage": {
          "prompt_tokens": 3120,
          "completion_tokens": 6,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        }
      },
      {
        "arm": "excluded_namespaces",
        "protocol": "decisions",
        "started": true,
        "seconds": 5.7269,
        "completed": true,
        "valid": true,
        "actual_model_matches": true,
        "finish_stop": true,
        "usage": {
          "prompt_tokens": 2769,
          "completion_tokens": 16,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        }
      },
      {
        "arm": "excluded_namespaces",
        "protocol": "chat",
        "started": true,
        "seconds": 4.1645,
        "completed": true,
        "valid": true,
        "actual_model_matches": true,
        "finish_stop": true,
        "usage": {
          "prompt_tokens": 2630,
          "completion_tokens": 6,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 0
          }
        }
      },
      {
        "arm": "current",
        "protocol": "decisions",
        "started": true,
        "seconds": 5.0127,
        "completed": true,
        "valid": true,
        "actual_model_matches": true,
        "finish_stop": true,
        "usage": {
          "prompt_tokens": 3257,
          "completion_tokens": 42,
          "prompt_tokens_details": {
            "cached_tokens": 0
          },
          "completion_tokens_details": {
            "reasoning_tokens": 24
          }
        }
      }
    ],
    "production_settings_preserved": true,
    "all_key_rows_preserved": true,
    "personal_codex_config_preserved": true,
    "success": true
  },
  "codex_comparison": [
    {
      "protocol": "chat",
      "samples_per_arm": 1,
      "current_input": 3120,
      "candidate_input": 2630,
      "input_reduction_percent": 15.71,
      "current_seconds": 3.3303,
      "candidate_seconds": 4.1645
    },
    {
      "protocol": "decisions",
      "samples_per_arm": 1,
      "current_input": 3257,
      "candidate_input": 2769,
      "input_reduction_percent": 14.98,
      "current_seconds": 5.0127,
      "candidate_seconds": 5.7269
    }
  ],
  "claude_public": {
    "success": true,
    "version": "0.9.10-mac.1",
    "source_commit": "26ab468b157747f1de6ea5dc3e934874b2f6bedf",
    "rounds": 1,
    "inference_retries": 0,
    "concurrent_requests": 1,
    "resident": 2,
    "workers": 64,
    "temporary_key_revoked": true,
    "settings_preserved": true,
    "owner_keys_preserved": true,
    "rows": [
      {
        "round": 1,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "chat",
        "request_id": "4af2e427-2ffd-46e8-a6a0-6ee8bfeb5f86",
        "request_bytes": 120,
        "http": 200,
        "seconds": 2.9063,
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
        "completion_tokens": 60,
        "cost_usd": 0.000862,
        "cached_tokens": null,
        "reasoning_tokens": null,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 209,
          "cli_spawn_ms": 3,
          "cli_ready_ms": null,
          "inference_ms": 1648,
          "output_validation_ms": null,
          "total_ms": 1869
        },
        "passed": true,
        "local_usage_metadata": {
          "prompt_tokens": 562,
          "completion_tokens": 60,
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": null,
          "calls_started": 1,
          "calls_completed": 1,
          "billing_complete": 1
        }
      },
      {
        "round": 1,
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "decisions",
        "request_id": "13f5504f-0ecb-4d26-807b-49e2fc4298e9",
        "request_bytes": 156,
        "http": 200,
        "seconds": 7.133,
        "response_valid": true,
        "execution": {
          "warm_hits": 0,
          "cold_starts": 1
        },
        "lease_valid": true,
        "receipt_http": 200,
        "receipt_complete": true,
        "cost_matches": true,
        "prompt_tokens": 3474,
        "completion_tokens": 618,
        "cost_usd": 0.006564,
        "cached_tokens": null,
        "reasoning_tokens": null,
        "timings_ms": {
          "validation_ms": 0,
          "schema_wait_ms": null,
          "schema_execution_ms": null,
          "queue_wait_ms": 0,
          "provider_setup_ms": 154,
          "cli_spawn_ms": 2,
          "cli_ready_ms": null,
          "inference_ms": 5851,
          "output_validation_ms": 0,
          "total_ms": 6013
        },
        "passed": true,
        "local_usage_metadata": {
          "prompt_tokens": 3474,
          "completion_tokens": 618,
          "cached_tokens": 0,
          "cache_write_tokens": 0,
          "reasoning_tokens": null,
          "calls_started": 1,
          "calls_completed": 1,
          "billing_complete": 1
        }
      }
    ],
    "summary": [
      {
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "chat",
        "requests": 1,
        "passed": 1,
        "median_seconds": 2.9063,
        "max_seconds": 2.9063
      },
      {
        "model": "anthropic/claude-haiku-4.5",
        "protocol": "decisions",
        "requests": 1,
        "passed": 1,
        "median_seconds": 7.133,
        "max_seconds": 7.133
      }
    ]
  },
  "claude_direct_turn_metadata": {
    "schema": 1,
    "real_inference_cli_calls": 1,
    "transport": "direct subscribed native CLI; no public relay",
    "cli_version": "2.1.306",
    "model": "anthropic/claude-haiku-4.5",
    "raw_content_events_or_credentials_saved": false,
    "events": {
      "system": 8,
      "assistant": 4,
      "rate_limit_event": 1,
      "user": 2,
      "result": 1
    },
    "assistant_messages": [
      {
        "usage": {
          "input_tokens": 1486,
          "cache_creation_input_tokens": 0,
          "cache_read_input_tokens": 0,
          "output_tokens": 1
        },
        "content_types": {
          "text": 1
        },
        "text_characters": 25,
        "tool_names": [],
        "stop_reason": null,
        "usage_scope": "latest assistant event; output may be partial; CLI aggregate is authoritative"
      },
      {
        "usage": {
          "input_tokens": 2180,
          "cache_creation_input_tokens": 0,
          "cache_read_input_tokens": 0,
          "output_tokens": 4
        },
        "content_types": {
          "tool_use": 1
        },
        "text_characters": 0,
        "tool_names": [
          "StructuredOutput"
        ],
        "stop_reason": null,
        "usage_scope": "latest assistant event; output may be partial; CLI aggregate is authoritative"
      }
    ],
    "num_turns": 3,
    "usage": {
      "input_tokens": 3666,
      "cache_creation_input_tokens": 0,
      "cache_read_input_tokens": 0,
      "output_tokens": 801
    },
    "structured_output_present": true,
    "success": true,
    "bridge_usage": {
      "prompt_tokens": 3666,
      "completion_tokens": 801,
      "prompt_tokens_details": {
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "cache_write_1h_tokens": 0
      }
    },
    "seconds": 7.6797,
    "observed_unique_assistant_messages": 2,
    "assistant_input_sum_matches_cli_total": true
  },
  "pre_inference_helper_failure": {
    "schema": 1,
    "real_inference_cli_calls": 0,
    "transport": "direct subscribed native CLI; no public relay",
    "cli_version": "2.1.306",
    "model": "anthropic/claude-haiku-4.5",
    "raw_content_events_or_credentials_saved": false,
    "events": {},
    "assistant_messages": [],
    "success": false,
    "error_category": "AttributeError",
    "seconds": 0.1233,
    "phase": "read-only auth metadata parsing in diagnostic helper, before inference"
  },
  "real_usage_total": {
    "inference_cli_calls": 7,
    "prompt_tokens": 19478,
    "completion_tokens": 1549
  },
  "production_proof": {
    "installed_version": "0.9.10-mac.1",
    "source_commit": "26ab468b157747f1de6ea5dc3e934874b2f6bedf",
    "active_owner_keys": 3,
    "all_key_rows": 52,
    "health": {
      "ok": true,
      "version": "0.9.10-mac.1",
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
        "created": 18,
        "warm_hits": 0,
        "cold_starts": 2,
        "refill_failures": 0,
        "paused": false,
        "waiting_leases": 0
      },
      "warm_supported_providers": [
        "codex"
      ]
    },
    "service_stopped_or_reconfigured": false,
    "provider_login_changed": false,
    "production_code_changed": false,
    "worker_deployed": false
  },
  "script_sha256": {
    "ltbb-issue46-followup-codex.py": "6f3dccd32821fce56d7f4c51569cd33a6eb43d5b365c0b34a06045ba954bef09",
    "ltbb-issue46-codex-detail.py": "dfca574e9a91581ab8957dd130c86f8f94d0e7e9cb27f6e442932945d022f27e",
    "ltbb-issue46-codex-candidate.py": "dcf0ec289247c8d681de0ceeec1d43f5baac821b14e02b939b38d1ab3a7345a8",
    "ltbb-issue46-codex-exec.py": "d086527a4fafa477253a2eb9a44f52db5e107c61a61de21b5ce3563e35284f0c",
    "ltbb-issue46-followup-claude.py": "51f49f27468df7be39df5d3442ad52d729eabd3c354e2aaac81c7d221625bbf9",
    "ltbb-issue46-claude-decisions.py": "9a685130a5ca5bd0d67f3d4f09fe5f93884501e51d20333b3c82a1147ad651c8",
    "ltbb-issue46-claude-skill-fixture.py": "c1ea5c8ccb2467703d5af7c3d7a5f046cebae30fa01d12405e8993bb5619f688",
    "ltbb-issue46-followup-real-codex.py": "758f6ccd591c14825356e272bd4ed4c408b7bc9fae380c2f64a26ddf58fcf915",
    "ltbb-issue46-claude-real-turns.py": "9bc83ab6bb690dc7f049e96574ae4e269c80e1afdf15c335f045b4d65a3e354c"
  }
}
```
