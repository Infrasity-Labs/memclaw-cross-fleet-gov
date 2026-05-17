# Security Policy

## Reporting a Vulnerability

Please report vulnerabilities privately to the maintainers before opening a public issue.

Include:
- affected component
- reproduction steps
- potential impact
- suggested mitigation (if known)

## Secrets and Credentials

Never commit live credentials to this repository.
Use environment variables via `.env` and keep `.env` out of version control.

If a credential is exposed:
1. Rotate/revoke it immediately.
2. Replace it with a placeholder.
3. Audit logs for suspicious use.

## Scope

This repository is a reference implementation and is not production hardened by default.
Additional controls are required for production use.
