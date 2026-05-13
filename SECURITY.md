# Security Guidelines

## Overview

This document provides security guidance for using the Agentic Readiness Analysis framework. While the framework itself consists of transformation definitions and orchestration documentation, proper security practices are essential when executing assessments.

---

## Security Responsibilities

### User Responsibilities

- **Repository Access Control**: Only assess repositories you have authorization to analyze
- **Credential Management**: Use Git credential managers (not hardcoded credentials)
- **AWS Credentials**: Configure AWS CLI with IAM roles/profiles (never hardcode)
- **Report Handling**: Treat assessment reports as confidential - they contain architecture details
- **Environment Security**: Run assessments in trusted development/analysis environments only

### AWS Transform CLI Responsibilities

- Sandboxed execution environment for code analysis
- No code execution during assessment (read-only analysis)
- TLS encryption for all AWS API communications
- CloudTrail logging of all Transform API calls

### Kiro IDE Responsibilities

- Secure subagent spawning with isolated contexts
- File system access controls for repository operations
- Validation of portfolio configuration inputs
- Cleanup of temporary execution artifacts

---

## Security Best Practices

### 1. Repository URL Validation

When using `repository_url` in portfolio configurations, ensure URLs are from trusted sources:

```yaml
# ✅ GOOD - Trusted sources
repositories:
  - name: "my-service"
    repository_url: "https://github.com/my-org/my-service.git"
    path: "./services/my-service"

# ❌ AVOID - Untrusted or suspicious URLs
repositories:
  - name: "suspicious"
    repository_url: "https://random-site.com/repo.git"  # Unknown source
```

**Validation checklist:**
- Use HTTPS or SSH protocols only
- Verify domain ownership
- Check repository authenticity before cloning
- Use organization-approved Git servers

### 2. Credential Protection

**Git Credentials:**
```bash
# ✅ GOOD - Use credential managers
git config --global credential.helper osxkeychain  # macOS
git config --global credential.helper manager      # Windows
git config --global credential.helper cache        # Linux

# ✅ GOOD - Use SSH keys with passphrase
ssh-keygen -t ed25519 -C "your_email@example.com"
ssh-add ~/.ssh/id_ed25519

# ❌ NEVER - Hardcode credentials in configs
repository_url: "https://<username>:<token>@github.com/repo.git"  # NEVER DO THIS
```

**AWS Credentials:**
```bash
# ✅ GOOD - Use AWS CLI profiles
aws configure --profile assessment-user
export AWS_PROFILE=assessment-user

# ✅ GOOD - Use IAM roles (EC2, ECS, Lambda)
# No explicit credentials needed

# ❌ NEVER - Hardcode in environment or configs
export AWS_ACCESS_KEY_ID=AKIA...  # NEVER commit this
```

### 3. Portfolio Configuration Security

**Sensitive Data Handling:**
```yaml
# ✅ GOOD - No sensitive data in configs
portfolio_name: "ecommerce-platform"
goal: "agentic-ai-enablement"
goal_context: "Building customer-facing AI agents"

preferences:
  prefer: ["eks", "aurora"]
  avoid: ["self-managed-kafka"]

# ❌ AVOID - Sensitive business details
goal_context: "Migrating from Oracle (license expires Q3) to save $500K annually"  # Too specific
context: "Service handles 10M credit card transactions daily"  # Sensitive metrics
```

**Configuration file permissions:**
```bash
# Restrict access to portfolio configs
chmod 600 portfolio-config.yaml
chmod 600 .atx-config-*.yaml

# Store in version control with appropriate .gitignore
echo "*.atx-config-*.yaml" >> .gitignore
echo "portfolio-config.yaml" >> .gitignore  # If it contains sensitive data
```

### 4. Report Security

Assessment reports contain sensitive architecture and security findings. Protect them appropriately:

```bash
# Set restrictive permissions on report directories
chmod 700 agentic-readiness-assessment/

# Encrypt reports at rest (optional but recommended)
gpg --encrypt --recipient your-key agentic-readiness-assessment/*.md

# Use AWS KMS for encryption (if storing in S3)
aws s3 cp agentic-readiness-assessment/ s3://bucket/reports/ \
  --recursive \
  --sse aws:kms \
  --sse-kms-key-id alias/assessment-reports
```

**Report handling guidelines:**
- Treat as "Confidential" or "Internal" classification
- Do not commit to public repositories
- Share via secure channels only (encrypted email, secure file sharing)
- Implement retention policies (delete after modernization completes)
- Redact sensitive details before sharing with external parties

### 5. Input Validation

When creating portfolio configurations, validate all inputs:

**Goal validation:**
```yaml
# ✅ GOOD - Use predefined goals
goal: "agentic-ai-enablement"  # Valid
goal: "cloud-native-modernization"  # Valid
goal: "cost-optimization"  # Valid
goal: "general-readiness"  # Valid

# ⚠️ WARNING - Unrecognized goals default to general-readiness
goal: "custom-goal"  # Will trigger warning and default
```

**Path validation:**
```yaml
# ✅ GOOD - Relative paths within workspace
repositories:
  - name: "service-a"
    path: "./services/service-a"

# ❌ AVOID - Absolute paths or path traversal
repositories:
  - name: "suspicious"
    path: "/etc/passwd"  # Absolute path - security risk
  - name: "traversal"
    path: "../../sensitive-data"  # Path traversal attempt
```

### 6. AWS IAM Permissions

Use least privilege IAM policies for AWS Transform CLI:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "transform:ExecuteTransformation",
        "transform:ListTransformations",
        "transform:GetTransformation"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/transform/*"
    }
  ]
}
```

**Do NOT grant:**
- `transform:CreateTransformation` (unless publishing definitions)
- `transform:DeleteTransformation` (unless managing definitions)
- `bedrock:*` (overly broad)
- `*:*` (never use wildcard permissions)

### 7. Audit Logging

Enable comprehensive logging for security monitoring:

**AWS CloudTrail:**
```bash
# Verify CloudTrail is enabled
aws cloudtrail describe-trails

# Check for Transform API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::Transform::Transformation \
  --max-results 50
```

**Local execution logs:**
```bash
# Kiro IDE logs assessment executions
# Review logs for anomalous patterns:
# - Unexpected repository access
# - Failed authentication attempts
# - Unusual assessment durations
# - Error patterns indicating attacks
```

### 8. Secure Assessment Execution

**Environment isolation:**
```bash
# Run assessments in isolated environments
# ✅ GOOD - Dedicated assessment workstation
# ✅ GOOD - Ephemeral EC2 instance with IAM role
# ✅ GOOD - Container with mounted credentials

# ❌ AVOID - Production servers
# ❌ AVOID - Shared developer machines with production access
# ❌ AVOID - Environments with production credentials
```

**Network security:**
```bash
# Use VPN or private network for repository cloning
# Verify TLS certificates for Git operations
git config --global http.sslVerify true

# Use SSH for private repositories
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

---

## Threat Scenarios and Mitigations

### Scenario 1: Malicious Repository Content

**Threat**: Assessed repository contains malicious file names or content designed to exploit the assessment process.

**Mitigations:**
- AWS Transform uses sandboxed execution (no code execution)
- Read-only repository access during assessment
- Path validation prevents directory traversal
- File system access restrictions limit blast radius

**User actions:**
- Only assess repositories from trusted sources
- Review repository contents before assessment
- Use separate assessment environment (not production)

### Scenario 2: Credential Exposure in Reports

**Threat**: Assessment reports inadvertently include hardcoded credentials found in source code.

**Mitigations:**
- Review reports before sharing
- Use automated credential scanning tools
- Encrypt reports at rest
- Implement access controls on report directories

**User actions:**
```bash
# Scan reports for potential secrets before sharing
git-secrets --scan agentic-readiness-assessment/*.md
trufflehog filesystem agentic-readiness-assessment/

# Redact sensitive findings manually if needed
```

### Scenario 3: Unauthorized Repository Access

**Threat**: Attacker gains access to Git credentials and clones private repositories.

**Mitigations:**
- Use SSH keys with passphrase protection
- Enable MFA on Git provider accounts
- Use credential managers (not plaintext storage)
- Rotate credentials regularly
- Monitor Git access logs for anomalies

**User actions:**
```bash
# Use SSH agent with timeout
ssh-add -t 3600 ~/.ssh/id_ed25519  # 1 hour timeout

# Review GitHub/GitLab access logs regularly
# Enable alerts for unusual access patterns
```

### Scenario 4: AI Model Prompt Injection

**Threat**: Malicious code comments attempt to manipulate AI analysis through prompt injection.

**Mitigations:**
- Amazon Bedrock uses managed models with built-in protections
- Input sanitization before AI analysis
- Structured output validation
- Prompt engineering best practices in transformation definitions

**User actions:**
- Review assessment findings for anomalies
- Cross-validate AI-generated recommendations
- Report suspicious assessment behavior to AWS

---

## Incident Response

If you suspect a security incident during assessment execution:

1. **Stop immediately**: Halt any running assessments
2. **Isolate**: Disconnect from network if credential compromise suspected
3. **Preserve evidence**: Save logs, configs, and error messages
4. **Rotate credentials**: Change Git and AWS credentials immediately
5. **Report**: Contact your security team and AWS Support
6. **Review**: Analyze what went wrong and update procedures

**AWS Security Contact:**
- For AWS service security issues: aws-security@amazon.com
- For this project: See [CONTRIBUTING.md](CONTRIBUTING.md#security-issue-notifications)

---

## Compliance Considerations

### Data Classification

Assessment reports typically contain:
- **Confidential**: Architecture diagrams, service dependencies
- **Internal**: Technology stack details, modernization recommendations
- **Potentially Sensitive**: Security gaps, vulnerability findings

Handle according to your organization's data classification policy.

### Regulatory Requirements

If assessing applications subject to regulatory requirements:
- **GDPR**: Ensure no PII in assessment reports
- **HIPAA**: Use encrypted storage for reports
- **PCI DSS**: Restrict access to reports about payment systems
- **SOC 2**: Maintain audit logs of all assessment activities

### Third-Party Assessments

If using external consultants to run assessments:
- Require NDAs before sharing reports
- Provide read-only repository access only
- Use separate AWS accounts with limited permissions
- Review all generated reports before handoff
- Ensure secure deletion of cloned repositories after assessment

---

## Security Checklist

Before running portfolio assessments:

- [ ] AWS Transform CLI installed with least privilege IAM permissions
- [ ] Git credentials configured with credential manager (not hardcoded)
- [ ] Repository URLs validated as trusted sources
- [ ] Portfolio configuration contains no sensitive data
- [ ] Assessment environment isolated from production
- [ ] CloudTrail enabled for AWS API logging
- [ ] File system encryption enabled
- [ ] Report storage location secured with access controls
- [ ] Incident response procedures documented
- [ ] Team trained on secure assessment practices

After completing assessments:

- [ ] Reports reviewed for credential exposure
- [ ] Sensitive findings redacted before sharing
- [ ] Reports encrypted if stored long-term
- [ ] Temporary `.atx-config-*.yaml` files deleted
- [ ] Cloned repositories removed if no longer needed
- [ ] Access logs reviewed for anomalies
- [ ] Credentials rotated if any concerns
- [ ] Lessons learned documented

---

## Additional Resources

- [AWS Transform Security Documentation](https://docs.aws.amazon.com/transform/latest/userguide/security.html)
- [Amazon Bedrock Security Best Practices](https://docs.aws.amazon.com/bedrock/latest/userguide/security-best-practices.html)
- [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)
- [Git Security Best Practices](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

---

**Last Updated**: 2026-03-18  
**Review Cycle**: Quarterly
