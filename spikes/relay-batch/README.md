# Bounded batch polling research

Research only; does not modify, install or deploy the production Worker／Python Relay. No real device credentials or models are used. [Mac findings and limits](../../docs/qa/2026-10-24-macos-optimization-probes.md).

`candidate.mjs` reads the current Worker source and applies three asserted in-memory changes: opt-in `batch_size` 1–8, FIFO extraction under 6,100,000 encoded bytes, and a compatible batch envelope. Old agents still get `request`; the proposed decoder also accepts old Workers. A source-shape mismatch fails instead of silently producing a different candidate. Python Relay integration, a reusable HTTPS transport and real Cloudflare deployment are not implemented here.

```sh
node --test spikes/relay-batch/candidate.test.mjs spikes/relay-batch/candidate.regression.test.mjs
node spikes/relay-batch/probe.mjs /tmp/relay-batch-metadata.json
```

Tests replay the unchanged production Worker regression suite and add FIFO／at-most-once, legacy compatibility, waiting-poll wakeup, invalid sizes, encoded-byte bounds, restart/no replay and malformed decoder cases. Test bodies exist only in RAM. The benchmark buffers synthetic requests before polling and imposes 100／500 ms RTT; responses to `/agent/result` are immediate local calls. It measures dispatch only, not real network or model latency. Default rounds are three pairs at 16／64 requests and 100 ms RTT, plus one pair at 64／500 ms. Baseline/candidate order alternates. No result predicts a production speedup percentage.

Before adoption, keep poll and result connections separate so the 20-second long poll cannot block responses; honor existing proxy／TLS／redirect rules, bound result connections, preserve device/profile identity and 64＋8 budgets, and never replay dispatched work after uncertain delivery. Larger batches may expose real CLI concurrency and resource costs previously masked by serial delivery. Verify actual Python Relay, fault handling and original public endpoint with the fixed #39 gates before declaring a release.
