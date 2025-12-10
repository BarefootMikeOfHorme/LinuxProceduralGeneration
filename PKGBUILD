# Maintainer: Michael Shortland <barefoot.mike.of.horme@gmail.com>
pkgname=vaultmind-forge
pkgver=1.0.0
pkgrel=1
pkgdesc="AI-powered procedural content generation with visual node-based workflow editor"
arch=('x86_64')
url="https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration"
license=('custom:proprietary')
depends=(
    'python>=3.10'
    'python-pip'
    'python-virtualenv'
    'nodejs>=18'
    'npm'
    'curl'
)
optdepends=(
    'docker: For containerized deployment'
    'nginx: For reverse proxy setup'
    'redis: For distributed rate limiting'
    'systemd: For service management'
)
makedepends=(
    'git'
)
source=(
    "git+https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git#tag=v${pkgver}"
)
sha256sums=('SKIP')
install=vaultmind-forge.install

build() {
    cd "${srcdir}/LinuxProceduralGeneration"

    # Create Python virtual environment
    python -m venv .venv312

    # Install Python dependencies
    .venv312/bin/pip install --upgrade pip
    .venv312/bin/pip install -r requirements.txt

    # Build web UI
    cd web_ui
    npm ci --only=production
    npm run build
}

package() {
    cd "${srcdir}/LinuxProceduralGeneration"

    # Create installation directory
    install -dm755 "${pkgdir}/opt/${pkgname}"

    # Copy application files
    cp -r backend "${pkgdir}/opt/${pkgname}/"
    cp -r vaultmind_forge "${pkgdir}/opt/${pkgname}/"
    cp -r web_ui/dist "${pkgdir}/opt/${pkgname}/web_ui/"
    cp -r .venv312 "${pkgdir}/opt/${pkgname}/"

    # Copy configuration files
    install -Dm644 .env.example "${pkgdir}/opt/${pkgname}/.env.example"
    install -Dm644 pyproject.toml "${pkgdir}/opt/${pkgname}/pyproject.toml"
    install -Dm644 requirements.txt "${pkgdir}/opt/${pkgname}/requirements.txt"

    # Copy documentation
    install -Dm644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"
    install -Dm644 LICENSE.md "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE.md"
    install -Dm644 docs/DEPLOYMENT.md "${pkgdir}/usr/share/doc/${pkgname}/DEPLOYMENT.md"

    # Install systemd service
    install -Dm644 "${srcdir}/LinuxProceduralGeneration/packaging/vaultmind-forge.service" \
        "${pkgdir}/usr/lib/systemd/system/vaultmind-forge.service"

    # Install CLI wrapper script
    install -Dm755 "${srcdir}/LinuxProceduralGeneration/packaging/vaultmind-forge" \
        "${pkgdir}/usr/bin/vaultmind-forge"

    # Create data directories
    install -dm755 "${pkgdir}/var/lib/${pkgname}"
    install -dm755 "${pkgdir}/var/log/${pkgname}"
    install -dm755 "${pkgdir}/var/lib/${pkgname}/models"
    install -dm755 "${pkgdir}/var/lib/${pkgname}/output"
    install -dm755 "${pkgdir}/var/lib/${pkgname}/checkpoints"
}
