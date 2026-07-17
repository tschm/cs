# Security Policy

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to the Security Advisories page of this repository
   - Click "New draft security advisory"
   - Fill in the details and submit

2. **Email**
   - Send details to the repository maintainers
   - Include "SECURITY" in the subject line

### What to Include

Please include the following information in your report:

- **Description**: A clear description of the vulnerability
- **Impact**: The potential impact of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Affected Versions**: Which versions are affected
- **Suggested Fix**: If you have one (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 7 days
- **Resolution Timeline**: We aim to resolve critical issues within 30 days
- **Credit**: We will credit reporters in the security advisory (unless you prefer to remain anonymous)

### Scope

This security policy applies to:

- The source code and configuration files in this repository
- GitHub Actions workflows provided by this repository
- Python utilities and scripts maintained in this repository

### Out of Scope

The following are generally out of scope:

- Vulnerabilities in upstream dependencies (report these to the respective projects)
- Issues that require physical access to a user's machine
- Social engineering attacks
- Denial of service attacks that require significant resources

## Security Measures

This project implements several security measures:

### Code Scanning
- **CodeQL**: Automated code scanning for Python and GitHub Actions
- **Bandit**: Python security linter integrated in CI and pre-commit
- **Secret Scanning**: GitHub secret scanning enabled on this repository
- **Fuzzing**: ClusterFuzzLite exercises Atheris-based fuzz targets on pull requests and scheduled batch runs

### Supply Chain Security
- **SLSA Provenance**: Build attestations for release artifacts (public repositories only)
- **Locked Dependencies**: `uv.lock` ensures reproducible builds
- **Dependabot**: Automated dependency updates with security patches (version and security updates)
- **Renovate**: Additional automated dependency update management

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please report security issues by emailing the maintainers directly or using
[GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
if enabled for this repository.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Any suggested mitigations or patches

We will acknowledge receipt of your report and aim to respond within 5 business days.
