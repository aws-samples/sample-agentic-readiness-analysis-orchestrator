# Containerization Summary — legacy-pricing-cgi

## Detected Stack

| Property | Value |
|----------|-------|
| Language | C++ (pre-C++11) |
| Build System | Makefile with g++ |
| Framework | Apache CGI binary |
| Artifact | `pricing.cgi` (compiled executable) |
| Port | 8080 |
| Health Endpoint | `/cgi-bin/pricing.cgi?sku=HEALTH&qty=1` |
| Config | `/etc/pricing/rules.dat` (pipe-delimited flat file) |

## Generated Artifacts

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build: compiles with GCC 12, serves via Apache httpd 2.4 on Alpine |
| `k8s/namespace.yaml` | Dedicated Kubernetes namespace |
| `k8s/configmap.yaml` | Non-secret environment configuration |
| `k8s/deployment.yaml` | Deployment with 2 replicas, probes, resource limits, hardened security context |
| `k8s/service.yaml` | ClusterIP Service exposing port 8080 |

## Build & Push to Amazon ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

# Build the image
docker build -t legacy-pricing-cgi:latest .

# Tag for ECR
docker tag legacy-pricing-cgi:latest \
  <account-id>.dkr.ecr.<region>.amazonaws.com/legacy-pricing-cgi:latest

# Push
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/legacy-pricing-cgi:latest
```

## Deploy to EKS

```bash
# Update the image reference in k8s/deployment.yaml to your ECR URI, then:
kubectl apply -f k8s/
```

This applies the namespace, configmap, deployment, and service in one command.

## Pricing Rules Configuration

The application reads pricing data from `/etc/pricing/rules.dat`. In the
container image a sample file is baked in. For production, mount the real
rules file via a ConfigMap or a persistent volume:

```yaml
volumes:
  - name: pricing-rules
    configMap:
      name: pricing-rules-data
volumeMounts:
  - name: pricing-rules
    mountPath: /etc/pricing
```

## Assumptions & Operator Actions

1. **Image URI**: Replace `legacy-pricing-cgi:latest` in `k8s/deployment.yaml`
   with your actual ECR image URI.
2. **Pricing rules**: The baked-in `/etc/pricing/rules.dat` contains a sample
   entry. Mount your production rules file as described above.
3. **Ingress**: The Service is `ClusterIP`. To expose externally, create an
   Ingress resource using the AWS ALB Ingress Controller (example in
   `k8s/service.yaml` comments).
4. **Secrets**: No secrets are required by this application. If future
   integrations require credentials, use Kubernetes Secrets (not the ConfigMap).
5. **GCC version**: The original code required GCC 3.4. The Dockerfile uses
   GCC 12 which compiles this simple C++ code without issues. No source
   modifications were made.
