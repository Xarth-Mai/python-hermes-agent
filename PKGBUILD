# Maintainer: wyf9661 <wyf9661@hotmail.com>
# Contributor: Nous Research <ops@nousresearch.com>

_pkgname=hermes-agent
pkgname=python-${_pkgname}
tag=2026.8.19
pkgver=0.20.5
pkgrel=1
pkgdesc="The self-improving AI agent — creates skills from experience, improves them during use, and runs anywhere"
arch=('any')
url="https://github.com/NousResearch/${_pkgname}"
license=('MIT')
depends=('python>=3.11' 'python-dotenv' 'python-prompt_toolkit' 'python-openai' 'python-fire'
          'python-ruamel-yaml' 'python-rich' 'python-pyjwt' 'python-tenacity' 'python-yaml'
          'python-httpx' 'python-requests' 'python-jinja' 'python-pydantic' 'python-psutil'
          'python-markdown' 'python-pathspec' 'python-ptyprocess'
          'python-certifi' 'python-packaging' 'python-urllib3' 'python-websockets'
          'python-pillow' 'python-multipart' 'python-cryptography'
          'python-fastapi' 'python-starlette' 'python-croniter' 'uvicorn')
optdepends=('python-telegram-bot: Telegram messaging support'
            'python-discord: Discord messaging support (PyPI: discord.py)'
            'python-aiohttp: Async HTTP for messaging/web, QQ bot & Wechat messaging needs this'
            'python-mcp: Model Context Protocol support'
            'python-anthropic: Anthropic Claude API support'
            'python-faster-whisper: Local voice transcription'
            'python-sounddevice: Audio I/O for voice'
            'python-numpy: Numerical computing for voice/other'
            'python-simple-term-menu: Interactive CLI menu'
            'python-slack-sdk: Slack integration'
            'python-qrcode: QR code generation for auth'
            'python-exa-py: Exa web search backend'
            'python-firecrawl-py: Firecrawl web search backend'
            'python-fal-client: Fal image generation backend'
            'python-edge-tts: Edge TTS TTS backend'
            'python-brotlicffi: Brotli compression for aiohttp'
            'python-mautrix: Matrix messaging support'
            'python-aiosqlite: SQLite async for Matrix'
            'python-asyncpg: PostgreSQL async for Matrix'
            'python-aiohttp-socks: SOCKS proxy for Matrix'
            'python-defusedxml: XML hardening for WeCom')
makedepends=('python-installer' 'python-wheel' 'python-build' 'python-setuptools' 'nodejs' 'npm')
# Bun / JS bundles and generated assets should not be stripped.
options=('!strip' '!debug')
source=(
    "${url}/archive/refs/tags/v${tag}.tar.gz"
    "0001-fix-daemon-pool-py314-ThreadPoolExecutor-API.patch"
    "0002-use-hermes-wrapper-for-systemd-gateway.patch"
    "0003-fix-systemd-virtualenv-for-arch-package.patch"
    "hermes-wrapper"
)
sha256sums=('8e7f7d2aa6be48ae8b5550325be44aef339413ceec6ed74c18287001103de8fd'
            '6b3357098d9e70eb33c95e2f7d12c2bdc016f6e7933b517d85f1399d50caea71'
            '6027be55aff07d1950fa9d942d7da48fca00434d3c38d0d95af0d4f7699d3ab2'
            '0a92b4ae04655681b0b7bcc90418ed94033699a1673e813ddb1e18d4462f034d'
            '9531986d061e1503395b4261d941a78f48996c48f9c7190cf0787113d07127b9')

prepare() {
  cd "${srcdir}/hermes-agent-${tag}"
  # Arch Linux packaging uses distro setuptools.
  # Relax upstream's setuptools pin so the package can build with
  # the current Arch Python toolchain.
  sed -i \
    -e 's/setuptools>=77.0,<83/setuptools>=77.0/' \
    -e 's/setuptools==83.0.0/setuptools>=77.0/' \
    pyproject.toml
  # Python 3.14: ThreadPoolExecutor no longer has _initializer/_initargs
  patch -p1 < "${srcdir}/0001-fix-daemon-pool-py314-ThreadPoolExecutor-API.patch"
  # Use the packaged hermes wrapper for generated systemd units.
  # This preserves HERMES_* runtime asset environment variables.
  patch -p1 < "${srcdir}/0002-use-hermes-wrapper-for-systemd-gateway.patch"
  # Do not emit a fake VIRTUAL_ENV for non-venv (Arch system Python) installs.
  patch -p1 < "${srcdir}/0003-fix-systemd-virtualenv-for-arch-package.patch"
}

build() {
  cd "${srcdir}/hermes-agent-${tag}"

  # Upstream blocks normal wheel builds because runtime assets are not included.
  # We package those assets separately below, matching the upstream Nix layout.
  HERMES_NIX_BUILD=1 python -m build --wheel --no-isolation --quiet

  # Build the dashboard and TUI from the upstream npm workspaces.
  # The dashboard outputs to hermes_cli/web_dist via vite.config.ts.
  npm ci --silent --no-fund --no-audit --progress=false
  npm run --silent build --workspace web
  npm run --silent build --workspace ui-tui
}

package() {
  cd "${srcdir}/hermes-agent-${tag}"

  python -m installer --destdir="${pkgdir}" dist/*.whl

  local _share="${pkgdir}/usr/share/hermes-agent"

  install -d "${_share}"

  # Runtime assets intentionally omitted from the Python wheel.
  # Keep them under /usr/share and expose them through HERMES_* in the wrapper.
  cp -r plugins "${_share}/plugins"
  cp -r locales "${_share}/locales"
  cp -r optional-mcps "${_share}/optional-mcps"

  # Bundled skills and optional-skills are intentionally not packaged.
  # Users can manage skills separately through Hermes' skill management.

  find "${_share}" -type d -name '__pycache__' -prune -exec rm -rf '{}' +
  find "${_share}" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

  test -f hermes_cli/web_dist/index.html
  cp -r hermes_cli/web_dist "${_share}/web_dist"

  test -f ui-tui/dist/entry.js
  install -Dm644 ui-tui/dist/entry.js "${pkgdir}/usr/lib/hermes-agent/ui-tui/dist/entry.js"

  install -d "${pkgdir}/usr/lib/hermes-agent"

  # Preserve the wheel-generated console scripts and wrap them with
  # the runtime environment required by the split asset layout.
  local _cmd
  for _cmd in hermes hermes-agent hermes-acp; do
      if [[ -f "${pkgdir}/usr/bin/${_cmd}" ]]; then
          mv "${pkgdir}/usr/bin/${_cmd}" "${pkgdir}/usr/lib/hermes-agent/${_cmd}.real"
          ln -s /usr/lib/hermes-agent/hermes-wrapper "${pkgdir}/usr/bin/${_cmd}"
      fi
  done

  install -Dm755 "${srcdir}/hermes-wrapper" "${pkgdir}/usr/lib/hermes-agent/hermes-wrapper"

  # Packaging sanity checks.
  test -f "${_share}/plugins/platforms/wecom/plugin.yaml"
  test -d "${_share}/locales"
  test -d "${_share}/optional-mcps"
  test -f "${_share}/web_dist/index.html"
  test -f "${pkgdir}/usr/lib/hermes-agent/ui-tui/dist/entry.js"
}
