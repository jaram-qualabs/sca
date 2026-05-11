"""
Validador de Parte B (frontend, React).

Levanta el dev server del candidato, abre Playwright headless, toma
screenshots en distintos viewports y estados, y verifica que los elementos
mínimos del mock estén presentes en el DOM.

A diferencia del validador de Parte B de backend (que valida un output JSON
contra el ground truth), acá la validación es **visual + estructural**:

- Visual: las screenshots se guardan a un directorio dedicado para que el
  corrector (humano o LLM multimodal) las compare contra el mock del PDF.
- Estructural: chequeamos en el DOM la presencia de los 5 grupos de elementos
  obligatorios del mock — tabs nivel 1, tabs nivel 2, header dinámico, lista
  de usuarios y botones inferiores.

El validador NO scorea criterios — eso lo hace el LLM con la ayuda de las
screenshots. Devuelve un `PartBFrontendResult` con flags y paths que el
skill `sca-corrector-frontend` consume.

Uso típico desde el skill:

    from sca.validators.part_b_frontend import validate
    result = validate(candidate_dir='/tmp/sca_work/<gid>/repo')
    print(result.summary())
    # Las screenshots quedan en result.output_dir

Requisitos del entorno:
- `node` y `npm` instalados (para el dev server).
- `node_modules/` ya presente en el repo del candidato (correr `npm install`
  antes — el validador NO lo hace porque puede tardar minutos).
- `playwright` y un browser (chromium) instalados:
    pip install --break-system-packages playwright
    python -m playwright install chromium

Limitaciones conocidas:
- No verifica fidelidad pixel-by-pixel contra el mock — eso lo hace el LLM
  multimodal mirando las screenshots.
- Si el dev server tarda más de `start_timeout_seconds` en arrancar, falla.
- Asume que el dev server corre en localhost:3000 (CRA), :5173 (Vite) o
  :3000/:4000 (Next). Otros puertos no se autodetectan.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# Puertos por defecto que probamos en orden, mapeados al stack que los usa.
DEFAULT_DEV_PORTS: List[Tuple[int, str]] = [
    (5173, 'vite'),
    (3000, 'cra/next'),
    (4000, 'next-alt'),
    (8080, 'webpack-dev-server'),
]


@dataclass
class PartBFrontendResult:
    """Resultado del validador de Parte B (frontend)."""

    passed: bool = False
    server_started: bool = False
    server_url: str = ''
    server_command: str = ''
    output_dir: str = ''
    screenshots: List[str] = field(default_factory=list)

    # Flags por elemento esperado del mock (estructural, no visual)
    has_level1_tabs: bool = False        # Content_module / Auth_module
    level1_tab_count: int = 0
    has_level2_tabs: bool = False        # Module 1..N (providers)
    level2_tab_count: int = 0
    has_dynamic_header: bool = False     # "Number of users in module N:" o similar
    has_user_list: bool = False
    user_list_count: int = 0
    has_action_buttons: bool = False     # Delete / Advice / Create / Submit
    action_buttons_found: List[str] = field(default_factory=list)

    # Errores que detectó el browser durante la corrida
    console_errors: List[str] = field(default_factory=list)
    page_errors: List[str] = field(default_factory=list)

    error: str = ''

    def summary(self) -> str:
        lines = ['=== Parte B (Frontend) ===']
        lines.append(f"  Server arrancó:        {'✅' if self.server_started else '❌'}")
        if self.server_url:
            lines.append(f"  URL:                   {self.server_url}")
        if self.server_command:
            lines.append(f"  Comando:               {self.server_command}")
        lines.append(f"  Tabs nivel 1:          {'✅' if self.has_level1_tabs else '❌'} ({self.level1_tab_count} encontrados)")
        lines.append(f"  Tabs nivel 2:          {'✅' if self.has_level2_tabs else '❌'} ({self.level2_tab_count} encontrados)")
        lines.append(f"  Header dinámico:       {'✅' if self.has_dynamic_header else '❌'}")
        lines.append(f"  Lista de usuarios:     {'✅' if self.has_user_list else '❌'} ({self.user_list_count} botones)")
        lines.append(f"  Botones inferiores:    {'✅' if self.has_action_buttons else '❌'} ({', '.join(self.action_buttons_found) or 'ninguno'})")
        if self.console_errors:
            lines.append(f"  Errores en consola:    {len(self.console_errors)}")
            for e in self.console_errors[:3]:
                lines.append(f"    · {e[:120]}")
        if self.page_errors:
            lines.append(f"  Errores de página:     {len(self.page_errors)}")
            for e in self.page_errors[:3]:
                lines.append(f"    · {e[:120]}")
        if self.screenshots:
            lines.append(f"  Screenshots ({len(self.screenshots)}):")
            for s in self.screenshots:
                lines.append(f"    · {s}")
        if self.error:
            lines.append(f"  Error: {self.error}")
        lines.append(f"  Resultado FINAL:       {'✅ OK' if self.passed else '❌ con observaciones'}")
        return '\n'.join(lines)


def _detect_dev_command(candidate_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Determina el comando para levantar el dev server desde `package.json`.

    Devuelve (comando, stack_label). Por ejemplo:
      ('npm run dev', 'vite')
      ('npm start', 'cra')
    """
    pkg = candidate_dir / 'package.json'
    if not pkg.exists():
        return None, None
    try:
        data = json.loads(pkg.read_text(encoding='utf-8'))
    except Exception:
        return None, None

    scripts = data.get('scripts', {}) or {}
    deps = {**(data.get('dependencies') or {}), **(data.get('devDependencies') or {})}

    # Heurísticas en orden: stack más específico primero.
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


def _wait_for_server(url: str, timeout_seconds: int) -> bool:
    """Polea la URL hasta que responda o se acabe el timeout."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def _detect_running_port(default_ports: List[Tuple[int, str]]) -> Optional[int]:
    """Detecta cuál de los puertos default tiene un server escuchando."""
    for port, _ in default_ports:
        try:
            with socket.create_connection(('localhost', port), timeout=0.3):
                return port
        except OSError:
            continue
    return None


def _spawn_dev_server(
    candidate_dir: Path,
    command: str,
    log_file: Path,
) -> subprocess.Popen:
    """
    Lanza el dev server como subprocess. Redirige stdout/stderr a log_file.

    El proceso queda como "process group leader" (start_new_session=True) para
    que podamos matarlo a él y a sus hijos al terminar.
    """
    env = os.environ.copy()
    # CRA: que NO abra el browser automáticamente.
    env['BROWSER'] = 'none'
    env['CI'] = 'true'  # Suprime prompts interactivos en muchos servers.
    # Compatibilidad con webpack 4 + OpenSSL 3 (Node 17+): sin esto, CRA 4
    # crashea con ERR_OSSL_EVP_UNSUPPORTED en md4. Inofensivo para stacks
    # nuevos que no usan ese algoritmo.
    existing_node_opts = env.get('NODE_OPTIONS', '')
    if '--openssl-legacy-provider' not in existing_node_opts:
        env['NODE_OPTIONS'] = (
            f'{existing_node_opts} --openssl-legacy-provider'.strip()
        )

    log_fh = open(log_file, 'w')
    proc = subprocess.Popen(
        command,
        shell=True,
        cwd=str(candidate_dir),
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )
    return proc


def _kill_dev_server(proc: Optional[subprocess.Popen]) -> None:
    """Mata el proceso del dev server y todo su grupo."""
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), 15)  # SIGTERM al grupo
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), 9)  # SIGKILL
    except (ProcessLookupError, PermissionError):
        pass


def _run_playwright_checks(
    server_url: str,
    output_dir: Path,
    result: PartBFrontendResult,
) -> None:
    """
    Abre el browser headless, toma screenshots y rellena los flags
    estructurales del result.

    Modifica `result` in-place. Captura excepciones de Playwright y las
    pone en `result.error` si el flow se rompe.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        result.error = (
            'Playwright no está instalado. Correr: '
            'pip install --break-system-packages playwright && '
            'python -m playwright install chromium'
        )
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 900})

            # Capturar errores de consola y de página.
            page.on('console', lambda msg: (
                result.console_errors.append(msg.text)
                if msg.type == 'error' else None
            ))
            page.on('pageerror', lambda exc: result.page_errors.append(str(exc)))

            page.goto(server_url, wait_until='networkidle', timeout=15000)
            page.wait_for_timeout(500)

            # ── Screenshot 1: estado inicial ─────────────────────────────
            sc1 = output_dir / '01-initial.png'
            page.screenshot(path=str(sc1), full_page=True)
            result.screenshots.append(str(sc1))

            # ── Estructura: tabs nivel 1 ─────────────────────────────────
            # Buscamos botones/links cuyo texto contenga las palabras esperadas.
            # Lectura tolerante: "auth_module", "Auth_module", "AUTH", etc.
            level1_pattern = re.compile(r'(auth|content)[_\s]*module', re.IGNORECASE)
            level1_candidates = page.locator('button, a, label, [role="tab"], li').all()
            level1_matches = []
            for el in level1_candidates:
                try:
                    text = (el.text_content() or '').strip()
                    if level1_pattern.search(text):
                        level1_matches.append(text)
                except Exception:
                    continue
            # Deduplicar conservando orden y filtrando textos demasiado largos
            # (pueden ser un contenedor que envuelve a varios).
            seen = set()
            level1_unique = []
            for t in level1_matches:
                if len(t) <= 60 and t not in seen:
                    seen.add(t)
                    level1_unique.append(t)
            result.level1_tab_count = len(level1_unique)
            result.has_level1_tabs = len(level1_unique) >= 2

            # ── Estructura: lista de usuarios ────────────────────────────
            # Heurística: cualquier elemento clickeable cuyo texto matchee
            # un id de usuario. Aceptamos las formas:
            #   u0, u0.json, ./u0.json, /u0.json, user 0, User N
            user_pattern = re.compile(
                r'^(\./|/)?u\d+(\.json)?$|^user\s*\d+$',
                re.IGNORECASE,
            )
            user_count = 0
            for el in page.locator('button, li, a, span').all():
                try:
                    text = (el.text_content() or '').strip()
                    if user_pattern.match(text):
                        user_count += 1
                except Exception:
                    continue
            result.user_list_count = user_count
            result.has_user_list = user_count >= 1

            # ── Estructura: header dinámico ──────────────────────────────
            # Buscamos un texto tipo "Number of users in <algo>".
            page_text = page.content()
            result.has_dynamic_header = bool(
                re.search(r'number\s+of\s+users\s+in', page_text, re.IGNORECASE)
            )

            # ── Estructura: botones inferiores ───────────────────────────
            expected_actions = ['delete', 'advice', 'create', 'submit']
            actions_found = []
            for action in expected_actions:
                try:
                    loc = page.get_by_text(re.compile(rf'^\s*{action}\s*$', re.IGNORECASE))
                    if loc.count() > 0:
                        actions_found.append(action.capitalize())
                except Exception:
                    continue
            result.action_buttons_found = actions_found
            result.has_action_buttons = len(actions_found) >= 3  # al menos 3 de 4

            # ── Screenshot 2: tras click en la 2a tab nivel 1 ────────────
            # Si hay más de una, clickeamos la segunda para capturar el cambio.
            if result.level1_tab_count >= 2:
                try:
                    second_tab = level1_candidates[level1_matches.index(level1_unique[1])]
                    second_tab.click(timeout=2000)
                    page.wait_for_timeout(500)
                    sc2 = output_dir / '02-after-click-level1.png'
                    page.screenshot(path=str(sc2), full_page=True)
                    result.screenshots.append(str(sc2))
                except Exception:
                    pass

            # ── Estructura: tabs nivel 2 (después de seleccionar nivel 1) ──
            # Heurística: botones cuyo texto matchee /(provider|module)\s*\d+/
            # o un string corto que cambia al cambiar de nivel 1.
            level2_pattern = re.compile(
                r'(provider|module)\s*\d+|authn\.|authz\.|^module\s*\w+$',
                re.IGNORECASE,
            )
            level2_matches = set()
            for el in page.locator('button, a, label, [role="tab"]').all():
                try:
                    text = (el.text_content() or '').strip()
                    if level2_pattern.search(text) and len(text) <= 40:
                        level2_matches.add(text)
                except Exception:
                    continue
            result.level2_tab_count = len(level2_matches)
            result.has_level2_tabs = len(level2_matches) >= 2

            # ── Screenshot 3: mobile viewport ────────────────────────────
            page.set_viewport_size({'width': 380, 'height': 800})
            page.wait_for_timeout(300)
            sc3 = output_dir / '03-mobile.png'
            page.screenshot(path=str(sc3), full_page=True)
            result.screenshots.append(str(sc3))

        finally:
            browser.close()


def validate(
    candidate_dir: str,
    *,
    output_dir: Optional[str] = None,
    start_timeout_seconds: int = 60,
    keep_server_log: bool = True,
) -> PartBFrontendResult:
    """
    Valida la Parte B (frontend) levantando la app del candidato y tomando
    screenshots con Playwright headless.

    Args:
        candidate_dir: ruta al repo del candidato (con `package.json` y
            `node_modules/` ya instalado).
        output_dir: carpeta donde guardar las screenshots. Default:
            `<candidate_dir>/.sca-screenshots/`.
        start_timeout_seconds: cuánto esperar a que arranque el dev server.
        keep_server_log: si True, deja el log del dev server al lado de las
            screenshots para diagnosticar.

    Returns:
        PartBFrontendResult con:
        - paths absolutos a las screenshots tomadas
        - flags estructurales (tabs, header, lista, botones)
        - errores de consola/página detectados
        - mensaje de error si el flow se rompió
    """
    candidate_path = Path(candidate_dir).expanduser().resolve()
    if not candidate_path.is_dir():
        return PartBFrontendResult(error=f'Directorio no existe: {candidate_path}')

    if not (candidate_path / 'node_modules').is_dir():
        return PartBFrontendResult(
            error=(
                'node_modules/ no está presente. Correr `npm install` '
                f'(o equivalente) en {candidate_path} antes de validar.'
            )
        )

    out_path = Path(output_dir) if output_dir else candidate_path / '.sca-screenshots'
    out_path.mkdir(parents=True, exist_ok=True)

    result = PartBFrontendResult(output_dir=str(out_path))

    command, stack = _detect_dev_command(candidate_path)
    if not command:
        result.error = 'No pude detectar comando de dev server en package.json'
        return result
    result.server_command = command

    log_file = out_path / 'dev-server.log'

    proc: Optional[subprocess.Popen] = None
    try:
        proc = _spawn_dev_server(candidate_path, command, log_file)

        # Probar puertos default hasta encontrar el server arriba.
        port = None
        deadline = time.time() + start_timeout_seconds
        while time.time() < deadline and port is None:
            if proc.poll() is not None:
                # El server murió; leer el log para reportar.
                try:
                    log_tail = log_file.read_text()[-2000:]
                except Exception:
                    log_tail = '(no log disponible)'
                result.error = f'dev server murió antes de arrancar:\n{log_tail}'
                return result
            port = _detect_running_port(DEFAULT_DEV_PORTS)
            if port is None:
                time.sleep(0.5)

        if port is None:
            result.error = f'dev server no arrancó en ninguno de los puertos {DEFAULT_DEV_PORTS} dentro de {start_timeout_seconds}s'
            return result

        result.server_url = f'http://localhost:{port}'
        # Pequeña espera adicional para que termine el bundling.
        if not _wait_for_server(result.server_url, timeout_seconds=15):
            result.error = f'el server escucha en {port} pero no responde HTTP'
            return result

        result.server_started = True

        # Correr los chequeos con Playwright.
        _run_playwright_checks(result.server_url, out_path, result)

    except Exception as e:
        result.error = f'excepción no esperada: {type(e).__name__}: {e}'
    finally:
        _kill_dev_server(proc)
        if not keep_server_log:
            try:
                log_file.unlink(missing_ok=True)
            except Exception:
                pass

    # Resultado "passed": el server arrancó y se vieron los grupos mínimos
    # (tabs nivel 1 + lista de usuarios + 3 de 4 botones inferiores).
    result.passed = (
        result.server_started
        and result.has_level1_tabs
        and result.has_user_list
        and result.has_action_buttons
    )

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python part_b_frontend.py <candidate_dir> [output_dir]')
        sys.exit(1)

    candidate_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    result = validate(candidate_dir, output_dir=output_dir)
    print(result.summary())
    sys.exit(0 if result.passed else 1)
