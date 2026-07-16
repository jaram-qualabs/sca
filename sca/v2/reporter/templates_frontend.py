"""
Templates de reporting del SCA **v2** — prueba técnica nueva de FRONTEND (HLS).

Equivalente a `sca/v2/reporter/templates.py` (backend v2) pero adaptado a la
prueba nueva de frontend. Mantiene la misma forma — `build_scores_payload`,
`build_asana_title`, `build_asana_text`, `build_slack_text`,
`critical_failures` — para que el skill de frontend v2 y la Routine invoquen
la API igual que en backend v2.

⚠️ Independiente de v1: no importa nada de `sca/reporter/`. Sí comparte
`NIVEL_LABEL` con backend v2 (compartir dentro de v2 está bien; el límite
que no se cruza es v2 → v1).

La prueba nueva (ver `new-technical-test/Frontend/Prueba Tecnica.pdf`):
- Req 1: SPA con dashboard de validación y análisis de manifests HLS
  (URL → validación en tiempo real + gráficos de resolución/bandwidth/
  codecs/duración).
- Req 2: filtro dinámico de resoluciones con sliders → obtiene el manifest
  filtrado (vía el backend FastAPI provisto).
- Req 3: player HLS integrado con cambio dinámico de resolución y pista de
  audio.
- Figma de referencia; framework libre pero el cliente prefiere React.
  Se entrega el `.git` local actualizado.

Uso típico (con $SCA_ROOT seteado):

    import os, sys
    sys.path.insert(0, os.environ['SCA_ROOT'])
    from sca.v2.reporter.templates_frontend import (
        build_scores_payload, build_asana_text, build_asana_title, build_slack_text,
    )
"""

from typing import Any, Dict, List, Optional

# Compartido DENTRO de v2 (nunca desde v1).
from sca.v2.reporter.templates import NIVEL_LABEL


# Los 29 criterios scoreables de frontend v2 (0/1 cada uno).
# Numeración F301.. para no colisionar con backend v2 (F201..) ni con v1.
CRITERIOS_FRONTEND_V2: List[int] = [
    # Documentación
    301, 302, 303,
    # Git y entrega
    304, 305, 306,
    # Dashboard de validación y análisis (Req 1)
    307, 308, 309, 310,
    # Filtro dinámico de resoluciones (Req 2)
    311, 312, 313,
    # Player HLS integrado (Req 3)
    314, 315, 316,
    # UI y fidelidad visual
    317, 318, 319,
    # Calidad del código
    320, 321, 322, 323, 324, 325, 326, 327, 328, 329,
]


# Criterios críticos para frontend v2: si alguno es 0, el nivel se fuerza a 0.
# Mapeo desde v1: la funcionalidad core de cada requerimiento reemplaza a
# "Parte A incorrecta" (F135); F325 (código duplicado) se mantiene de F121.
CRITERIOS_CRITICOS_FRONTEND_V2: Dict[int, str] = {
    307: 'F307 la validación del manifest no funciona',
    312: 'F312 el filtro no obtiene el manifest filtrado',
    314: 'F314 el player no reproduce',
    325: 'F325 hay código duplicado',
}


# Estructura del texto de Asana para frontend v2: 7 secciones con su emoji y
# los (row, descripción) que las componen.
SECCIONES_FRONTEND_V2: List[Any] = [
    ('📚 Documentación', [
        (301, 'Explica cómo correr la app (y el backend provisto si hace falta)'),
        (302, 'Documenta versiones y dependencias'),
        (303, 'Explica decisiones de diseño (librerías de gráficos/player, estructura)'),
    ]),
    ('🌱 Git y entrega', [
        (304, 'Incluye el .git local actualizado en el entregable'),
        (305, 'Commits incrementales (no un único commit gigante sobre el inicial)'),
        (306, 'Mensajes de commit descriptivos'),
    ]),
    ('📊 Dashboard de validación y análisis (Req 1)', [
        (307, 'Ingresa una URL y valida el manifest mostrando el resultado en tiempo real'),
        (308, 'Muestra errores de manifests inválidos de forma clara'),
        (309, 'Desglose visual con gráficos: resolución, bandwidth, codecs, duración total'),
        (310, 'Los tipos de gráfico elegidos son acordes y legibles'),
    ]),
    ('🎚 Filtro dinámico de resoluciones (Req 2)', [
        (311, 'Sliders para seleccionar el rango de resolución'),
        (312, 'Obtiene el manifest filtrado a partir del filtro aplicado'),
        (313, 'Feedback al usuario (loading, errores, rango sin resultados)'),
    ]),
    ('🎬 Player HLS integrado (Req 3)', [
        (314, 'Reproduce una variante obtenida del parse_manifest'),
        (315, 'Cambia dinámicamente entre resoluciones según selección del usuario'),
        (316, 'Cambia entre pistas de audio según selección del usuario'),
    ]),
    ('🎨 UI y fidelidad visual', [
        (317, 'Similitud visual con el Figma de referencia'),
        (318, 'Responsive'),
        (319, 'Consistencia visual entre vistas (layout, estados, tipografía)'),
    ]),
    ('🍝 Calidad del código', [
        (320, 'Componentes chicos y reutilizables'),
        (321, 'Separa lógica de presentación (hooks/servicios para las llamadas a la API)'),
        (322, 'Manejo de estado adecuado (sin prop drilling excesivo ni estado global innecesario)'),
        (323, 'Nomenclatura y convenciones consistentes'),
        (324, 'Solo componentes funcionales con hooks (no mezcla estilos)'),
        (325, 'Sin código duplicado'),
        (326, 'Estilos organizados y desacoplados (CSS junto a su componente)'),
        (327, 'Error handling en la integración con el backend'),
        (328, 'Comentarios adecuados (ni ausentes ni excesivos)'),
        (329, 'Agrega tests automatizados (bonus)'),
    ]),
]

TOTAL_CRITERIOS = len(CRITERIOS_FRONTEND_V2)


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
    Arma el payload que se persiste en `$SCA_WORK/scores.json` (frontend v2).

    `scores` debe tener las 29 filas de `CRITERIOS_FRONTEND_V2` con 0/1.
    `nivel` es explícito (0-3), igual que en backend v2.

    Misma validación dura que backend v2: campos narrativos obligatorios y
    nivel forzado a 0 si falla algún crítico.
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
            'build_scores_payload (frontend v2): faltan campos obligatorios: '
            + ', '.join(_missing)
            + '. Las secciones del texto de Asana NUNCA pueden ir vacías.'
        )

    if nivel not in NIVEL_LABEL:
        raise ValueError(f'build_scores_payload (frontend v2): nivel inválido: {nivel!r}')

    norm = _normalize_scores(scores)
    fallas = [desc for f, desc in CRITERIOS_CRITICOS_FRONTEND_V2.items() if norm.get(f) == 0]
    if fallas and nivel != 0:
        raise ValueError(
            'build_scores_payload (frontend v2): hay criterios críticos en 0 '
            f'({"; ".join(fallas)}) — el nivel debe ser 0 (no_suficiente), no {nivel}.'
        )

    puntaje = sum(1 for f in CRITERIOS_FRONTEND_V2 if norm.get(f) == 1)

    return {
        'version':     'v2',
        'kind':        'frontend',
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
    """Título de la task de Asana: `SCA v2 — <Apellido>, <Nombre> (Frontend)`."""
    cand = payload['candidato']
    return f'SCA v2 — {cand["apellido"]}, {cand["nombre"]} (Frontend)'


def build_asana_text(payload: Dict[str, Any]) -> str:
    """
    Construye el `notes` de la task de Asana desde el payload de scores.json
    para frontend v2. Formato: nivel + justificación + 7 secciones con ✅/❌ +
    aspectos + otras notas + feedback.
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
    for titulo, items in SECCIONES_FRONTEND_V2:
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
    Mensaje de éxito para postear en Slack al final de la corrección de
    frontend v2. El header dice "Frontend" para distinguir de un vistazo.
    """
    cand = payload['candidato']
    r    = payload['resumen']

    candidato = f"{cand['apellido']}, {cand['nombre']}"
    if email:
        candidato += f' ({email})'

    lines = [
        '*SCA v2 — Corrección Frontend completada* ✅',
        f'*Candidato:* {candidato}',
        f'*Fuente:* {source_url}',
        f"*Nivel:* {r['nivel']}",
        f"*Puntaje:* {r['puntaje']}",
        f'*Asana:* {asana_url}',
    ]
    return '\n'.join(lines)


def critical_failures(payload: Dict[str, Any]) -> List[str]:
    """
    Devuelve las descripciones de los criterios críticos (F307/F312/F314/F325)
    que fallaron (= 0).
    """
    scores = _normalize_scores(payload['scores'])
    return [desc for f, desc in CRITERIOS_CRITICOS_FRONTEND_V2.items() if scores.get(f) == 0]
