# Authentication Methods

## SSH Authentication (Recommended)

### Why SSH?
- No passwords or tokens to manage
- Keys don't expire
- Works across all Git operations
- Most secure option

### Full Setup Process

#### 1. Generate SSH Key

**Ed25519 (recommended):**
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

**RSA (legacy systems):**
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

#### 2. Configure SSH Agent

**Linux/macOS:**
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

**Windows (PowerShell as Admin):**
```powershell
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

**Windows (Git Bash):**
```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519
```

#### 3. Add Key to GitHub

```bash
# Copy public key
cat ~/.ssh/id_ed25519.pub        # Linux/macOS
clip < ~/.ssh/id_ed25519.pub     # Windows
pbcopy < ~/.ssh/id_ed25519.pub   # macOS
```

Then: GitHub → Settings → SSH and GPG keys → New SSH key

#### 4. Configure SSH for GitHub

Create/edit `~/.ssh/config`:
```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    AddKeysToAgent yes
```

#### 5. Test Connection
```bash
ssh -T git@github.com
```

---

## GitHub CLI Authentication

### Installation

**macOS:**
```bash
brew install gh
```

**Windows:**
```powershell
winget install --id GitHub.cli
# or
choco install gh
```

**Linux (Debian/Ubuntu):**
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh
```

### Authentication Flow

```bash
gh auth login
```

Interactive prompts:
1. Select GitHub.com or Enterprise
2. Choose protocol: SSH (recommended) or HTTPS
3. Authenticate via browser or paste token

### Useful Commands
```bash
gh auth status          # Check current auth
gh auth refresh         # Refresh token
gh auth switch          # Switch accounts
gh auth logout          # Sign out
```

---

## Personal Access Tokens (PAT)

### When to Use
- Corporate firewalls blocking SSH
- CI/CD environments
- Script automation

### Token Types

| Type | Use Case |
|------|----------|
| Fine-grained | New projects, specific repos |
| Classic | Legacy, broader access |

### Required Scopes

**Minimum for Git operations:**
- `repo` - Full repository access
- `read:org` - Read org membership

**For GitHub CLI:**
- `repo`, `read:org`, `admin:public_key`

### Creating a Fine-Grained Token

1. GitHub → Settings → Developer settings
2. Personal access tokens → Fine-grained tokens
3. Generate new token
4. Set expiration (max 1 year)
5. Select repositories
6. Set permissions:
   - Contents: Read and write
   - Metadata: Read-only

### Using PAT

**Direct in URL (not recommended):**
```bash
git clone https://TOKEN@github.com/user/repo.git
```

**Git Credential Manager (recommended):**
```bash
git config --global credential.helper manager
# Then use token when prompted for password
```

**Store in environment:**
```bash
export GITHUB_TOKEN="your_token_here"
```

---

## OAuth Apps (IDE-Specific)

### How It Works
1. IDE redirects to GitHub authorization page
2. User approves access
3. GitHub sends token back to IDE
4. IDE stores token securely

### Supported IDEs
- VS Code (GitHub extension)
- JetBrains IDEs (built-in)
- Cursor
- GitHub Desktop

### Revoking Access
GitHub → Settings → Applications → Authorized OAuth Apps → Revoke
