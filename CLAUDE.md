# SCA — Contexto para Claude

Este archivo lo lee Claude al arrancar una sesión en este repo. Si estás humano
leyendo, también te sirve como intro de 5 minutos.

## Qué es

**SCA = Sistema de Corrección Automatizada**. Es el corrector automático de
pruebas técnicas de backend de Qualabs. Dado un repo con la solución de un
candidato (Parte A + Parte B), produce:

- Un scoring de 23 criterios (0/1 cada uno)
- Un nivel sugerido: `no_suficiente` / `trainee` / `junior` / `semi_senior`
- Una justificación breve del nivel (para que un humano la valide)
- Una task en Asana con el feedback formateado
- Un mensaje en Slack avisando de la corrección

Se usa en dos modos:

- **Manual** (Cowork / Claude Code local): alguien le pide a Claude "corregí
  esta prueba" y Claude dispara el skill `sca-corrector`.
- **Desatendido** (Routine con cron diario): una Routine en
  `claude.ai/code/routines` corre todos los días a las 9am ART ejecutando
  `routine/PROMPT.md`. La Routine poleá Asana buscando tasks en la section
  "Para corregir" con un `.zip` adjunto, las corrige en batch y crea en
  cada una una subtask `"Comentarios y corrección SCA"` con el feedback.
  La presencia de esa subtask marca la task como ya corregida (idempotencia).

> **Flow viejo (legacy).** Antes la Routine se disparaba por un Google Form
> que llamaba al API de claude.ai vía Apps Script. Ese flow sigue
> documentado en `routine/PROMPT-form.md.legacy` + `apps-script/` por si hay
> que volver, pero **no está activo** — lo reemplazó el cron+Asana.

## SCA v2 (prueba técnica nueva — HLS) 🚧

Existe una **segunda generación de la prueba técnica** (manipulación de
manifests HLS, ver `new-technical-test/`) con su propio corrector **v2 en
beta**, que convive con v1 hasta que la prueba vieja se elimine. Todo v2 vive
en `sca/v2/` (templates backend y frontend), `sca-corrector-v2/`,
`sca-corrector-frontend-v2/` y `new-technical-test/`. **v2 no importa nada de
v1** — el plan de convivencia, el mapeo de criterios viejos→nuevos y el
checklist para eliminar v1 están en `sca/v2/PLAN.md`. La Routine rutea
v1/v2 en el Paso 5.0 de `routine/PROMPT.md` (tag de Asana `sca-v2` +
sniff del zip como fallback) y el sub-flujo v2 vive autocontenido en
`routine/v2/CORRECCION.md`, que se lee solo si el batch tiene tasks v2. Si vas a tocar scoring
o formato de v2, leé primero `sca/v2/reporter/templates.py` (BE) o
`templates_frontend.py` (FE). El resto de este archivo describe v1.

## Layout del repo

```
sca/                         Paquete Python — lógica del corrector sin UI
  validators/                Valida el output de Parte A y Parte B
    part_a.py                Valida output de Parte A contra `datos prueba tecnica/`
    part_b.py                Valida que Parte B cubra los 8 módulos
  reporter/
    templates.py             ⭐ FUENTE ÚNICA DE VERDAD para BACKEND (23 criterios)
    templates_frontend.py    ⭐ FUENTE ÚNICA DE VERDAD para FRONTEND (35 criterios)
  asana/                     Wrappers HTTP directos para operaciones que el MCP de Asana no expone
    attachments.py           Subir archivos a una task vía PAT (POST /api/1.0/attachments)

sca-corrector/               Skill de corrección manual de BACKEND
  SKILL.md                   ⭐ Skill que Claude activa con "corregí esta prueba"
  references/                Material que Claude lee durante la corrección
    manual.md                Criterios detallados fila por fila (F3..F31)
    expected_output.md       Outputs esperados de Parte A y Parte B
    backend/                 Repos de candidatos de ejemplo (gitignored)
    frontend/                Muestras de correcciones humanas + zips de candidatos FE
  candidato/                 Espacio scratch para correcciones locales (opcional)

sca-corrector-frontend/      Skill de corrección manual de FRONTEND (React)
  SKILL.md                   ⭐ Skill que Claude activa cuando detecta React
  references/
    manual.md                Criterios detallados fila por fila (F101..F135)
    expected_part_a.md       Cómo validar Parte A (script o in-browser)
    # mock visual: leer Prueba tecnica/Prueba técnica - Frontend.pdf

routine/                     Modo desatendido (Claude Routine con cron)
  PROMPT.md                  ⭐ El prompt ACTIVO (cron diario + Asana-triggered)
  PROMPT-form.md.legacy      El prompt viejo (disparado por Google Form) — no activo
  SETUP.md                   Cómo crear/configurar la Routine paso a paso

apps-script/                 [LEGACY] Trigger del Google Form del flow viejo
  trigger.gs                 `onFormSubmit` → POST /v1/routines/<id>/fire
  SETUP.md                   Cómo configurar Form + Apps Script + secrets
  # Inactivo hoy. Reemplazado por el cron+Asana. Se mantiene por si hay
  # que revertir. Si el flow nuevo se estabiliza, se puede borrar.

Prueba tecnica/              Material que se le entrega al candidato
  Prueba técnica - Backend.docx
  Prueba técnica - Frontend.pdf
  datos prueba tecnica/      20 archivos JSON (u0.json..u19.json) — input de la prueba;
                             también usados por `sca/validators/` como ground truth
  datos prueba tecnica.zip   Mismo contenido empaquetado para adjuntar al candidato

Requerimientos/              Specs originales del sistema
  Requerimientos Automatización.pdf   PDF con RF-01..RF-05 del SCA

CLAUDE.md                    Este archivo — contexto para Claude en el root
README.md                    Placeholder mínimo (no es documentación útil todavía)
```

## Fuente única de verdad: dos módulos paralelos

**Backend** (`sca/reporter/templates.py`) y **frontend**
(`sca/reporter/templates_frontend.py`) son los dos archivos cabeza. Si vas a
cambiar el formato de cualquier output (texto de Asana, mensaje de Slack,
schema de scores.json, lista de criterios, emojis, orden de secciones,
etiquetas de nivel): tocá SOLO el archivo correspondiente. El skill y la
Routine importan desde estos.

`templates.py` (backend) exporta:

- `NIVEL_LABEL`, `CRITERIOS_23`, `CRITERIOS_CRITICOS`, `SECCIONES`
- `build_scores_payload(...)`, `build_asana_title(payload)`,
  `build_asana_text(payload)`, `build_slack_text(...)`,
  `critical_failures(payload)` — críticos: F12/F28/F29

`templates_frontend.py` (frontend) exporta lo mismo pero adaptado a las 35
filas del template oficial:

- `CRITERIOS_FRONTEND` (35 ítems), `CRITERIOS_CRITICOS_FRONTEND` (4 críticos:
  F108/F121/F132/F135), `SECCIONES_FRONTEND` (6 secciones)
- Builders idénticos en signature: `build_scores_payload`, `build_asana_title`
  (agrega sufijo "(Frontend)" al título), `build_asana_text`, `build_slack_text`
  (header dice "Frontend"), `critical_failures`
- Reutiliza `NIVEL_LABEL` desde `templates.py` para mantener un único set de
  etiquetas de nivel

Antes existía duplicación entre la Routine y el skill. Ya no — no la
reintroduzcas.

## Convenciones

**Paths vía env vars.** Los snippets de bash y Python usan:

- `SCA_ROOT`: raíz del repo. En la Routine es `/workspace`; en Cowork local es
  `/Users/javieraramberri/Projects/SCA`.
- `SCA_WORK`: scratch dir efímero (`/tmp/sca_work` en la Routine). Ahí viven
  `scores.json`, `texto_asana.txt`, `asana.json`. En el flow cron cada task
  tiene su sub-dir `$SCA_WORK/<task_gid>/` para evitar colisiones.

Para importar el paquete `sca` desde cualquier snippet:

```python
import os, sys
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.reporter.templates import build_asana_text  # o lo que necesites
```

**Criterios críticos.** Si cualquiera de estos es 0, el nivel es automáticamente
`no_suficiente`:

- Backend (`templates.py`): F12 (hardcodea providers), F28 (Parte A incorrecta),
  F29 (Parte B no cubre los 8 módulos).
- Frontend (`templates_frontend.py`): F108 (hardcodea providers), F121 (código
  duplicado), F132 (mezcla componentes funcionales y no funcionales), F135
  (Parte A incorrecta).

**Manejo de errores en la Routine (flow cron).** Dos niveles:

- **Errores globales del batch** (MCP caído, section no existe, env vars
  faltantes): patrón declarativo — alertar a Slack con `❌ *SCA — Fallo global
  en Paso N*` y abortar.
- **Errores por task** (zip corrupto, título sin paréntesis, stack que
  no arranca): **no abortan el batch**. Se logean, se deja un comentario en
  la task problemática (no subtask), y el loop sigue con la próxima.

El Paso 12 del PROMPT (Slack por corrección exitosa) es no-crítico: si falla,
se logea y se declara éxito igual (Asana es el registro autoritativo).

**Idioma.** Contenido user-facing (Asana, Slack, mensajes de error) en
español. Código y docstrings en español también. Commits: lo que quieras.

## Cómo encarar cambios comunes

| Querés cambiar...                                    | Tocá                                                 |
|------------------------------------------------------|------------------------------------------------------|
| Formato del texto de Asana / Slack — backend         | `sca/reporter/templates.py`                          |
| Formato del texto de Asana / Slack — frontend        | `sca/reporter/templates_frontend.py`                 |
| Lista de criterios (agregar/quitar/reordenar) — BE   | `sca/reporter/templates.py` (`CRITERIOS_23`, `SECCIONES`) |
| Lista de criterios — FE                              | `sca/reporter/templates_frontend.py` (`CRITERIOS_FRONTEND`, `SECCIONES_FRONTEND`) |
| Reglas para determinar el nivel — BE                 | `sca-corrector/SKILL.md` Paso 7                      |
| Reglas para determinar el nivel — FE                 | `sca-corrector-frontend/SKILL.md` Paso 7             |
| Señales blandas que pueden bajar el nivel            | `sca-corrector/SKILL.md` Paso 7 (BE) — FE las hereda |
| Guías de scoring por criterio (BE: F4, F20, F25...)  | `sca-corrector/SKILL.md` Paso 5/6                    |
| Guías de scoring por criterio (FE: F102, F112, F128...) | `sca-corrector-frontend/references/manual.md`     |
| Lógica del validator de Parte A o B (BE)             | `sca/validators/part_a.py` o `part_b.py`             |
| Lógica del validator de Parte B (FE, screenshots)    | `sca/validators/part_b_frontend.py`                  |
| Subir screenshots a Asana (via PAT, no MCP)          | `sca/asana/attachments.py`                           |
| Orquestación de la Routine (pasos, orden, env vars)  | `routine/PROMPT.md`                                  |
| Cadencia del cron, network allowlist, env vars prod  | `routine/SETUP.md`                                   |
| Criterios críticos (F12/F28/F29 BE — F108/F121/F132/F135 FE) | `templates.py` o `templates_frontend.py` (`CRITERIOS_CRITICOS*`) |
| Flow viejo (Google Form + Apps Script)               | `apps-script/trigger.gs` + `routine/PROMPT-form.md.legacy` (legacy, inactivo) |

## Testing

No hay test suite formal. Para cambios en `sca/reporter/templates.py`, corré
el smoke test que arma un payload, lo serializa a JSON, lo deserializa, y
verifica que los builders devuelven strings sensatos:

```bash
cd "$SCA_ROOT"
SCA_ROOT="$PWD" python3 -c "
import sys; sys.path.insert(0, '.')
from sca.reporter.templates import build_scores_payload, build_asana_text, build_slack_text
scores = {f: 1 for f in [3,4,5,8,9,10,11,12,13,16,17,18,19,20,21,22,23,24,25,28,29,30,31]}
scores[34] = 2
p = build_scores_payload(scores, apellido='Test', nombre='User', nivel_justif='test')
print(build_asana_text(p))
print(build_slack_text(p, repo_url='r', email='e', asana_url='a'))
"
```

Para validar una corrección real (manual), usá el skill con un repo real
apuntado por URL. Los validators de Parte A y B ya cubren la correctitud de
output; el resto (código limpio, documentación, nivel) lo determina el LLM
según el skill.

## Decisiones de diseño que NO hay que revertir

Cada una de estas costó su tiempo debuggear. Si querés deshacerlas, primero
leé el motivo.

1. **No generamos Excel.** Se removió el paso de armar el checklist con
   openpyxl + copiar el template + hacer `recalc.py`. Era frágil, la Routine
   se pasaba del límite de tokens al manejar el binario, y Asana terminó
   siendo el registro autoritativo real.

2. **No subimos a Drive.** El conector MCP de Drive no banca archivos
   binarios inline del tamaño de un xlsx con base64. Y sin el xlsx, no hay
   nada que subir.

3. **Conectores MCP (Slack + Asana), no API keys.** OAuth del dueño de la
   Routine. Trade-off aceptado: los mensajes/tasks salen con su identidad,
   no con voz de bot. Se migra a API keys cuando haga falta separación de
   identidad.

4. **La Routine baja el ZIP desde Asana (no clona un repo).** El flow cron
   actual recibe el zip como attachment en la task de Asana. El flow viejo
   (legacy) recibía un `repo_url` vía Google Form y lo clonaba — eso requería
   que el repo fuera público y fallaba mudo con repos privados. El cron no
   tiene ese problema: Asana entrega el zip vía URL firmada.

5. **Templates centralizados en `sca/reporter/templates.py`.** Antes estaban
   duplicados entre `routine/PROMPT.md` (SECCIONES inline en el Paso 9) y
   `sca-corrector/SKILL.md` (template markdown). Cambiar uno y no el otro
   generó inconsistencias. Por favor no vuelvas a poner el template inline.

6. **El nombre del candidato se extrae del título de la task de Asana**
   (entre paréntesis). Se evaluaron custom fields de Asana pero requieren
   disciplina adicional de RRHH al crear la task. La convención
   `"... (Nombre Apellido)"` en el título es liviana y self-documenting.

7. **Auto-detect del tipo de prueba (backend vs frontend).** No se usa un
   custom field — se mira el `package.json` del zip. Si tiene React →
   frontend → invoca `sca-corrector-frontend`. Si no → backend → invoca
   `sca-corrector`. Es menos configurable pero cero fricción para RRHH.

8. **Skill y templates separados para backend vs frontend.** Aunque la
   estructura es paralela (35 vs 23 criterios, 6 vs 4 secciones, mismas
   firmas de builders), se mantienen como dos módulos independientes:
   `sca/reporter/templates.py` + `sca-corrector/SKILL.md` para backend, y
   `sca/reporter/templates_frontend.py` + `sca-corrector-frontend/SKILL.md`
   para frontend. Razones: los checklists vienen de templates oficiales
   distintos (`Requerimientos/Template Backend.xlsx` y `Template Frontend.xlsx`),
   los críticos y secciones son específicos de cada uno, y evolucionan a
   ritmos distintos. La única pieza compartida es `NIVEL_LABEL` (los 4
   niveles son los mismos).

## Pendientes conocidos

- **Activar el flow de frontend en producción.** Hoy el Paso 5 del
  `routine/PROMPT.md` detecta frontend y skipea con un aviso. El skill de
  frontend, el validador con Playwright y el upload de screenshots ya
  existen pero todavía no están enganchados a la Routine. Plan: validar
  con varios candidatos reales hasta que la calibración esté razonable
  (como hicimos con backend), después reemplazar el skip por la invocación
  al skill + validator. Requiere `ASANA_PAT` configurado (ver `routine/SETUP.md`).

- **Nivel no-determinístico.** El mismo test corrido dos veces puede dar
  niveles distintos (pasó con Prueba1 que salió Semi Senior y luego Junior
  con los mismos comentarios). La justificación del nivel que se guarda en
  `scores.json` ayuda a que un humano valide o corrija. Fix de fondo
  pendiente: hacer el árbol de decisión del Paso 7 del skill determinístico
  (reglas explícitas por nivel en lugar de ANDs estrictos que dejan huecos
  en perfiles mixtos).

- **Nivel no-determinístico.** El mismo test corrido dos veces puede dar
  niveles distintos (pasó con Prueba1 que salió Semi Senior y luego Junior
  con los mismos comentarios). La justificación del nivel que se guarda en
  `scores.json` ayuda a que un humano valide o corrija. Fix de fondo
  pendiente: hacer el árbol de decisión del Paso 7 del skill determinístico
  (reglas explícitas por nivel en lugar de ANDs estrictos que dejan huecos
  en perfiles mixtos).

- **`build_slack_text` todavía pide `repo_url` y `email`.** En el flow cron
  no hay repo_url ni email — pasamos el permalink de la task de Asana como
  `repo_url` y `"—"` como `email`. Funciona pero el label en Slack dice
  "Repo:" cuando en realidad es un link a Asana. Cuando se jubile
  definitivamente el flow viejo, refactorizar `templates.py` para usar
  labels más neutros (`source_url` en vez de `repo_url`, email opcional).

- **Skills reusables (análisis pendiente).** En algún momento extraer
  `candidate-repo-bootstrap` (bajar zip / clonar repo + detectar stack +
  instalar deps) como skill reusable, si aparece un segundo corrector. Hoy
  no se justifica.

## Cómo trabajar en este repo con Claude

- Cuando Claude vaya a tocar scoring/formato de **backend**, que **lea
  `sca/reporter/templates.py` primero** — es el archivo cabeza.
- Cuando vaya a tocar scoring/formato de **frontend**, que **lea
  `sca/reporter/templates_frontend.py` primero** y revise
  `sca-corrector-frontend/references/manual.md` para las guías.
- Cuando toque orquestación o configuración de la Routine, que lea
  `routine/PROMPT.md` y `routine/SETUP.md` como par.
- Cambios en el skill de backend requieren leer `sca-corrector/SKILL.md`
  completo, no chunks — el Paso 6 y el 7 tienen muchas guías específicas
  (F4, F20, F25…) que se referencian entre sí.
- Cambios en el skill de frontend requieren leer
  `sca-corrector-frontend/SKILL.md` y `references/manual.md` juntos — el
  manual tiene el detalle por criterio (F101..F135) y el SKILL tiene la
  orquestación (instalación, levantar la app, screenshots, scoring).
- Para pruebas de verificación, preferir el smoke test de arriba antes que
  correr la Routine completa (más rápido, más barato, mismo feedback para
  cambios de formato).
