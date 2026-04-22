"""
Templates de reporting del SCA: esquema de `scores.json`, texto de Asana y
mensaje de Slack.

Fuente única de verdad del formato de las correcciones. La Routine en
`routine/PROMPT.md` y el skill en `sca-corrector/SKILL.md` importan desde
acá — si cambia el checklist o el formato de los mensajes, este es el único
archivo a tocar.

Uso típico (desde la Routine o el skill, con $SCA_ROOT seteado):

    import os, sys
    sys.path.insert(0, os.environ['SCA_ROOT'])
    from sca.reporter.templates import (
        build_scores_payload, build_asana_text, build_asana_title, build_slack_text,
    )
"""

from typing import Any, Dict, List, Optional


# Nivel → etiqueta usada tanto en Asana como en Slack.
NIVEL_LABEL: Dict[int, str] = {
    0: '🔴 No suficiente',
    1: '🟡 Trainee',
    2: '🟢 Junior',
    3: '⭐ Semi Senior',
}


# Filas del checklist que representan los 23 criterios scoreables.
# El puntaje X/23 se calcula contando cuántos de estos valen 1.
CRITERIOS_23: List[int] = [
    3, 4, 5,
    8, 9, 10, 11, 12, 13,
    16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
    28, 29, 30, 31,
]


# Criterios críticos: si alguno es 0, el nivel debe ser `no_suficiente` (0).
# Se usan tanto en scoring como en el reporte final para destacar fallas.
CRITERIOS_CRITICOS: Dict[int, str] = {
    12: 'F12 hardcodea providers',
    28: 'F28 Parte A incorrecta',
    29: 'F29 Parte B no cubre módulos',
}


# Estructura del texto de Asana: secciones con su emoji y los (row, descripción)
# que las componen. El orden define el orden en el mensaje renderizado.
SECCIONES: List[Any] = [
    ('📚 Documentación', [
        (3,  'Explica cómo correr el código'),
        (4,  'Documenta la versión de la tecnología'),
        (5,  'Explica elecciones o decisiones de diseño'),
    ]),
    ('👨\u200d💻 Usabilidad', [
        (8,  'El output es consistente entre Parte A y Parte B'),
        (9,  'Parametriza la carpeta de archivos de entrada'),
        (10, 'No hardcodea nombres de archivos'),
        (11, 'No hardcodea la cantidad de archivos'),
        (12, 'No hardcodea providers'),
        (13, 'Imprime la salida como pide la letra'),
    ]),
    ('🍝 Calidad del código', [
        (16, 'Nomenclatura consistente'),
        (17, 'Comentarios adecuados'),
        (18, 'Sin comentarios excesivos'),
        (19, 'Sigue convenciones de la tecnología'),
        (20, 'Divide en funciones'),
        (21, 'No repite código de Parte A en Parte B'),
        (22, 'Sin código duplicado interno'),
        (23, 'Sin código mal indentado'),
        (24, 'Sin formato irregular'),
        (25, 'Tiene error handling (bonus)'),
    ]),
    ('🛠 Eficacia y Eficiencia', [
        (28, 'Parte A correcta'),
        (29, 'Parte B cubre los 8 módulos'),
        (30, 'Busca un set reducido de usuarios'),
        (31, 'Asegura el set mínimo (bonus)'),
    ]),
]


def _normalize_scores(scores: Dict[Any, int]) -> Dict[int, int]:
    """scores.json deserializa keys como strings; esta función las vuelve int."""
    return {int(k): v for k, v in scores.items()}


def build_scores_payload(
    scores: Dict[int, int],
    *,
    apellido: str,
    nombre: str,
    aspectos: Optional[List[str]] = None,
    otras_notas: str = '',
    feedback: str = '',
    nivel_justif: str = '',
) -> Dict[str, Any]:
    """
    Arma el payload que se persiste en `$SCA_WORK/scores.json`.

    Calcula `puntaje` (X/23) y agrega `resumen` con la etiqueta del nivel para
    que los pasos de Asana y Slack no tengan que recalcularlo.

    `scores` debe tener las 23 filas de `CRITERIOS_23` más la fila 34 (nivel).
    """
    nivel_val = scores[34]
    puntaje = sum(1 for f in CRITERIOS_23 if scores.get(f) == 1)

    return {
        'scores':      scores,
        'aspectos':    aspectos or [],
        'otras_notas': otras_notas,
        'feedback':    feedback,
        'candidato':   {'apellido': apellido, 'nombre': nombre},
        'resumen':     {
            'nivel_val':     nivel_val,
            'nivel':         NIVEL_LABEL[nivel_val],
            'puntaje':       f'{puntaje}/23',
            'justificacion': nivel_justif,
        },
    }


def build_asana_title(payload: Dict[str, Any]) -> str:
    """Título de la task de Asana. Convención: `SCA — <Apellido>, <Nombre>`."""
    cand = payload['candidato']
    return f'SCA — {cand["apellido"]}, {cand["nombre"]}'


def build_asana_text(payload: Dict[str, Any]) -> str:
    """
    Construye el `notes` de la task de Asana desde el payload de scores.json.

    Formato: nivel + justificación + 4 secciones con ✅/❌ + aspectos +
    otras notas + feedback. Texto plano con emojis y saltos de línea —
    Asana lo renderiza OK.
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
    for titulo, items in SECCIONES:
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
    repo_url: str,
    email: str,
    asana_url: str,
) -> str:
    """
    Mensaje de éxito para postear en Slack al final de la Routine.

    Usa markdown de Slack (`*bold*`). No incluye link al Excel porque el paso
    de generar Excel fue removido — el registro autoritativo vive en Asana.
    """
    cand = payload['candidato']
    r    = payload['resumen']

    lines = [
        '*SCA — Corrección completada* ✅',
        f"*Candidato:* {cand['apellido']}, {cand['nombre']} ({email})",
        f"*Repo:* {repo_url}",
        f"*Nivel:* {r['nivel']}",
        f"*Puntaje:* {r['puntaje']}",
        f"*Asana:* {asana_url}",
    ]
    return '\n'.join(lines)


def critical_failures(payload: Dict[str, Any]) -> List[str]:
    """
    Devuelve las descripciones de los criterios críticos (F12/F28/F29) que
    fallaron (= 0). Usado por el reporte final de la Routine.
    """
    scores = _normalize_scores(payload['scores'])
    return [desc for f, desc in CRITERIOS_CRITICOS.items() if scores.get(f) == 0]
