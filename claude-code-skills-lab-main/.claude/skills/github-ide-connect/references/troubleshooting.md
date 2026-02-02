# Troubleshooting Guide

## SSH Issues

### Permission denied (publickey)

**Symptoms:**
```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Diagnosis:**
```bash
# Check if SSH agent is running
ssh-add -l

# Test SSH connection with verbose output
ssh -vT git@github.com
```

**Solutions:**

1. **Key not added to agent:**
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

2. **Key not on GitHub:**
   - Copy public key: `cat ~/.ssh/id_ed25519.pub`
   - Add to GitHub → Settings → SSH and GPG keys

3. **Wrong key being used:**
   Edit `~/.ssh/config`:
   ```
   Host github.com
       IdentityFile ~/.ssh/id_ed25519
       IdentitiesOnly yes
   ```

4. **Key permissions too open:**
   ```bash
   chmod 600 ~/.ssh/id_ed25519
   chmod 644 ~/.ssh/id_ed25519.pub
   chmod 700 ~/.ssh
   ```

### Connection timed out

**Symptoms:**
```
ssh: connect to host github.com port 22: Connection timed out
```

**Solutions:**

1. **Use SSH over HTTPS port:**
   Edit `~/.ssh/config`:
   ```
   Host github.com
       Hostname ssh.github.com
       Port 443
       User git
   ```

2. **Check firewall/proxy settings**

---

## HTTPS/PAT Issues

### 403 Forbidden

**Symptoms:**
```
remote: Permission to user/repo.git denied
fatal: unable to access: The requested URL returned error: 403
```

**Solutions:**

1. **Token expired:** Generate new PAT on GitHub
2. **Wrong scopes:** Ensure `repo` scope is selected
3. **Org restrictions:** Request OAuth app access in org settings

### Authentication failed

**Symptoms:**
```
remote: Invalid username or password.
fatal: Authentication failed
```

**Solutions:**

1. **Clear cached credentials:**
   ```bash
   # Windows
   cmdkey /delete:git:https://github.com

   # macOS
   git credential-osxkeychain erase
   host=github.com
   protocol=https
   [press Enter twice]

   # Linux
   rm ~/.git-credentials
   ```

2. **Use PAT instead of password:**
   - GitHub no longer accepts passwords
   - Generate PAT and use as password

---

## IDE-Specific Issues

### JetBrains: Can't push to organization repo

**Cause:** JetBrains IDE Integration OAuth app not authorized

**Solution:**
1. GitHub → Settings → Applications → Authorized OAuth Apps
2. Find "JetBrains IDE Integration"
3. Click → Grant access to required organizations

### VS Code: Git not found

**Symptoms:**
```
Git not found. Install it or configure it using 'git.path' setting.
```

**Solution:**
```json
// settings.json
{
  "git.path": "C:\\Program Files\\Git\\bin\\git.exe"  // Windows
  // or
  "git.path": "/usr/bin/git"  // Linux/macOS
}
```

### Cursor: Auth code not appearing

**Solution:**
- Look at bottom-left status bar (not menus)
- The auth code appears there during OAuth flow

---

## SSL/TLS Issues

### SSL certificate problem

**Symptoms:**
```
SSL certificate problem: unable to get local issuer certificate
```

**Temporary fix (not recommended for production):**
```bash
git config --global http.sslVerify false
```

**Proper solutions:**

1. **Update CA certificates:**
   ```bash
   # macOS
   brew install ca-certificates

   # Ubuntu/Debian
   sudo apt update && sudo apt install ca-certificates

   # Windows - reinstall Git with OpenSSL
   ```

2. **Corporate proxy - add certificate:**
   ```bash
   git config --global http.sslCAInfo /path/to/certificate.pem
   ```

---

## Network Issues

### Behind corporate proxy

**Solution:**
```bash
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy https://proxy.example.com:8080
```

**With authentication:**
```bash
git config --global http.proxy http://user:password@proxy.example.com:8080
```

**Remove proxy:**
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## Credential Issues

### Credentials not being saved

**Solution by OS:**

**Windows:**
```bash
git config --global credential.helper manager
```

**macOS:**
```bash
git config --global credential.helper osxkeychain
```

**Linux:**
```bash
# Temporary (15 min cache)
git config --global credential.helper cache

# Permanent (stored in plaintext)
git config --global credential.helper store
```

### Wrong credentials being used

**Clear all credentials:**
```bash
# Check current helper
git config --global credential.helper

# For manager (Windows)
cmdkey /list | findstr git
cmdkey /delete:git:https://github.com

# For osxkeychain (macOS)
git credential-osxkeychain erase
host=github.com
protocol=https
```

---

## Diagnostic Commands

```bash
# Full Git configuration
git config --list --show-origin

# SSH debug
ssh -vvv git@github.com

# Check remote URLs
git remote -v

# GitHub CLI status
gh auth status

# Test connectivity
curl -I https://github.com
ssh -T git@github.com
```
