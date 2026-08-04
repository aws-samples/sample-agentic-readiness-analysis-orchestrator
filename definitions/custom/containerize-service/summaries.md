# Summary

Containerizes a legacy web service by generating a Dockerfile, .dockerignore,
and Kubernetes deployment + service manifests. Additive and non-destructive —
adds container artifacts without touching application source or dependencies.
Pairs with the MODA "service is not containerized" finding. Detects the runtime
(Node/Ruby/Java), listen port, and start command, pins a supported base image,
runs as non-root, and opens a reviewable PR describing assumptions and follow-up
hardening.
