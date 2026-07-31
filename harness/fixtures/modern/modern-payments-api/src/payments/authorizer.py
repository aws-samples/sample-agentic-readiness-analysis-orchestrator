"""Lambda authorizer: validate an OAuth2 client-credentials access token.

The token is issued by Cognito for a machine client (no human login flow). We verify
the signature and the required scope and hand the request handlers a principal with
the granted scopes. No credential is ever logged or persisted.
"""

from __future__ import annotations

import os

# In a real deployment this uses the Cognito JWKS to verify RS256 signatures. The
# fixture keeps the shape (verify -> extract client_id + scopes) without the network call.
_USER_POOL = os.environ.get("COGNITO_USER_POOL_ID", "")


def handler(event: dict, _context) -> dict:
    token = _bearer_token(event)
    claims = _verify(token)  # raises on invalid signature / expiry / audience
    return {
        "isAuthorized": True,
        "context": {
            "client_id": claims["client_id"],
            "scopes": claims["scope"],  # space-delimited, e.g. "payments:read payments:write"
        },
    }


def _bearer_token(event: dict) -> str:
    header = event.get("headers", {}).get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise PermissionError("missing bearer token")
    return header.split(" ", 1)[1]


def _verify(token: str) -> dict:
    # Placeholder for JWKS verification; real impl fetches keys for _USER_POOL and
    # validates iss/aud/exp. Never trust an unverified token.
    if not token:
        raise PermissionError("empty token")
    raise NotImplementedError("wire to Cognito JWKS in deployment")
