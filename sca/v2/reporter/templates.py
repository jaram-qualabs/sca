"""
Templates de reporting del SCA **v2** — prueba técnica nueva de BACKEND (HLS).

Fuente única de verdad del formato de las correcciones v2 de backend. El skill
`sca-corrector-v2/SKILL.md` y (a futuro) la Routine importan desde acá — si
cambia el checklist o el formato de los mensajes, este es el único archivo a
tocar.

⚠️ Este módulo es INDEPENDIENTE de v1 (`sca/reporter/templates.py`). No
importa nada de v1 a propósito: cuando la prueba vieja se elimine, se borra
`sca/reporter/` completo sin tocar este paquete.

La prueba nueva (ver `new-technical-test/Backend/Prueba tecnica.pdf`):
- Parte 1: evolucionar un servicio FastAPI provisto (filtro por resolución)
  agregando filtro por rango de bitrate, con diseño extensible (vienen 3
  criterios más). Se entrega el `.git` local actualizado.
- Parte 2: módulo de set cover — subconjunto mínimo de chunklists que cubre
  todos los IDs de segmentos. Salida JSON. Cualquier lenguaje.

Uso típico (con $SCA_ROOT seteado):

    import os, sys
    sys.path.insert(0, os.environ['SCA_ROOT'])
    from sca.v2.reporter.templates import (
        build_scores_payload, build_asana_text, build_asana_title, build_slack_text,
    )
"""

from typing import Any, Dict, List, Optional


# Nivel → etiqueta usada tanto en Asana como en Slack.
# (Duplicado deliberado de v1: v2 no importa de v1 para poder borrarla.)
NIVEL_LABEL: Dict[int, str] = {
    0: '🔴 No suficiente',
    1: '🟡 Trainee',
    2: '🟢 Junior',
    3: '⭐ Semi Senior',
}


# Los 26 criterios scoreables de backend v2 (0/1 cada uno).
# Numeración F201.. para no colisionar con v1 (F3..F31) ni frontend v2 (F301..).
CRITERIOS_BACKEND_V2: List[int] = [
    # Documentación
    201, 202, 203,
    # Git y entrega
    204, 205, 206,
    # API y funcionalidad (Parte 1)
    207, 208, 209, 210, 211,
    # Diseño extensible (Parte 1, req. 2)
    212, 213, 214,
    # Calidad del código
    215, 216, 217, 218, 219, 220, 221,
    # Parte 2 — Reconstrucción de playlist
    222, 223, 224, 225, 226,
]


# Criterios críticos: si alguno es 0, el nivel debe ser `no_suficiente` (0).
# Mapeo desde v1: F28 (Parte A incorrecta) → F207, F12 (hardcodea providers,
# espíritu = no generaliza) → F212, F29 (Parte B no cubre módulos) → F222.
CRITERIOS_CRITICOS_V2: Dict[int, str] = {
    207: 'F207 el filtro por bitrate no funciona',
    212: 'F212 el diseño no permite agregar criterios de filtrado nuevos',
    222: 'F222 la Parte 2 no cubre la totalidad de los segmentos',
}


# Estructura del texto de Asana: secciones con su emoji y los (row, descripción)
# que las componen. El orden define el orden en el mensaje renderizado.
SECCIONES_V2: List[Any] = [
    ('📚 Documentación', [
        (201, 'Explica cómo correr el código (ambas partes)'),
        (202, 'Documenta versiones y dependencias (actualiza README/requirements si agrega)'),
        (203, 'Explica decisiones de diseño (en especial el filtrado extensible)'),
    ]),
    ('🌱 Git y entrega', [
        (204, 'Incluye el .git local actualizado en el entregable'),
        (205, 'Commits incrementales (no un único commit gigante sobre el inicial)'),
        (206, 'Mensajes de commit descriptivos'),
    ]),
    ('👨‍💻 API y funcionalidad (Parte 1)', [
        (207, 'El filtro por rango de bitrate (min/max) funciona'),
        (208, 'El filtro por resolución existente sigue funcionando'),
        (209, 'Los filtros son combinables en una misma request'),
        (210, 'Valida parámetros y devuelve errores HTTP coherentes (400/404/422)'),
        (211, 'Actualiza la documentación de la API (Swagger/README) con lo nuevo'),
    ]),
    ('🏗 Diseño extensible', [
        (212, 'Se pueden agregar criterios de filtrado sin modificar la lógica existente'),
        (213, 'Mantiene la separación de capas (rutas en app.py, lógica en el service)'),
        (214, 'No introduce código duplicado al agregar el filtro nuevo'),
    ]),
    ('🍝 Calidad del código', [
        (215, 'Nomenclatura consistente'),
        (216, 'Comentarios adecuados (ni ausentes ni excesivos)'),
        (217, 'Sigue las convenciones del código base (async, typing, pydantic)'),
        (218, 'Divide en funciones/módulos con responsabilidades claras'),
        (219, 'Formato e indentación consistentes'),
        (220, 'Tiene error handling (bonus)'),
        (221, 'Agrega tests automatizados (bonus)'),
    ]),
    ('🧩 Parte 2 — Reconstrucción de playlist', [
        (222, 'Cubre la totalidad de los IDs de segmentos'),
        (223, 'Encuentra el subconjunto mínimo (óptimo, no solo válido)'),
        (224, 'Salida JSON en el formato que pide la letra'),
        (225, 'Parsea los .m3u8 reales (no hardcodea IDs ni cantidad de archivos)'),
        (226, 'Maneja casos borde (IDs incubribles, archivos malformados, carpeta vacía)'),
    ]),
]

TOTAL_CRITERIOS = len(CRITERIOS_BACKEND_V2)


def _normalize_scores(scores: Dict[Any, int]) -> Dict[int, int]:
    """scores.json deserializa keys como strings; esta función las vuelve int."""
    return {int(k): v for k, v in scores.items()}


def build_scores_payload(
    scores: Dict[int, int],
    *,
    nivel: int,
    apellido: str,
    nombre: str,
    aspectos: Optional[List[str]] = None,
    otras_notas: str = '',
    feedback: str = '',
    nivel_justif: str = '',
) -> Dict[str, Any]:
    """
    Arma el payload que se persiste en `$SCA_WORK/scores.json` (backend v2).

    `scores` debe tener las 26 filas de `CRITERIOS_BACKEND_V2` con 0/1.
    `nivel` es explícito (0-3) — a diferencia de v1, no viaja como una fila
    mágica dentro de `scores`.

    Calcula `puntaje` (X/26) y agrega `resumen` con la etiqueta del nivel para
    que los pasos de Asana y Slack no tengan que recalcularlo.

    Los campos `aspectos`, `otras_notas`, `feedback` y `nivel_justif` son
    OBLIGATORIOS y deben tener contenido sustantivo (no string vacío, no `—`,
    no lista vacía) — misma regla dura que en v1: las secciones del texto de
    Asana NUNCA pueden ir vacías. Si alguno falta, lanza `ValueError`.
    """
    _missing: List[str] = []
    if not aspectos or not any(a and a.strip() and a.strip() != '—' for a in aspectos):
        _missing.append('aspectos (lista de al menos 1 ítem con contenido)')
    if not otras_notas or not otras_notas.strip() or otras_notas.strip() == '—':
        _missing.append('otras_notas')
    if not feedback or not feedback.strip() or feedback.strip() == '—':
        _missing.append('feedback')
    if not nivel_justif or not nivel_justif.strip() or nivel_justif.strip() == '—':
        _missing.append('nivel_justif')
    if _missing:
        raise ValueError(
            'build_scores_payload (backend v2): faltan campos obligatorios: '
            + ', '.join(_missing)
            + '. Las secciones del texto de Asana NUNCA pueden ir vacías.'
        )

    if nivel not in NIVEL_LABEL:
        raise ValueError(f'build_scores_payload (backend v2): nivel inválido: {nivel!r}')

    # Regla dura de críticos: si falla alguno, el nivel solo puede ser 0.
    norm = _normalize_scores(scores)
    fallas = [desc for f, desc in CRITERIOS_CRITICOS_V2.items() if norm.get(f) == 0]
    if fallas and nivel != 0:
        raise ValueError(
            'build_scores_payload (backend v2): hay criterios críticos en 0 '
            f'({"; ".join(fallas)}) — el nivel debe ser 0 (no_suficiente), no {nivel}.'
        )

    puntaje = sum(1 for f in CRITERIOS_BACKEND_V2 if norm.get(f) == 1)

    return {
        'version':     'v2',
        'kind':        'backend',
        'scores':      scores,
        'aspectos':    aspectos,
        'otras_notas': otras_notas,
        'feedback':    feedback,
        'candidato':   {'apellido': apellido, 'nombre': nombre},
        'resumen':     {
            'nivel_val':     nivel,
            'nivel':         NIVEL_LABEL[nivel],
            'puntaje':       f'{puntaje}/{TOTAL_CRITERIOS}',
            'justificacion': nivel_justif,
        },
    }


def build_asana_title(payload: Dict[str, Any]) -> str:
    """Título de la task de Asana. Convención: `SCA v2 — <Apellido>, <Nombre>`.

    El prefijo `SCA v2` distingue las correcciones de la prueba nueva de las
    de la vieja (`SCA — ...`) mientras conviven.
    """
    cand = payload['candidato']
    return f'SCA v2 — {cand["apellido"]}, {cand["nombre"]}'


def build_asana_text(payload: Dict[str, Any]) -> str:
    """
    Construye el `notes` de la task de Asana desde el payload de scores.json.

    Formato: nivel + justificación + 6 secciones con ✅/❌ + aspectos +
    otras notas + feedback. Texto plano con emojis y saltos de línea.
    """
    scores      = _normalize_scores(payload['scores'])
    aspectos    = payload.get('aspectos') or ['—']
    otras_notas = payload.get('otras_notas') or '—'
    feedback    = payload.get('feedback') or '—'
    resumen     = payload['resumen']

    def icon(f: int) -> str:
        return '✅' if scores.get(f) == 1 else '❌'

    lines: List[str] = [
        f"Nivel: {resumen['nivel']}",
        f"Puntaje: {resumen['puntaje']}",
        f"Por qué este nivel: {resumen.get('justificacion', '—')}",
        '',
    ]
    for titulo, items in SECCIONES_V2:
        lines.append(titulo)
        for f, desc in items:
            lines.append(f'{icon(f)} {desc}')
        lines.append('')

    lines.append('⭐ Aspectos que destacan:')
    for a in aspectos:
        lines.append(a)
    lines.append('')

    lines.append('📝 Otras notas:')
    lines.append(otras_notas)
    lines.append('')

    lines.append('🎁 Feedback:')
    lines.append(feedback)

    return '\n'.join(lines)


def build_slack_text(
    payload: Dict[str, Any],
    *,
    source_url: str,
    asana_url: str,
    email: Optional[str] = None,
) -> str:
    """
    Mensaje de éxito para postear en Slack al final de la corrección.

    Corrige el pendiente de v1: label neutro `Fuente` (en el flow cron es el
    permalink de la task de Asana, no un repo) y `email` opcional.
    """
    cand = payload['candidato']
    r    = payload['resumen']

    candidato = f"{cand['apellido']}, {cand['nombre']}"
    if email:
        candidato += f' ({email})'

    lines = [
        '*SCA v2 — Corrección Backend completada* ✅',
        f'*Candidato:* {candidato}',
        f'*Fuente:* {source_url}',
        f"*Nivel:* {r['nivel']}",
        f"*Puntaje:* {r['puntaje']}",
        f'*Asana:* {asana_url}',
    ]
    return '\n'.join(lines)


def critical_failures(payload: Dict[str, Any]) -> List[str]:
    """
    Devuelve las descripciones de los criterios críticos (F207/F212/F222) que
    fallaron (= 0). Usado por el reporte final del skill o la Routine.
    """
    scores = _normalize_scores(payload['scores'])
    return [desc for f, desc in CRITERIOS_CRITICOS_V2.items() if scores.get(f) == 0]
