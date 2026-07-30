# Shipping Rate API

Legacy internal REST API that returns shipping rate quotes. Built in 2013 on
Node.js 0.10 with Express 3, backed by MongoDB 2.4, running under forever
on a single EC2 instance.

## Architecture
- **Runtime**: Node.js 0.10.x (long EOL), Express 3.x
- **Database**: MongoDB 2.4 (EOL) on the same EC2 instance
- **Process Manager**: `forever` (no systemd, no containers)
- **Deployment**: git pull + `forever restart` over SSH
- **Auth**: A shared static API key checked in a header

## Known Issues
- Node 0.10 and Express 3 are long unsupported; transitive CVEs everywhere
- `npm install` fails against the current registry (old deps unpublished)
- Callback-style code, no promises/async; deeply nested error handling
- MongoDB 2.4 has no auth enabled and binds to 0.0.0.0
- Static API key hardcoded in source
- No tests; no linting; `node_modules` partially committed
- Single instance; `forever` restart drops in-flight requests
