# IDE-Specific Configurations

## VS Code

### Built-in Git Integration
VS Code has built-in Git support. No extension needed for basic operations.

### GitHub Extension Setup
1. Install "GitHub Pull Requests and Issues" extension
2. Click Accounts icon (bottom left)
3. Sign in with GitHub
4. Authorize VS Code in browser

### Settings
```json
{
  "git.autofetch": true,
  "git.confirmSync": false,
  "github.gitProtocol": "ssh"
}
```

### Settings Sync with GitHub
1. Click gear icon → Turn on Settings Sync
2. Sign in with GitHub
3. Select what to sync

---

## JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)

### GitHub Plugin Setup
1. Settings/Preferences → Version Control → GitHub
2. Click `+` to add account
3. Choose login method:
   - **Log In via GitHub** (OAuth - recommended)
   - **Log In with Token** (PAT)

### Token Authentication
If OAuth fails:
1. Generate PAT with scopes: `repo`, `read:org`, `gist`
2. Settings → Version Control → GitHub → `+` → Log In with Token
3. Paste token

### Git Configuration
Settings → Version Control → Git:
- Path to Git executable: auto-detected or set manually
- SSH executable: Built-in or Native

### Troubleshooting JetBrains
If 403 errors occur:
1. Settings → Version Control → GitHub
2. Remove account
3. Re-add using "Log In via GitHub"
4. Ensure JetBrains IDE Integration app is authorized in GitHub

---

## Cursor

### GitHub Integration
1. Click account icon in sidebar
2. Connect GitHub Account
3. Authorize in browser
4. Watch status bar for auth code (bottom-left)

### SSH Setup for Cursor
Cursor uses system Git, so configure SSH at system level:
```bash
ssh-keygen -t ed25519 -C "email@example.com"
ssh-add ~/.ssh/id_ed25519
# Add public key to GitHub
```

---

## Vim/Neovim

### Uses System Git
Vim doesn't have built-in GitHub integration. Configure at system level.

### Recommended Plugins
- **fugitive.vim** - Git wrapper
- **vim-gh-line** - Open lines on GitHub

### Configuration Example
```vim
" .vimrc or init.vim
Plug 'tpope/vim-fugitive'

" Set Git editor
let $GIT_EDITOR = 'nvim'
```

### Git Config
```bash
git config --global core.editor "nvim"
```

---

## Sublime Text

### Uses System Git
Configure Git at system level. Sublime uses your terminal Git config.

### Sublime Merge
For better Git integration, use Sublime Merge alongside Sublime Text.

### Package: GitGutter
Shows Git diff in gutter:
1. Cmd/Ctrl + Shift + P
2. Install Package
3. Search "GitGutter"

---

## Visual Studio

### GitHub Extension
1. Extensions → Manage Extensions
2. Search "GitHub Extension for Visual Studio"
3. Install and restart

### Team Explorer
1. View → Team Explorer
2. Connect → GitHub → Sign in
3. Clone or create repositories

---

## Xcode

### Source Control
1. Xcode → Preferences → Accounts
2. Click `+` → GitHub
3. Sign in or use PAT

### SSH Configuration
Xcode uses system SSH. Ensure keys are added:
```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

---

## Eclipse

### EGit Plugin (pre-installed)
1. Window → Preferences → Version Control → Git
2. Configuration → User Settings
3. Set user.name and user.email

### GitHub Integration
1. Window → Show View → Git Repositories
2. Clone a Git Repository
3. Use SSH or HTTPS URL

---

## Android Studio

Same as JetBrains IDEs. See JetBrains section above.

---

## Universal Configuration

### Git Global Config
```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```

### Credential Helper

**macOS:**
```bash
git config --global credential.helper osxkeychain
```

**Windows:**
```bash
git config --global credential.helper manager
```

**Linux:**
```bash
git config --global credential.helper store
# or for temporary caching:
git config --global credential.helper cache
```
