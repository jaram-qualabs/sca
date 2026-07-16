"""
Fixture HLS local y reproducible para el validador FE v2.

Genera con ffmpeg un stream HLS VOD de 12s con 2 variantes (360p/720p) en
**VP9 + Opus (fMP4)** y lo sirve por HTTP con CORS habilitado.

¿Por qué VP9 y no H.264? El chromium que instala Playwright es el build
open-source SIN codecs propietarios: no decodifica h264/aac. Con un stream
h264 (como el de test-streams.mux.dev), hls.js corta en
`manifestIncompatibleCodecsError` y el chequeo del player siempre da falso
negativo. Con VP9+Opus la reproducción es real: el validador puede verificar
`currentTime > 0` y requests de segmentos.

¿Por qué CORS? La SPA del candidato corre en :5173 y pide el manifest a
:9000 — sin `Access-Control-Allow-Origin: *`, hls.js no puede fetchearlo.

Uso (generar + servir, bloqueante — correr en background):

    python3 -m sca.v2.validators.fixture --dir /tmp/sca_hls_fixture --port 9000 &

El manifest queda en `http://127.0.0.1:<port>/master.m3u8`. La generación es
idempotente: si el fixture ya existe, solo sirve.

Requiere `ffmpeg` con libvpx-vp9 y libopus (el ffmpeg de apt los trae).
"""

from __future__ import annotations

import argparse
import functools
import http.server
import subprocess
import sys
from pathlib import Path

VARIANTS = [
    # (altura, tamaño, bitrate_video, bandwidth_master)
    (360, '640x360', '400k', 500000),
    (720, '1280x720', '1200k', 1300000),
]
DURATION_S = 12
SEGMENT_S = 4


def ensure_fixture(directory: str | Path) -> Path:
    """Genera el fixture si no existe. Devuelve el path a master.m3u8."""
    root = Path(directory)
    master = root / 'master.m3u8'
    if master.exists() and all((root / f'{h}p' / 'index.m3u8').exists() for h, *_ in VARIANTS):
        return master

    root.mkdir(parents=True, exist_ok=True)
    for height, size, vbitrate, _bw in VARIANTS:
        out = root / f'{height}p'
        out.mkdir(exist_ok=True)
        cmd = [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-f', 'lavfi', '-i', f'testsrc2=size={size}:rate=25',
            '-f', 'lavfi', '-i', 'sine=frequency=440',
            '-t', str(DURATION_S),
            '-c:v', 'libvpx-vp9', '-b:v', vbitrate, '-deadline', 'realtime', '-cpu-used', '8',
            # Keyframe exacto cada SEGMENT_S: sin esto los segmentos exceden
            # TARGETDURATION y el validate() del backend provisto los rechaza
            # (y parse_manifest devuelve 500).
            '-force_key_frames', f'expr:gte(t,n_forced*{SEGMENT_S})',
            '-c:a', 'libopus', '-b:a', '48k',
            '-hls_time', str(SEGMENT_S), '-hls_playlist_type', 'vod',
            '-hls_segment_type', 'fmp4',
            '-hls_fmp4_init_filename', 'init.mp4',
            '-hls_segment_filename', str(out / 'seg%d.m4s'),
            str(out / 'index.m3u8'),
        ]
        subprocess.run(cmd, check=True, cwd=str(root))
        # ffmpeg deja init.mp4 en el cwd — moverlo junto a su variante.
        init = root / 'init.mp4'
        if init.exists():
            init.replace(out / 'init.mp4')

    lines = ['#EXTM3U', '#EXT-X-VERSION:7']
    for height, size, _vb, bandwidth in VARIANTS:
        profile = '21' if height <= 480 else '31'
        lines.append(
            f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={size},'
            f'CODECS="vp09.00.{profile}.08,opus"'
        )
        lines.append(f'{height}p/index.m3u8')
    master.write_text('\n'.join(lines) + '\n')
    return master


class _CorsHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, *args):  # silencioso
        pass


def serve(directory: str | Path, port: int = 9000) -> None:
    """Sirve el fixture con CORS. Bloqueante — correr en background."""
    handler = functools.partial(_CorsHandler, directory=str(directory))
    http.server.ThreadingHTTPServer(('127.0.0.1', port), handler).serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description='Genera y sirve el fixture HLS del SCA v2.')
    parser.add_argument('--dir', default='/tmp/sca_hls_fixture')
    parser.add_argument('--port', type=int, default=9000)
    parser.add_argument('--no-serve', action='store_true', help='Solo generar, no servir.')
    args = parser.parse_args()

    master = ensure_fixture(args.dir)
    print(f'Fixture listo: {master}', file=sys.stderr)
    if not args.no_serve:
        print(f'Sirviendo http://127.0.0.1:{args.port}/master.m3u8', file=sys.stderr)
        serve(args.dir, args.port)
    return 0


if __name__ == '__main__':
    sys.exit(main())
