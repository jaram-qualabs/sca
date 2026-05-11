"""
Templates de reporting del SCA para pruebas de **frontend**.

Equivalente a `sca/reporter/templates.py` (backend) pero adaptado al checklist
oficial de frontend (`Requerimientos/Template Frontend.xlsx`). Mantiene la
misma forma — `build_scores_payload`, `build_asana_title`, `build_asana_text`,
`build_slack_text`, `critical_failures` — para que el skill de frontend y la
Routine puedan invocar la API igual que en backend.

Diferencias con backend:
- 35 criterios scoreables (vs 23 en backend)
- 6 secciones (vs 4 en backend): se agregan "Usabilidad Front" y "Calidad del
  código Front" con criterios específicos de React/UI
- 4 criterios críticos (F108, F121, F132, F135) — si alguno es 0, el nivel es
  automáticamente `no_suficiente`
- Numeración separada (F101..F135) para evitar colisiones con backend (F3..F31)

Comparte con backend:
- `NIVEL_LABEL` (los 4 niveles son los mismos)
- Validación dura: las cuatro secciones narrativas (`aspectos`, `otras_notas`,
  `feedback`, `nivel_justif`) son obligatorias

Uso típico (desde el skill o la Routine, con $SCA_ROOT seteado):

    import os, sys
    sys.path.insert(0, os.environ['SCA_ROOT'])
    from sca.reporter.templates_frontend import (
        build_scores_payload, build_asana_text, build_asana_title, build_slack_text,
    )
"""

from typing import Any, Dict, List, Optional

# Reusamos los labels de nivel del módulo backend (single source of truth).
from sca.reporter.templates import NIVEL_LABEL


# Filas del checklist que representan los 35 criterios scoreables de frontend.
# El puntaje X/35 se calcula contando cuántos de estos valen 1.
CRITERIOS_FRONTEND: List[int] = [
    # Documentación
    101, 102, 103,
    # Usabilidad
    104, 105, 106, 107, 108,
    # Usabilidad Front
    109, 110, 111, 112, 113, 114, 115,
    # Calidad del código
    116, 117, 118, 119, 120, 121, 122, 123, 124,
    # Calidad del código Front
    125, 126, 127, 128, 129, 130, 131, 132, 133, 134,
    # Eficacia y eficiencia
    135,
]


# Criterios críticos para frontend: si alguno es 0, el nivel se fuerza a 0
# (no_suficiente). Vienen marcados con ❗ en el template oficial.
CRITERIOS_CRITICOS_FRONTEND: Dict[int, str] = {
    108: 'F108 hardcodea providers',
    121: 'F121 hay código duplicado',
    132: 'F132 mezcla componentes funcionales y no funcionales',
    135: 'F135 Parte A incorrecta',
}


# Estructura del texto de Asana para frontend: 6 secciones con su emoji y los
# (row, descripción) que las componen. El orden define el orden en el mensaje
# renderizado y refleja el orden visual del template oficial.
SECCIONES_FRONTEND: List[Any] = [
    ('📚 Documentación', [
        (101, 'Explica cómo correr el código'),
        (102, 'Documenta la versión de la tecnología'),
        (103, 'Explica cómo funciona el código o decisiones de diseño'),
    ]),
    ('👨‍💻 Usabilidad', [
        (104, 'Output consistente (todo por consola o todo por archivos)'),
        (105, 'Parametriza los archivos en la ejecución'),
        (106, 'No hardcodea nombres de archivos'),
        (107, 'No hardcodea la cantidad de archivos'),
        (108, 'No hardcodea providers'),
    ]),
    ('👨‍💻 Usabilidad Front', [
        (109, 'Queda seleccionado el botón del módulo o submódulo'),
        (110, 'Los headers dicen lo que pide la letra'),
        (111, 'Los botones dicen lo que pide la letra'),
        (112, 'Usa el ruteo de React'),
        (113, 'Similitud visual del módulo a la letra'),
        (114, 'Similitud visual de los botones a la letra'),
        (115, 'Responsive'),
    ]),
    ('🍝 Calidad del código', [
        (116, 'Nomenclatura consistente'),
        (117, 'Comentarios adecuados'),
        (118, 'Sin comentarios excesivos'),
        (119, 'Sigue convenciones de la tecnología'),
        (120, 'Divide en funciones'),
        (121, 'Sin código duplicado'),
        (122, 'Sin código mal indentado'),
        (123, 'Sin formato irregular'),
        (124, 'Tiene error handling (bonus)'),
    ]),
    ('🍝 Calidad del código Front', [
        (125, 'Componentes genéricos para el botón'),
        (126, 'Componentes genéricos para el Contenedor (header + content)'),
        (127, 'Usa destructuring de props'),
        (128, 'Utiliza el redux store'),
        (129, 'Carpeta separada para componentes genéricos'),
        (130, 'CSS desacoplado'),
        (131, 'Usa SCSS'),
        (132, 'Componentes funcionales o no funcionales (no los mezcla)'),
        (133, 'Constantes en archivos separados'),
        (134, 'Arquitectura clara (CSS junto al componente)'),
    ]),
    ('🛠 Eficacia y Eficiencia', [
        (135, 'Parte A correcta'),
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
    Arma el payload que se persiste en `$SCA_WORK/scores.json` para frontend.

    Calcula `puntaje` (X/35) y agrega `resumen` con la etiqueta del nivel para
    que los pasos de Asana y Slack no tengan que recalcularlo.

    `scores` debe tener las 35 filas de `CRITERIOS_FRONTEND` más la fila 140
    (nivel, 0-3).

    Los campos `aspectos`, `otras_notas`, `feedback` y `nivel_justif` son
    OBLIGATORIOS y deben tener contenido sustantivo (no string vacío, no `—`,
    no lista vacía). Si alguno falta, esta función lanza `ValueError` para
    forzar al caller a llenarlos antes de generar el texto.
    """
    # Validación dura: las cuatro secciones narrativas son obligatorias.
    # Misma regla que en backend: las secciones del texto de Asana NUNCA
    # pueden ir vacías o solo con un guión.
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
            'build_scores_payload (frontend): faltan campos obligatorios: '
            + ', '.join(_missing)
            + '. Las secciones del texto de Asana NUNCA pueden ir vacías.'
        )

    nivel_val = scores[140]
    puntaje = sum(1 for f in CRITERIOS_FRONTEND if scores.get(f) == 1)

    return {
        'kind':        'frontend',
        'scores':      scores,
        'aspectos':    aspectos,
        'otras_notas': otras_notas,
        'feedback':    feedback,
        'candidato':   {'apellido': apellido, 'nombre': nombre},
        'resumen':     {
            'nivel_val':     nivel_val,
            'nivel':         NIVEL_LABEL[nivel_val],
            'puntaje':       f'{puntaje}/35',
            'justificacion': nivel_justif,
        },
    }


def build_asana_title(payload: Dict[str, Any]) -> str:
    """Título de la task de Asana. Convención: `SCA — <Apellido>, <Nombre> (Frontend)`.

    El sufijo `(Frontend)` distingue las correcciones de frontend de las de
    backend, que usan el formato `SCA — <Apellido>, <Nombre>` sin sufijo.
    """
    cand = payload['candidato']
    return f'SCA — {cand["apellido"]}, {cand["nombre"]} (Frontend)'


def build_asana_text(payload: Dict[str, Any]) -> str:
    """
    Construye el `notes` de la task de Asana desde el payload de scores.json
    para frontend.

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
    for titulo, items in SECCIONES_FRONTEND:
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
    Mensaje de éxito para postear en Slack al final de la corrección de frontend.

    Diferencia visual con backend: el header dice "Frontend" para que el canal
    distinga de un vistazo de qué tipo de corrección se trata.
    """
    cand = payload['candidato']
    r    = payload['resumen']

    lines = [
        '*SCA — Corrección Frontend completada* ✅',
        f"*Candidato:* {cand['apellido']}, {cand['nombre']} ({email})",
        f"*Repo:* {repo_url}",
        f"*Nivel:* {r['nivel']}",
        f"*Puntaje:* {r['puntaje']}",
        f"*Asana:* {asana_url}",
    ]
    return '\n'.join(lines)


def critical_failures(payload: Dict[str, Any]) -> List[str]:
    """
    Devuelve las descripciones de los criterios críticos (F108/F121/F132/F135)
    que fallaron (= 0). Usado por el reporte final del skill o la Routine.
    """
    scores = _normalize_scores(payload['scores'])
    return [desc for f, desc in CRITERIOS_CRITICOS_FRONTEND.items() if scores.get(f) == 0]
