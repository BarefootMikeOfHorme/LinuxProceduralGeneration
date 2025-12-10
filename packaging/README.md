# VaultMind Forge - Package Building

This directory contains scripts and configuration files for building distributable packages.

## Arch Linux (AUR)

**Files:**
- `../PKGBUILD` - Arch Linux package build script
- `../vaultmind-forge.install` - Post-install hooks
- `vaultmind-forge.service` - Systemd service file
- `vaultmind-forge` - CLI wrapper script

**Building:**

```bash
# 1. Clone the repository
git clone https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git
cd LinuxProceduralGeneration

# 2. Build the package
makepkg -si

# 3. Or create source package for AUR
makepkg --printsrcinfo > .SRCINFO
```

**Publishing to AUR:**

```bash
# 1. Clone AUR repository
git clone ssh://aur@aur.archlinux.org/vaultmind-forge.git aur-vaultmind-forge
cd aur-vaultmind-forge

# 2. Copy files
cp ../PKGBUILD .
cp ../vaultmind-forge.install .
makepkg --printsrcinfo > .SRCINFO

# 3. Commit and push
git add PKGBUILD vaultmind-forge.install .SRCINFO
git commit -m "Update to version X.X.X"
git push
```

---

## Windows Installer

**Requirements:**
- [Inno Setup 6.x](https://jrsoftware.org/isdl.php)
- [NSSM (Non-Sucking Service Manager)](https://nssm.cc/download)

**Files:**
- `windows-installer.iss` - Inno Setup script
- `install-service.bat` - Service installation script
- `uninstall-service.bat` - Service removal script
- `windows-service-wrapper.bat` - Service execution wrapper

**Building:**

1. **Install Inno Setup:**
   Download and install from https://jrsoftware.org/isdl.php

2. **Build the web UI:**
   ```bash
   cd web_ui
   npm install
   npm run build
   ```

3. **Compile the installer:**
   ```bash
   # Using Inno Setup Compiler
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\windows-installer.iss
   ```

   Or open `windows-installer.iss` in Inno Setup and click "Compile"

4. **Output:**
   The installer will be created at: `packaging\dist\VaultMindForge-1.0.0-Setup.exe`

**Testing:**

1. Run the generated installer
2. Follow the installation wizard
3. The installer will:
   - Check for Python 3.12 (offer to download if missing)
   - Check for Node.js 18 (offer to download if missing)
   - Create virtual environment
   - Install Python dependencies
   - Install and start Windows service (if selected)
   - Open configuration editor (.env file)

**Service Management:**

After installation, the service can be managed with:
- Start Menu shortcuts
- NSSM commands:
  ```powershell
  nssm status VaultMindForge
  nssm start VaultMindForge
  nssm stop VaultMindForge
  nssm restart VaultMindForge
  ```

---

## Docker

See `../Dockerfile` and `../docker-compose.yml` for containerized deployment.

Build and publish:

```bash
# Build
docker build -t vaultmind-forge:1.0.0 .

# Tag for registry
docker tag vaultmind-forge:1.0.0 your-registry/vaultmind-forge:1.0.0

# Push
docker push your-registry/vaultmind-forge:1.0.0
```

---

## Version Management

When releasing a new version:

1. Update version in:
   - `pyproject.toml`
   - `web_ui/package.json`
   - `PKGBUILD` (pkgver)
   - `packaging/windows-installer.iss` (#define MyAppVersion)

2. Create git tag:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. Rebuild all packages

4. Publish to distribution channels
