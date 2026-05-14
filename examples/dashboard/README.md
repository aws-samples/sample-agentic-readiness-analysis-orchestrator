# Analysis Dashboard

Interactive HTML dashboards for visualizing ARA and MOD analysis results.

| File | Description |
|------|-------------|
| `index.html` | Landing page (redirects to ARA dashboard) |
| `agentic-readiness.html` | ARA dashboard -- run selector, readiness profiles, cross-cutting analysis, pilot ranking, program recommendations, delta comparison |
| `modernization.html` | MOD dashboard -- category scores, pathways, roadmap, radar chart, technology stack |
| `bridge.html` | Bridge dashboard -- shared remediation mapping, agentic readiness delta, MOD readiness gates |
| `bpmn-opportunity.html` | BAO dashboard -- agent opportunity classification, dependency discovery, implementation waves, Bedrock cost forecast |
| `cloudformation.yaml` | CloudFormation template for S3 + CloudFront hosting |

## Viewing Locally

Open `index.html` in a browser — no build step needed.

## Deployed Version

Live at: **https://d2fplme21ym2t.cloudfront.net**

## Deploying Updates

```bash
aws s3 sync dashboard/ s3://936068047509-dashboard/ \
  --delete \
  --exclude "cloudformation.yaml" \
  --exclude "README.md" \
  --content-type "text/html"

aws cloudfront create-invalidation \
  --distribution-id E36HDAABDBBG66 \
  --paths "/*"
```

## Data Source

Dashboard data comes from the Online Boutique portfolio analysis (11 microservices from Google's microservices-demo). The ARA dashboard supports multiple analysis runs with delta comparison between any two runs.
