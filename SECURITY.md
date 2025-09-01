# Security Guidelines

## 🔒 **CRITICAL SECURITY WARNING**

**FACT:** This template requires Spotify API credentials to function. **NEVER commit your actual credentials to version control!**

## Security Overview

This document outlines security best practices for using the Spotify App Agent Template. Following these guidelines is essential to protect your Spotify account and API credentials.

## 🚨 **IMMEDIATE SECURITY ACTIONS REQUIRED**

### 1. **Credential Management**
- ✅ **DO**: Use environment variables for all credentials
- ❌ **NEVER**: Hardcode credentials in source code
- ✅ **DO**: Keep `.env` files out of version control
- ❌ **NEVER**: Commit credentials to Git repositories

### 2. **Credential Rotation**
- **IMMEDIATE**: Rotate any exposed Spotify API credentials
- **REGULAR**: Set up credential rotation schedule (every 90 days)
- **MONITOR**: Watch for unusual API usage patterns

## 🔐 **Credential Security**

### Environment Variables
All credentials must be stored in environment variables:

```bash
# .env file (NEVER commit this file)
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REFRESH_TOKEN=your_refresh_token_here
SPOTIFY_USER_ID=your_spotify_user_id
```

### Secure Credential Loading
The template uses secure credential loading:

```python
# SECURE: Load from environment variables
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# VALIDATE: Check if credentials are provided
if not client_id or not client_secret:
    print("❌ CRITICAL SECURITY ERROR: Missing credentials!")
    sys.exit(1)
```

## 🛡️ **Security Features**

### Built-in Security Measures
- **No hardcoded secrets**: All credentials loaded from environment variables
- **Input validation**: All user inputs validated and sanitized
- **Error handling**: Comprehensive error handling prevents information leakage
- **Rate limiting**: Built-in rate limiting respects Spotify's API limits
- **Secure file handling**: Sensitive files excluded from version control

### Git Security
The `.gitignore` file excludes sensitive files:

```gitignore
# Environment variables and secrets
.env
.env.local
.env.*.local

# Spotify API credentials (backup)
api_keys.txt
credentials.json
```

## 🔍 **Security Checklist**

### Before Using the Template
- [ ] Create a dedicated Spotify app for this project
- [ ] Set appropriate redirect URIs in Spotify Developer Dashboard
- [ ] Use minimal required scopes for your app
- [ ] Create a `.env` file with your credentials
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test authentication flow

### During Development
- [ ] Never hardcode credentials in source code
- [ ] Use environment variables for all secrets
- [ ] Validate all user inputs
- [ ] Handle errors gracefully without exposing sensitive data
- [ ] Monitor API usage for unusual patterns
- [ ] Keep dependencies updated

### Before Deployment
- [ ] Rotate all credentials
- [ ] Review and minimize API scopes
- [ ] Set up monitoring and alerting
- [ ] Test security measures
- [ ] Document security procedures

## 🚨 **Common Security Mistakes**

### ❌ **NEVER DO THESE**

1. **Hardcode credentials in source code**
   ```python
   # WRONG - Never do this!
   CLIENT_ID = "your_actual_client_id"
   CLIENT_SECRET = "your_actual_secret"
   ```

2. **Commit .env files to version control**
   ```bash
   # WRONG - Never do this!
   git add .env
   git commit -m "Add credentials"
   ```

3. **Share credentials in public repositories**
   - Never post credentials in GitHub issues
   - Never share credentials in public forums
   - Never include credentials in code examples

4. **Use overly broad API scopes**
   - Only request the permissions you actually need
   - Review and minimize scopes regularly

### ✅ **ALWAYS DO THESE**

1. **Use environment variables**
   ```python
   # CORRECT - Always do this!
   client_id = os.getenv('SPOTIFY_CLIENT_ID')
   client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
   ```

2. **Validate credentials**
   ```python
   # CORRECT - Always validate
   if not client_id or not client_secret:
       print("❌ Missing credentials!")
       sys.exit(1)
   ```

3. **Keep credentials secure**
   - Store in `.env` files (excluded from Git)
   - Use secure credential management systems
   - Rotate credentials regularly

## 🔧 **Security Tools and Practices**

### Pre-commit Hooks
The template includes pre-commit hooks to prevent credential commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-for-credentials
        name: Check for hardcoded credentials
        entry: python tools/security_check.py
        language: system
        stages: [commit]
```

### Security Scanning
Regular security scans help identify vulnerabilities:

```bash
# Run security checks
python tools/security_check.py

# Check for hardcoded secrets
grep -r "CLIENT_ID\|CLIENT_SECRET\|API_KEY" . --exclude-dir=.git
```

### Monitoring
Monitor your application for security issues:

- **API Usage**: Watch for unusual API call patterns
- **Error Logs**: Monitor for authentication failures
- **Access Logs**: Track who accesses your application
- **Credential Usage**: Monitor credential refresh patterns

## 🆘 **Security Incident Response**

### If Credentials Are Exposed

1. **IMMEDIATE ACTIONS**
   - Revoke exposed credentials in Spotify Developer Dashboard
   - Generate new credentials
   - Update all environment variables
   - Check for unauthorized API usage

2. **INVESTIGATION**
   - Review Git history for credential commits
   - Check logs for unauthorized access
   - Monitor API usage for suspicious activity
   - Review access logs

3. **RECOVERY**
   - Update all systems with new credentials
   - Test authentication flows
   - Verify no unauthorized access occurred
   - Document the incident

### Reporting Security Issues

If you find a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. **DO** report privately to the maintainer
3. **DO** provide detailed information about the vulnerability
4. **DO** wait for a response before public disclosure

## 📚 **Security Resources**

### Spotify API Security
- [Spotify Web API Security](https://developer.spotify.com/documentation/web-api)
- [OAuth 2.0 Best Practices](https://tools.ietf.org/html/rfc6819)
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

### General Security
- [OWASP Security Guidelines](https://owasp.org/)
- [GitHub Security Best Practices](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure)
- [Python Security Best Practices](https://python-security.readthedocs.io/)

## 🔄 **Security Maintenance**

### Regular Tasks
- **Monthly**: Review API usage and permissions
- **Quarterly**: Rotate credentials
- **Annually**: Security audit and dependency updates
- **Ongoing**: Monitor for security updates and patches

### Security Updates
- Keep all dependencies updated
- Monitor security advisories
- Apply security patches promptly
- Test security measures regularly

## 📞 **Security Support**

### Getting Help
- **Documentation**: Review this security guide thoroughly
- **Issues**: Report security issues privately
- **Community**: Seek help from security professionals
- **Spotify Support**: Contact Spotify for API-related issues

### Emergency Contacts
- **Spotify Developer Support**: [developer.spotify.com/support](https://developer.spotify.com/support)
- **Security Incident**: Report privately to maintainers
- **Credential Compromise**: Revoke immediately in Spotify Dashboard

---

**Remember**: Security is everyone's responsibility. Stay vigilant and follow these guidelines to keep your application and credentials secure! 🔒
