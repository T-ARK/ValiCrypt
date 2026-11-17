# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

The ValiCrypt project treats application and cryptographic security with the highest priority. If you identify a security vulnerability, please do NOT create a public GitHub issue.

Please report security issues to the security team via secure email or private advisory.

When submitting a report, please include:
1. Description of the vulnerability and attack vector.
2. Steps to reproduce or proof-of-concept carrier/payload.
3. Potential security impact (e.g. data leak, crash, denial of service).

## Security Commitments

- **No Passwords Logged**: Passwords and encryption keys are strictly scrubbed from logs via `SecuritySanitizingFilter`.
- **Ephemeral Storage**: Uploaded carriers and extracted archives are stored in isolated temporary directories and automatically cleaned up.
- **Decompression Bomb Protection**: Input ZIP files are inspected for decompression ratios and total uncompressed size limits before processing.
- **Zip Slip Defense**: Path traversal attacks (e.g. `../` or absolute file paths) inside archives are strictly rejected.
- **Subprocess Safety**: All external command invocations (FFmpeg/ffprobe) use subprocess argument arrays rather than raw shell strings to prevent command injection.
