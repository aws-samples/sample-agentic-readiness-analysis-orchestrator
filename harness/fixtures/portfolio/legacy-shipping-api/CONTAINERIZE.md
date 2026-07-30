# Containerization Summary: shipping-rate-api

## Detected Stack

| Property | Value |
|----------|-------|
| Language | Node.js |
| Declared Engine | 0.10.x (upgraded to Node 18 for container runtime) |
| Framework | Express 3.4.8 |
| Database | MongoDB (via `mongodb` 1.4.7 driver) |
| Port | 8080 |
| Health Endpoint | None (TCP socket check used for probes) |

## Generated Artifacts

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build: installs deps in build stage, runs as non-root in slim runtime stage |
| `k8s/namespace.yaml` | Dedicated Kubernetes namespace |
| `k8s/configmap.yaml` | Non-secret environment configuration (MONGO_URL, PORT) |
| `k8s/deployment.yaml` | Deployment with 2 replicas, resource limits, probes, hardened securityContext |
| `k8s/service.yaml` | ClusterIP Service exposing port 8080 |

## Build and Push to Amazon ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

# Build the image
docker build -t shipping-rate-api .

# Tag for ECR
docker tag shipping-rate-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/shipping-rate-api:latest

# Push to ECR
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/shipping-rate-api:latest
```

## Deploy to EKS

```bash
# Update the image reference in k8s/deployment.yaml to your ECR URI, then:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

# Create the required secret for the API key
kubectl create secret generic shipping-rate-api-secret \
  --namespace=shipping-rate-api \
  --from-literal=api-key='<your-api-key>'
```

## Environment-Specific Values to Configure

| Variable | Location | Description |
|----------|----------|-------------|
| `MONGO_URL` | `k8s/configmap.yaml` | MongoDB connection string for your environment |
| `api-key` | Kubernetes Secret `shipping-rate-api-secret` | API authentication key |
| Image URI | `k8s/deployment.yaml` | Replace `shipping-rate-api:latest` with your ECR URI |

## Assumptions and Notes

1. **Node.js version**: The application declares `node: 0.10.x` in `package.json` but the Dockerfile uses Node 18 (current LTS) since Node 0.10 is EOL and unavailable as a supported Docker image. The `--ignore-engines` flag is used during `npm install`. The application may require minor adjustments to run on modern Node.js.
2. **No health endpoint**: The application has no dedicated health route (all endpoints require an API key), so TCP socket probes are used for Kubernetes readiness/liveness checks.
3. **Hardcoded values**: The source code has hardcoded `MONGO_URL` and `API_KEY`. The Kubernetes manifests externalize these via ConfigMap and Secret, but the application source itself would need modification to read from environment variables for full benefit.
4. **Read-only filesystem**: The Deployment sets `readOnlyRootFilesystem: true`. If the application writes temp files at runtime, this may need adjustment.
5. **Dependencies**: The legacy dependencies (`express@3.4.8`, `mongodb@1.4.7`) are extremely outdated and have known vulnerabilities. A dependency upgrade is strongly recommended as a follow-up.
