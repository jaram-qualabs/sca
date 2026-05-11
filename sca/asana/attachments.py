"""
Wrapper para subir attachments a una task de Asana.

El conector MCP de Asana no expone `create_attachment`. Asana REST sí
acepta `POST /api/1.0/attachments` con `multipart/form-data`. Este módulo
es un wrapper minimalista sobre `urllib` (sin dependencias externas).

Requiere un Personal Access Token de Asana en la env var `ASANA_PAT`:

    1. Asana → Profile → My Settings → Apps → Manage Developer Apps
    2. Personal access tokens → New access token
    3. Copiar el token y setear como env var en la Routine.

Convive con el conector MCP que sigue manejando el resto (tasks, comments,
subtasks). Esto solo cubre el upload, que MCP no soporta.

Uso típico desde la Routine, después de crear la subtask con el feedback:

    from sca.asana.attachments import upload_attachments
    result = upload_attachments(
        task_gid=subtask_gid,
        file_paths=['/tmp/sca-fe-01.png', '/tmp/sca-fe-02.png'],
        pat=os.environ['ASANA_PAT'],
    )
    print(result.summary())
"""

from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


ASANA_ATTACHMENTS_URL = 'https://app.asana.com/api/1.0/attachments'


@dataclass
class UploadResult:
    """Resultado de subir un lote de attachments a una task."""

    task_gid: str = ''
    uploaded: List[Dict[str, Any]] = field(default_factory=list)
    """Cada item tiene `{'gid', 'name', 'permanent_url', 'local_path'}`."""

    failed: List[Dict[str, str]] = field(default_factory=list)
    """Cada item tiene `{'local_path', 'error'}`."""

    @property
    def all_succeeded(self) -> bool:
        return bool(self.uploaded) and not self.failed

    def summary(self) -> str:
        lines = ['=== Upload attachments a Asana ===']
        lines.append(f'  Task GID:   {self.task_gid}')
        lines.append(f'  OK:         {len(self.uploaded)}')
        lines.append(f'  Fallidos:   {len(self.failed)}')
        for u in self.uploaded:
            lines.append(f"    ✅ {u.get('name', '?')} → {u.get('permanent_url', u.get('gid', '?'))}")
        for f in self.failed:
            lines.append(f"    ❌ {f.get('local_path', '?')}: {f.get('error', '?')[:120]}")
        return '\n'.join(lines)


def _build_multipart_body(
    boundary: str,
    task_gid: str,
    file_name: str,
    mime_type: str,
    file_bytes: bytes,
) -> bytes:
    """Construye el cuerpo multipart/form-data para POST /attachments."""
    parts = bytearray()
    # Field: parent (GID de la task)
    parts.extend(f'--{boundary}\r\n'.encode())
    parts.extend(b'Content-Disposition: form-data; name="parent"\r\n\r\n')
    parts.extend(task_gid.encode())
    parts.extend(b'\r\n')
    # Field: file (el binario)
    parts.extend(f'--{boundary}\r\n'.encode())
    parts.extend(
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'.encode()
    )
    parts.extend(f'Content-Type: {mime_type}\r\n\r\n'.encode())
    parts.extend(file_bytes)
    parts.extend(b'\r\n')
    # Closing boundary
    parts.extend(f'--{boundary}--\r\n'.encode())
    return bytes(parts)


def upload_attachment(
    task_gid: str,
    file_path: str | os.PathLike,
    pat: str,
    *,
    name: Optional[str] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Sube un archivo como attachment a una task de Asana.

    Args:
        task_gid: GID de la task de Asana (la subtask de feedback).
        file_path: ruta al archivo local a subir (PNG, PDF, etc.).
        pat: Personal Access Token de Asana (Bearer token).
        name: nombre con el que aparece el attachment en Asana. Default:
            el nombre del archivo en disco.
        timeout: timeout HTTP en segundos.

    Returns:
        El objeto `data` que devuelve Asana, con campos como `gid`, `name`,
        `permanent_url`, `download_url`, `view_url`.

    Raises:
        FileNotFoundError: si `file_path` no existe.
        ValueError: si la API devuelve un error HTTP (incluye el body de
            respuesta para diagnosticar).
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f'No existe: {path}')

    file_name = name or path.name
    mime, _ = mimetypes.guess_type(file_name)
    mime = mime or 'application/octet-stream'
    file_bytes = path.read_bytes()

    boundary = f'------------SCA{uuid.uuid4().hex}'
    body = _build_multipart_body(boundary, task_gid, file_name, mime, file_bytes)

    req = urllib.request.Request(
        ASANA_ATTACHMENTS_URL,
        data=body,
        method='POST',
        headers={
            'Authorization': f'Bearer {pat}',
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Accept': 'application/json',
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            return payload.get('data', {}) or {}
    except urllib.error.HTTPError as e:
        # Asana devuelve JSON con el error en el body — lo incluimos para
        # diagnosticar (`{"errors":[{"message":"..."}]}`).
        try:
            err_body = e.read().decode('utf-8', errors='replace')
        except Exception:
            err_body = '(no body)'
        raise ValueError(
            f'Asana API HTTP {e.code} subiendo {path.name}: {err_body[:500]}'
        )
    except urllib.error.URLError as e:
        raise ValueError(
            f'Asana API conexión falló subiendo {path.name}: {e.reason}'
        )


def upload_attachments(
    task_gid: str,
    file_paths: List[str | os.PathLike],
    pat: str,
    *,
    timeout: int = 60,
) -> UploadResult:
    """
    Sube una lista de archivos a una task. Errores per-file NO abortan el
    batch — quedan registrados en `result.failed` y el loop continúa.

    Args:
        task_gid: GID de la task destino.
        file_paths: lista de paths locales.
        pat: Personal Access Token de Asana.
        timeout: timeout HTTP por archivo.

    Returns:
        UploadResult con dos listas: `uploaded` (los exitosos) y `failed`.
    """
    result = UploadResult(task_gid=task_gid)
    for p in file_paths:
        path = Path(p)
        try:
            data = upload_attachment(task_gid, path, pat, timeout=timeout)
            result.uploaded.append({
                'gid':            data.get('gid', ''),
                'name':           data.get('name', path.name),
                'permanent_url':  data.get('permanent_url', ''),
                'download_url':   data.get('download_url', ''),
                'view_url':       data.get('view_url', ''),
                'local_path':     str(path),
            })
        except Exception as e:
            result.failed.append({
                'local_path': str(path),
                'error':      f'{type(e).__name__}: {e}',
            })
    return result


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print(
            'Uso: python -m sca.asana.attachments <task_gid> <file1> [<file2> ...]'
            '\n  Requiere env var ASANA_PAT.'
        )
        sys.exit(1)
    pat = os.environ.get('ASANA_PAT')
    if not pat:
        print('Error: la env var ASANA_PAT no está seteada.')
        sys.exit(2)
    task = sys.argv[1]
    files = sys.argv[2:]
    res = upload_attachments(task, files, pat)
    print(res.summary())
    sys.exit(0 if res.all_succeeded else 1)
