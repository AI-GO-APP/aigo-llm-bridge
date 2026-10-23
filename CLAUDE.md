# Project setup

Read [AGENTS.md](AGENTS.md) before setting up or changing this project. Deployment is exclusively user-owned BYO Cloudflare; there is no publisher-operated relay.

For installation or Cloudflare pairing, read [skills/byo-cloudflare/SKILL.md](skills/byo-cloudflare/SKILL.md). Keep device identity, endpoint and client API keys independent of Claude Code/Codex account login. Do not alter the user's active CLI login or interact with their windows.

Product requirements, architecture, schema, API, design, decisions and acceptance are versioned in [docs/README.md](docs/README.md). Update affected documents in the same PR; run `python tools/check_product_docs.py`. Windows Setup uses current/aigo-bridge.exe; do not assume the legacy ZIP layout.

For macOS use the current source Release and [Mac install/update/release guide](docs/MACOS-RELEASE.md), not historical desktop packages. For both systems use [the installation prompt](docs/AI-AGENT-SETUP.md). Keep the same installed profile on updates; do not redeploy its Worker.
