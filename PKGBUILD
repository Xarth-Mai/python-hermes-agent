# Maintainer: wyf9661 <wyf9661@hotmail.com>
# Contributor: Nous Research <ops@nousresearch.com>

_pkgname=hermes-agent
pkgname=python-${_pkgname}
tag=0.22.0
pkgver=0.22.0
pkgrel=2
_commit=e06df9c2eae6901f4c88f464e0ae6e753c0428b8
pkgdesc="The self-improving AI agent — creates skills from experience, improves them during use, and runs anywhere"
arch=('any')
url="https://github.com/NousResearch/${_pkgname}"
license=('MIT')
depends=('nodejs' 'python>=3.14' 'python-dotenv' 'python-prompt_toolkit' 'python-openai' 'python-fire'
          'python-ruamel-yaml' 'python-rich' 'python-pyjwt' 'python-tenacity' 'python-yaml'
          'python-httpx' 'python-socksio' 'python-requests' 'python-jinja' 'python-pydantic' 'python-psutil'
          'python-markdown' 'python-pathspec' 'python-ptyprocess' 'python-snowballstemmer'
          'python-certifi' 'python-truststore' 'python-tomli-w' 'python-packaging' 'python-urllib3' 'python-websockets'
          'python-pillow' 'python-pillow-heif' 'python-multipart' 'python-cryptography'
          'python-fastapi' 'python-starlette' 'python-croniter' 'uvicorn'
          'python-httptools' 'python-watchfiles')
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
makedepends=('git' 'python-installer' 'python-wheel' 'python-build' 'python-setuptools' 'npm')
# Bun / JS bundles and generated assets should not be stripped.
options=('!strip' '!debug')
source=(
    "${_pkgname}::git+${url}.git#commit=${_commit}"
    "0002-use-hermes-wrapper-for-systemd-gateway.patch"
    "0003-preserve-system-python-for-arch-package.patch"
    "hermes-wrapper"
    "check-package.py"
)
sha256sums=('SKIP'
            '658cf475a1b8a064616136f2c2c659f97a8162ec4294ad8c8df4cfe03a41a6cc'
            'e433a8ed6b48ae6b7de2772bb797be96db7b0a5d54d45c9e72310bcac633f4ff'
            '904cd6e09ad691f7fefd90b2e13f03cf7e184917c3924ced34cfca16b9c456f8'
            'f9a48f9b8463194164bdeeb71230867915232ee0e6d9a13d29f144c936fa2d82')

prepare() {
  cd "${srcdir}/${_pkgname}"
  # Arch Linux packaging uses distro setuptools.
  # Relax upstream's setuptools pin so the package can build with
  # the current Arch Python toolchain.
  sed -i \
    -e 's/setuptools>=77.0,<83/setuptools>=77.0/' \
    -e 's/setuptools==83.0.0/setuptools>=77.0/' \
    -e "s/version = \"0.0.0\"/version = \"${pkgver}\"/" \
    pyproject.toml
  # Use the packaged hermes wrapper for generated systemd units.
  # This preserves HERMES_* runtime asset environment variables.
  patch -p1 < "${srcdir}/0002-use-hermes-wrapper-for-systemd-gateway.patch"
  patch -p1 < "${srcdir}/0003-preserve-system-python-for-arch-package.patch"
}

build() {
  cd "${srcdir}/${_pkgname}"

  # Upstream blocks normal wheel builds because runtime assets are not included.
  # We package those assets separately below, matching the upstream Nix layout.
  GIT_CEILING_DIRECTORIES="${srcdir}" python scripts/write_install_stamp.py --output install-stamp.json \
    --commit "${_commit}" --branch "v${tag}" --dirty --base-version "${pkgver}" --distance 0 \
    --source build --update-mechanism external
  HERMES_NIX_BUILD=1 python -m build --wheel --no-isolation --quiet

  # Build the dashboard and TUI from the upstream npm workspaces.
  # The dashboard outputs to hermes_cli/web_dist via vite.config.ts.
  npm ci --workspace web --workspace ui-tui --include-workspace-root \
    --silent --no-fund --no-audit --progress=false
  npm run --silent build --workspace web
  npm run --silent build --workspace ui-tui
}

check() {
  cd "${srcdir}/${_pkgname}"
  PYTHONPATH=. python "${srcdir}/check-package.py"
}

package() {
  cd "${srcdir}/${_pkgname}"

  python -m installer --destdir="${pkgdir}" --prefix=/usr dist/*.whl

  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"

  local _share="${pkgdir}/usr/share/hermes-agent"

  install -d "${_share}"
  install -m644 install-stamp.json "${_share}/install-stamp.json"

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
  install -Dm644 ui-tui/package.json "${pkgdir}/usr/lib/hermes-agent/ui-tui/package.json"

  install -d "${pkgdir}/usr/lib/hermes-agent"

  # Preserve the wheel-generated console scripts and wrap them with
  # the runtime environment required by the split asset layout.
  local _cmd
  for _cmd in hermes hermes-agent hermes-acp; do
      test -x "${pkgdir}/usr/bin/${_cmd}"
      mv "${pkgdir}/usr/bin/${_cmd}" "${pkgdir}/usr/lib/hermes-agent/${_cmd}.real"
      ln -s /usr/lib/hermes-agent/hermes-wrapper "${pkgdir}/usr/bin/${_cmd}"
  done

  install -Dm755 "${srcdir}/hermes-wrapper" "${pkgdir}/usr/lib/hermes-agent/hermes-wrapper"

  # Git checkouts inherit the build umask; packaged runtime files are public
  chmod -R a+rX "${pkgdir}/usr"

  # Packaging sanity checks.
  test -z "$(find "${pkgdir}/usr" -type d ! -perm -0555 -print -quit)"
  test -z "$(find "${pkgdir}/usr" -type f ! -perm -0444 -print -quit)"
  test -f "${_share}/plugins/platforms/wecom/plugin.yaml"
  test -d "${_share}/locales"
  test -d "${_share}/optional-mcps"
  test -f "${_share}/web_dist/index.html"
  test -f "${pkgdir}/usr/lib/hermes-agent/ui-tui/dist/entry.js"
  node --check "${pkgdir}/usr/lib/hermes-agent/ui-tui/dist/entry.js"
}
