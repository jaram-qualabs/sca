"""
Validador funcional de la prueba de FRONTEND v2 (dashboard HLS).

Levanta el dev server del candidato, abre Playwright headless y recorre los
3 requerimientos de la letra tomando screenshots como evidencia:

1. **Dashboard**: ingresa la URL de un manifest en el input, dispara el
   análisis y verifica que aparezca el resultado de validación y gráficos.
2. **Filtro**: detecta los sliders de resolución, intenta aplicar el filtro y
   verifica que aparezca el manifest filtrado.
3. **Player**: detecta el elemento <video>, intenta reproducir y mide
   readyState/currentTime; cuenta los selectores de calidad/audio.

El validador NO scorea criterios — eso lo hace el LLM con estas señales y
las screenshots. Devuelve un `FrontendV2Result` que el skill
`sca-corrector-frontend-v2` y la Routine (`routine/v2/CORRECCION.md`)
consumen.

⚠️ Autocontenido de v2: no importa nada de `sca/validators/` (v1). Los
patrones de boot/kill del dev server están adaptados de allá a propósito,
para que borrar v1 no rompa esto.

Requisitos del entorno:
- `node`/`npm`, `node_modules/` ya instalado en el repo del candidato.
- El **backend provisto** corriendo (default `http://127.0.0.1:8000`) — la
  SPA lo consume. Levantarlo desde `new-technical-test/Frontend/Backend/`.
- `playwright` + chromium:
    pip install --break-system-packages playwright
    python -m playwright install chromium
- Un manifest HLS alcanzable (default: el stream de prueba de la letra —
  requiere red hacia `test-streams.mux.dev`).

Uso típico:

    from sca.v2.validators.frontend import validate
    result = validate('/tmp/sca_work/<gid>/candidato', output_dir='.../screenshots')
    print(result.summary())
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

DEFAULT_MANIFEST = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8'
DEFAULT_BACKEND = 'http://127.0.0.1:8000'

# Puertos default de dev servers, en orden de prueba.
DEFAULT_DEV_PORTS: List[Tuple[int, str]] = [
    (5173, 'vite'),
    (3000, 'cra/next'),
    (4000, 'next-alt'),
    (8080, 'webpack-dev-server'),
]

ANALYZE_BUTTON = re.compile(r'analiz|valid|cargar|load|check|submit|parse', re.IGNORECASE)
FILTER_BUTTON = re.compile(r'filtr|apply|aplicar', re.IGNORECASE)


@dataclass
class FrontendV2Result:
    """Señales funcionales de la prueba FE v2. Un flag por evidencia."""

    passed: bool = False
    server_started: bool = False
    server_url: str = ''
    server_command: str = ''
    backend_reachable: bool = False
    output_dir: str = ''
    screenshots: List[str] = field(default_factory=list)

    # Req 1 — Dashboard
    url_input_found: bool = False
    validation_shown: bool = False       # F307
    charts_count: int = 0                # F309 (canvas + svg detectados)

    # Req 2 — Filtro
    sliders_count: int = 0               # F311 (inputs type=range)
    filter_applied: bool = False         # F312 (apareció un m3u8 tras filtrar)

    # Req 3 — Player
    video_found: bool = False            # F314 (elemento <video>)
    video_ready: bool = False            # F314 (readyState >= 2: hay media decodificable)
    video_playing: bool = False          # F314 (currentTime avanzó)
    manifest_requests: int = 0           # F314 (requests .m3u8 del player)
    segment_requests: int = 0            # F314 (requests .ts/.m4s: el player cargó el stream)
    media_selectors_count: int = 0       # F315/F316 (selects de calidad/audio)

    console_errors: List[str] = field(default_factory=list)
    page_errors: List[str] = field(default_factory=list)
    error: str = ''

    def summary(self) -> str:
        def flag(b): return '✅' if b else '❌'
        lines = ['=== Frontend v2 (dashboard HLS) ===']
        lines.append(f"  Server arrancó:       {flag(self.server_started)}  {self.server_url}")
        lines.append(f"  Backend provisto:     {flag(self.backend_reachable)}")
        lines.append(f"  Input de URL:         {flag(self.url_input_found)}")
        lines.append(f"  Validación visible:   {flag(self.validation_shown)}  (F307)")
        lines.append(f"  Gráficos detectados:  {self.charts_count}  (F309)")
        lines.append(f"  Sliders:              {self.sliders_count}  (F311)")
        lines.append(f"  Filtro aplicado:      {flag(self.filter_applied)}  (F312)")
        lines.append(
            f"  Player:               video={flag(self.video_found)} "
            f"ready={flag(self.video_ready)} playing={flag(self.video_playing)} "
            f"m3u8={self.manifest_requests} segs={self.segment_requests}  (F314)"
        )
        lines.append(
            "  ↳ Nota: el chromium de Playwright no decodifica h264/aac —"
            " ready/playing pueden dar ❌ con el player andando. La evidencia"
            " robusta de F314 es segs > 0 (el player pidió segmentos)."
        )
        lines.append(f"  Selects calidad/audio: {self.media_selectors_count}  (F315/F316)")
        if self.console_errors:
            lines.append(f"  Errores de consola:   {len(self.console_errors)}")
            for e in self.console_errors[:3]:
                lines.append(f"    · {e[:120]}")
        if self.page_errors:
            lines.append(f"  Errores de página:    {len(self.page_errors)}")
        for s in self.screenshots:
            lines.append(f"  📸 {s}")
        if self.error:
            lines.append(f"  Error: {self.error}")
        lines.append(f"  Resultado FINAL:      {'✅ OK' if self.passed else '❌ con observaciones'}")
        return '\n'.join(lines)


def _detect_dev_command(candidate_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """Comando de dev server según package.json (vite/next/cra/genérico)."""
    pkg = candidate_dir / 'package.json'
    if not pkg.exists():
        return None, None
    try:
        data = json.loads(pkg.read_text(encoding='utf-8'))
    except Exception:
        return None, None
    scripts = data.get('scripts', {}) or {}
    deps = {**(data.get('dependencies') or {}), **(data.get('devDependencies') or {})}
    if 'vite' in deps and 'dev' in scripts:
        return 'npm run dev', 'vite'
    if 'next' in deps and 'dev' in scripts:
        return 'npm run dev', 'next'
    if 'react-scripts' in deps and 'start' in scripts:
        return 'npm start', 'cra'
    if 'dev' in scripts:
        return 'npm run dev', 'unknown-dev'
    if 'start' in scripts:
        return 'npm start', 'unknown-start'
    return None, None


def _detect_running_port() -> Optional[int]:
    for port, _ in DEFAULT_DEV_PORTS:
        try:
            with socket.create_connection(('localhost', port), timeout=0.3):
                return port
        except OSError:
            continue
    return None


def _url_ok(url: str, timeout: int = 3) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status < 500
    except Exception:
        return False


def _spawn_dev_server(candidate_dir: Path, command: str, log_file: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env['BROWSER'] = 'none'
    env['CI'] = 'true'
    log_fh = open(log_file, 'w')
    return subprocess.Popen(
        command, shell=True, cwd=str(candidate_dir),
        stdout=log_fh, stderr=subprocess.STDOUT, env=env, start_new_session=True,
    )


def _kill_dev_server(proc: Optional[subprocess.Popen]) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), 15)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), 9)
    except (ProcessLookupError, PermissionError):
        pass


def _shot(page, out: Path, name: str, result: FrontendV2Result) -> None:
    path = out / name
    try:
        page.screenshot(path=str(path), full_page=True)
        result.screenshots.append(str(path))
    except Exception:
        pass


def _run_playwright(server_url: str, manifest_url: str, out: Path, result: FrontendV2Result) -> None:
    """Recorre la app y rellena las señales. Modifica `result` in-place."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        result.error = (
            'Playwright no instalado: pip install --break-system-packages playwright '
            '&& python -m playwright install chromium'
        )
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.on('console', lambda m: result.console_errors.append(m.text)
                    if m.type == 'error' else None)
            page.on('pageerror', lambda e: result.page_errors.append(str(e)))

            def _track_request(req):
                url = req.url.split('?')[0]
                if url.endswith('.m3u8') or 'filter_manifest' in url:
                    result.manifest_requests += 1
                elif url.endswith(('.ts', '.m4s', '.mp4', '.aac')):
                    result.segment_requests += 1
            page.on('request', _track_request)

            page.goto(server_url, wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(1500)
            _shot(page, out, '01-initial.png', result)

            # ── Req 1: ingresar URL y analizar ───────────────────────────
            url_input = page.locator('input[type="url"], input[type="text"]').first
            if url_input.count() > 0:
                result.url_input_found = True
                url_input.fill(manifest_url)
                clicked = False
                for btn in page.locator('button').all():
                    try:
                        if ANALYZE_BUTTON.search(btn.text_content() or ''):
                            btn.click(timeout=3000)
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    url_input.press('Enter')
                page.wait_for_timeout(6000)  # validate + parse pueden tardar

                body = page.inner_text('body')
                result.validation_shown = bool(re.search(
                    r'v[aá]lid|valid|inv[aá]lid|✅|❌|error', body, re.IGNORECASE))
                result.charts_count = page.locator('canvas, svg').count()
                _shot(page, out, '02-dashboard.png', result)

            # ── Req 2: sliders + aplicar filtro ──────────────────────────
            result.sliders_count = page.locator('input[type="range"]').count()
            if result.sliders_count:
                for btn in page.locator('button').all():
                    try:
                        if FILTER_BUTTON.search(btn.text_content() or ''):
                            btn.click(timeout=3000)
                            break
                    except Exception:
                        continue
                page.wait_for_timeout(4000)
                body = page.inner_text('body')
                in_widgets = ' '.join(
                    (el.input_value() or '') for el in page.locator('textarea').all())
                result.filter_applied = '#EXTM3U' in body or '#EXTM3U' in in_widgets \
                    or '#EXT-X-STREAM-INF' in body
                _shot(page, out, '03-filter.png', result)

            # ── Req 3: player ────────────────────────────────────────────
            video = page.locator('video').first
            if video.count() > 0:
                result.video_found = True
                page.evaluate(
                    "() => { const v = document.querySelector('video');"
                    " if (v) { v.muted = true; v.play().catch(() => {}); } }")
                page.wait_for_timeout(6000)
                state = page.evaluate(
                    "() => { const v = document.querySelector('video');"
                    " return v ? {rs: v.readyState, t: v.currentTime} : null; }")
                if state:
                    result.video_ready = state['rs'] >= 2
                    result.video_playing = state['t'] > 0
                _shot(page, out, '04-player.png', result)
                # Selects de calidad/audio cerca del player
                result.media_selectors_count = page.locator('select').count()

            # ── Mobile ───────────────────────────────────────────────────
            page.set_viewport_size({'width': 380, 'height': 800})
            page.wait_for_timeout(500)
            _shot(page, out, '05-mobile.png', result)

        finally:
            browser.close()


def validate(
    candidate_dir: str,
    *,
    manifest_url: str = DEFAULT_MANIFEST,
    backend_url: str = DEFAULT_BACKEND,
    output_dir: Optional[str] = None,
    start_timeout_seconds: int = 90,
) -> FrontendV2Result:
    """
    Valida la app FE v2 del candidato end-to-end y toma screenshots.

    Args:
        candidate_dir: repo del candidato (con node_modules ya instalado).
        manifest_url: manifest HLS para el recorrido (default: el de la letra).
        backend_url: dónde corre el backend FastAPI provisto.
        output_dir: carpeta de screenshots (default <candidato>/.sca-screenshots).
    """
    candidate_path = Path(candidate_dir).expanduser().resolve()
    if not candidate_path.is_dir():
        return FrontendV2Result(error=f'Directorio no existe: {candidate_path}')
    if not (candidate_path / 'node_modules').is_dir():
        return FrontendV2Result(error='node_modules/ ausente — correr npm install antes.')

    out = Path(output_dir) if output_dir else candidate_path / '.sca-screenshots'
    out.mkdir(parents=True, exist_ok=True)
    result = FrontendV2Result(output_dir=str(out))

    result.backend_reachable = _url_ok(f'{backend_url}/docs')
    if not result.backend_reachable:
        # No abortamos: la app puede embeber su propio backend. Queda la señal.
        print(f'⚠️ Backend provisto no responde en {backend_url}', file=sys.stderr)

    command, _stack = _detect_dev_command(candidate_path)
    if not command:
        result.error = 'No pude detectar comando de dev server en package.json'
        return result
    result.server_command = command

    log_file = out / 'dev-server.log'
    proc: Optional[subprocess.Popen] = None
    try:
        proc = _spawn_dev_server(candidate_path, command, log_file)
        port, deadline = None, time.time() + start_timeout_seconds
        while time.time() < deadline and port is None:
            if proc.poll() is not None:
                tail = log_file.read_text()[-2000:] if log_file.exists() else '(sin log)'
                result.error = f'dev server murió antes de arrancar:\n{tail}'
                return result
            port = _detect_running_port()
            if port is None:
                time.sleep(0.5)
        if port is None:
            result.error = f'dev server no arrancó en {start_timeout_seconds}s'
            return result

        result.server_url = f'http://localhost:{port}'
        if not _url_ok(result.server_url, timeout=5):
            result.error = f'el server escucha en {port} pero no responde HTTP'
            return result
        result.server_started = True

        _run_playwright(result.server_url, manifest_url, out, result)

    except Exception as e:
        result.error = f'excepción no esperada: {type(e).__name__}: {e}'
    finally:
        _kill_dev_server(proc)

    # passed = evidencia mínima de los 3 requerimientos. Para el player, la
    # señal robusta en headless es que haya pedido segmentos (los codecs
    # h264/aac no están en el chromium de Playwright, así que readyState y
    # currentTime no son confiables).
    result.passed = (
        result.server_started
        and result.validation_shown
        and result.sliders_count >= 1
        and result.video_found
        and (result.segment_requests > 0 or result.video_ready)
    )
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python -m sca.v2.validators.frontend <candidate_dir> [output_dir] [manifest_url]')
        sys.exit(1)
    r = validate(
        sys.argv[1],
        output_dir=sys.argv[2] if len(sys.argv) > 2 else None,
        manifest_url=sys.argv[3] if len(sys.argv) > 3 else DEFAULT_MANIFEST,
    )
    print(r.summary())
    sys.exit(0 if r.passed else 1)
