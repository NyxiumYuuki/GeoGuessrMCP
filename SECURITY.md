# Security Policy

## Supported Versions

We actively support the following versions of the GeoGuessr MCP Server:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of the GeoGuessr MCP Server seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **Do NOT** open a public issue for security vulnerabilities
2. Email security details to: **yuki.vachot@datasingularity.fr**
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested fix (if available)

### What to Expect

- **Acknowledgment**: You will receive a response within 48 hours acknowledging receipt of your report
- **Investigation**: We will investigate the issue and provide an initial assessment within 5 business days
- **Updates**: We will keep you informed about the progress of the fix
- **Resolution**: Once fixed, we will notify you and coordinate disclosure timing
- **Credit**: We will credit you for the discovery (unless you prefer to remain anonymous)

## Security Best Practices

### Authentication

- **Never commit** your `GEOGUESSR_NCFA_COOKIE` to version control
- Use environment variables (`.env` file) for sensitive credentials
- Rotate your cookies regularly
- Use read-only API access when possible

### Deployment

- Always use HTTPS in production environments
- Keep Docker images updated with the latest security patches
- Use secrets management for production deployments
- Implement rate limiting on public-facing endpoints
- Review and restrict container permissions

### API Usage

- Monitor API usage for unusual patterns
- Implement request validation and sanitization
- Use the latest version of dependencies
- Enable monitoring and logging for security events

## Known Security Considerations

### Authentication Token Storage

The server stores authentication cookies in memory during runtime. For production use:
- Ensure proper access controls on the server
- Use encrypted storage if persisting credentials
- Implement session timeouts

### API Monitoring

The monitoring system periodically checks GeoGuessr API endpoints:
- Requests are made with appropriate rate limiting
- No sensitive data is logged
- Schema data is stored locally without sensitive information

### Docker Security

When deploying with Docker:
- Use non-root user inside containers
- Limit container capabilities
- Use read-only root filesystem where possible
- Scan images for vulnerabilities regularly

## Dependency Security

We use automated tools to monitor dependencies:
- Regular updates via Dependabot (recommended)
- Vulnerability scanning in CI/CD pipelines
- Manual security audits of critical dependencies

### Updating Dependencies

```bash
# Check for security vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade -e ".[dev]"
```

## Security Checklist for Contributors

Before submitting a pull request, ensure:

- [ ] No hardcoded credentials or secrets
- [ ] Input validation on all user-provided data
- [ ] Proper error handling without information disclosure
- [ ] No SQL injection vulnerabilities (if using databases)
- [ ] No XSS vulnerabilities in web interfaces
- [ ] Dependencies are up to date
- [ ] Security tests are passing
- [ ] Code follows secure coding practices

## Vulnerability Disclosure Policy

We follow a coordinated disclosure policy:

1. **Private disclosure**: Vulnerabilities are reported privately
2. **Investigation period**: 90 days to develop and test a fix
3. **Coordinated release**: Fix is released with security advisory
4. **Public disclosure**: Details published after fix is available

## Security Updates

Security updates are released as:
- **Critical**: Immediate patch release
- **High**: Release within 7 days
- **Medium**: Release within 30 days
- **Low**: Included in next scheduled release

## Contact

For security-related questions or concerns:
- **Email**: yuki.vachot@datasingularity.fr
- **Response Time**: Within 48 hours

---

**Last Updated**: 2025-11-29
