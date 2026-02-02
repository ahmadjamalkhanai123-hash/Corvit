---
name: github-ide-connect
description: |
  Automates connecting any code IDE to GitHub accounts. Handles SSH keys, Personal Access Tokens, GitHub CLI authentication, and OAuth setup.
  This skill should be used when users need to connect their IDE (VS Code, JetBrains, Cursor, Vim, Neovim, Sublime, etc.) to GitHub for the first time or fix authentication issues.
---

# GitHub IDE Connect

Automate the setup of GitHub authentication for any IDE.

## Before Implementation

| Source | Gather |
|--------|--------|
| **User's IDE** | Which IDE(s) they use |
| **User's OS** | Windows, macOS, or Linux |
| **Auth preference** | SSH, HTTPS/PAT, or GitHub CLI |
| **Existing setup** | Any existing keys, tokens, or configs |

## Workflow

```
Detect Environment → Choose Auth Method → Execute Setup → Verify Connection → Configure IDE
```

### Step 1: Detect Environment

Run these commands to understand the current state:

```bash
# Check OS
uname -a || ver

# Check if Git is installed
git --version

# Check existing SSH keys
ls -la ~/.ssh/ 2>/dev/null || dir %USERPROFILE%\.ssh

# Check if GitHub CLI is installed
gh --version 2>/dev/null

# Check existing Git config
git config --global user.name
git config --global user.email
```

### Step 2: Choose Authentication Method

| Method | Best For | Requirements |
|--------|----------|--------------|
| **SSH** | Most secure, passwordless | SSH client |
| **GitHub CLI** | Easiest setup | `gh` installed |
| **PAT (HTTPS)** | Behind strict firewalls | None |

**Decision tree:**
1. If `gh` is installed → Recommend GitHub CLI
2. If SSH access available → Recommend SSH
3. Otherwise → Use PAT

### Step 3: Execute Setup

See `references/auth-methods.md` for detailed procedures per method.

#### Quick SSH Setup
```bash
# Generate key (if none exists)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key
ssh-add ~/.ssh/id_ed25519

# Copy public key (then add to GitHub → Settings → SSH Keys)
cat ~/.ssh/id_ed25519.pub
```

#### Quick GitHub CLI Setup
```bash
# Install if needed (varies by OS - see references/)
# Then authenticate
gh auth login
# Follow interactive prompts, choose SSH protocol
```

#### Quick PAT Setup
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Generate token with `repo` scope
3. Use as password when Git prompts for credentials

### Step 4: Verify Connection

```bash
# For SSH
ssh -T git@github.com

# For GitHub CLI
gh auth status

# For any method
git ls-remote https://github.com/octocat/Hello-World.git
```

Expected SSH output: `Hi username! You've successfully authenticated...`

### Step 5: Configure IDE

See `references/ide-configs.md` for IDE-specific setup.

**Universal Git config:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

## IDE-Specific Quick Reference

| IDE | Auth Integration | Config Location |
|-----|------------------|-----------------|
| VS Code | Settings Sync, GitHub extension | Settings → Accounts |
| JetBrains | Built-in GitHub plugin | Settings → Version Control → GitHub |
| Cursor | GitHub OAuth | Accounts panel |
| Vim/Neovim | Uses system Git | `~/.gitconfig` |
| Sublime | Uses system Git | `~/.gitconfig` |

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Permission denied (publickey) | SSH key not added | `ssh-add ~/.ssh/id_ed25519` |
| 403 Forbidden | PAT expired/wrong scope | Regenerate token with `repo` scope |
| SSL certificate problem | Corporate proxy | `git config --global http.sslVerify false` (temp) |
| OAuth app not authorized | Org restriction | Request access in GitHub org settings |

For detailed troubleshooting, see `references/troubleshooting.md`.

## Scripts Available

| Script | Purpose |
|--------|---------|
| `scripts/setup-ssh.sh` | Automated SSH key setup |
| `scripts/setup-ssh.ps1` | SSH setup for Windows PowerShell |
| `scripts/verify-connection.sh` | Test GitHub connectivity |

## What This Skill Does NOT Do

- Manage multiple GitHub accounts (use `gh auth switch` manually)
- Configure GitHub Actions or CI/CD
- Set up GitHub Enterprise (different auth flow)
- Handle 2FA recovery codes
