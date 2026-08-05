# Soul Memory v3.6.3

## Fixes

1. Clean injected memory focus before prependContext injection
   - strips heartbeat boilerplate
   - strips tool/edit success text
   - strips untrusted metadata envelopes

2. Filter noisy memory entries from injection
   - avoids polluting User / Config buckets with internal tool logs

3. Keep existing search/index pipeline fixes
   - real index building from v3.6.2
   - reliable query extraction and JSON CLI from v3.6.x

## Result

Injected `Memory Focus` is cleaner and more likely to contain real semantic context instead of heartbeat/tool noise.
