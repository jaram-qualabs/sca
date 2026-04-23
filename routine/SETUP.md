# SCA Routine — Setup

Guía para crear y configurar la Routine en Claude Code que ejecuta la corrección
automática **en modo cron** (una vez al día, poleando Asana).

> Este setup describe el **flow actual** (Asana-triggered, cron). El flow viejo
> basado en Google Form sigue documentado en `routine/PROMPT-form.md.legacy` +
> `apps-script/SETUP.md`, y no está activo. Si querés volver a activarlo, leé
> esos archivos — pero el flow actual lo reemplaza.

---

## Prerequisitos

- Cuenta claude.ai con plan **Pro, Max, Team o Enterprise**
- Claude Code on the web habilitado (Settings → Claude Code)
- El repositorio SCA en GitHub (necesario para que la Routine acceda a los
  validators y al skill)
- Workspace de **Slack** donde postear resultados y alertas
- Proyecto de **Asana** con:
  - Una section llamada **"Para corregir"** (el nombre es configurable vía env var)
  - Su GID (de la URL: `app.asana.com/0/<PROJECT_GID>/...`)

> No necesitás webhook de Slack ni Personal Access Token de Asana — la Routine
> usa **conectores MCP** con OAuth del dueño de la Routine (Paso 4).

---

## Paso 1 — Subir el repo SCA a GitHub

Si todavía no está en GitHub:

```bash
cd /Users/javieraramberri/Projects/SCA
git init
git add .
git commit -m "chore: initial commit"
gh repo create qualabs/sca --private --push --source .
```

La Routine conecta el repo para tener acceso al código Python de los validators
(`sca/validators/`), al reporter (`sca/reporter/templates.py`) y al skill de
corrección (`sca-corrector/SKILL.md`).

---

## Paso 2 — Crear la Routine

1. Ir a [claude.ai/code/routines](https://claude.ai/code/routines)
2. Click en **New routine**
3. Completar:

### Nombre

```
SCA — Corrector diario de Pruebas Técnicas
```

### Prompt

Copiar el contenido completo de `routine/PROMPT.md` (este repo).

### Repositorio

Conectar el repo `qualabs/sca` (o el nombre que le hayas dado).

---

## Paso 3 — Configurar el entorno (Cloud Environment)

### Setup script

```bash
cd /workspace
which git curl unzip python3 pip node npm file
echo "✅ Entorno listo"
```

### Network access

Modo **Custom** con estos dominios permitidos (además de los que la Routine
necesite por default para git/npm/pip):

```
asanausercontent.com
*.asanausercontent.com
```

Sin esto, el Paso 4 del PROMPT falla al descargar el zip firmado de Asana con
`403 "Host not in allowlist"` o `503 "DNS cache overflow"`.

> Si también vas a mantener el flow viejo (o tus candidatos clonan de repos
> privados por SSH), agregá los dominios que correspondan (`github.com`,
> `gitlab.com`, etc.).

### Environment variables

En la sección **Environment variables** de la Routine, agregá estas tres
referencias (no son secretos):

| Variable             | Valor                                                          |
|----------------------|----------------------------------------------------------------|
| `SLACK_CHANNEL`      | Canal destino, ej. `#sca-correcciones`                         |
| `ASANA_PROJECT_GID`  | GID del proyecto Asana, ej. `1200429007986535`                 |
| `ASANA_SECTION_NAME` | (opcional, default `Para corregir`) nombre de la section       |

**Cómo conseguir los valores:**

- `SLACK_CHANNEL`: nombre del canal con `#` adelante (el conector MCP lo
  resuelve) o el ID del canal (en Slack: click derecho sobre el canal →
  **View channel details** → al final del modal, "Channel ID", empieza con `C...`).
- `ASANA_PROJECT_GID`: abrí el proyecto en Asana; la URL tiene el formato
  `app.asana.com/0/1234567890123456/list`. El número es el GID.

> Los tokens de Slack/Asana **no van acá** — se configuran vía OAuth en los
> conectores MCP (Paso 4).
> El Paso 0.2 del PROMPT valida estas variables con fail-fast: si falta alguna,
> la Routine corta con mensaje claro antes de hacer llamadas MCP.

---

## Paso 4 — Configurar conectores MCP

La Routine usa dos conectores MCP con OAuth del dueño. Activalos en la sección
**Connectors**:

1. **Asana** — listar sections/tasks/attachments, descargar URLs firmadas,
   crear subtask con el feedback, dejar comentarios.
2. **Slack** — postear correcciones y alertas de error.

Para cada uno: click en **Connect**, autorizar el workspace correcto, y
verificar que el panel muestre "Connected" antes de seguir.

> **Trade-off conocido:** los mensajes de Slack y las subtasks de Asana quedan
> creados con la identidad del dueño de la Routine (no con una voz de bot
> dedicada). Aceptable por ahora; migrar a API keys (Slack webhook + Asana
> PAT) cuando se necesite separación de identidad.

---

## Paso 5 — Configurar el schedule (cron diario)

En la sección **Triggers** de la Routine → **Add trigger** → **Schedule**:

- **Frecuencia:** diaria
- **Hora:** `09:00` — zona horaria **`America/Argentina/Buenos_Aires`** (UTC-3)
- Guardar.

Con esto, la Routine corre una vez cada mañana laboral. Latencia máxima para
RRHH: ~24h. Si tu instancia de claude.ai solo permite cron en UTC, usá `12:00`
UTC (equivalente a 9am ART).

> Si querés disparar manualmente (para testear sin esperar al cron), en la
> misma sección Triggers agregá un trigger de tipo **Manual** y usalo desde
> claude.ai.

---

## Paso 6 — Preparar el proyecto de Asana

1. **Crear la section "Para corregir"** si no existe (en el proyecto cuyo GID
   pusiste en `ASANA_PROJECT_GID`).
2. Convenir con RRHH el **flujo operativo**:
   - Al recibir una prueba técnica, RRHH crea una task en ese proyecto.
   - Título: cualquier cosa con el **nombre del candidato entre paréntesis**.
     Ej: `"Prueba técnica (Mateo Pérez)"`.
   - Adjuntan el `.zip` del candidato a la task.
   - Mueven la task a la section **"Para corregir"**.
3. Al día siguiente (o cuando corra el cron), la Routine:
   - Procesa cada task de la section.
   - Crea una subtask `"Comentarios y corrección SCA"` con el feedback.
   - Postea en Slack.
   - La task queda marcada como corregida (por la presencia de la subtask).

> RRHH no necesita mover la task después de la corrección: la idempotencia la
> garantiza la subtask. Si querés, podés tener una Rule de Asana que mueva la
> task a "Corregidas" cuando se crea la subtask — pero es opcional.

---

## Paso 7 — Probar el flujo

### Prueba manual (sin esperar el cron)

1. Asegurate de tener al menos una task de prueba en la section "Para corregir"
   del proyecto Asana configurado, con:
   - Nombre entre paréntesis en el título.
   - Un `.zip` adjunto (con un repo válido de Parte A + Parte B).
2. En claude.ai/code/routines, abrí tu Routine.
3. Dispará el trigger **Manual** (o click en "Run now").
4. Mirá la session URL: deberías ver el batch completo procesando tasks.
5. Al terminar, verificá:
   - Subtask nueva en la task de Asana con el feedback.
   - Mensaje en `$SLACK_CHANNEL` con el resumen.
6. Volvé a disparar la Routine. Esta vez debería saltear la task (porque ya
   tiene la subtask de corrección). Eso confirma la idempotencia del Paso 1.3.

### Prueba del cron

Dejar pasar un día. Al siguiente run programado, revisá los logs de la Routine
en claude.ai y el canal de Slack.

---

## Estructura resultante

```
Cron diario 9am ART
        ↓
Routine session (cloud):
  1. Lista tasks en section "Para corregir"
  2. Filtra las que ya tienen subtask "Comentarios y corrección SCA"
  3. Por cada task restante:
     a. Extrae nombre del título (entre paréntesis)
     b. Baja el .zip más reciente de Asana
     c. Auto-detecta backend vs frontend (frontend se skipea por ahora)
     d. Corrige según el skill sca-corrector
     e. Crea subtask "Comentarios y corrección SCA" con el feedback
     f. Postea en Slack
  4. Resume el batch en Slack
```

---

## Troubleshooting

**Paso 0 aborta con "faltan env vars":** No configuraste `SLACK_CHANNEL` o
`ASANA_PROJECT_GID` en Environment variables. Revisar Paso 3.

**Paso 1 aborta con section no encontrada:** La section `"Para corregir"` no
existe en el proyecto, o tiene otro nombre. Revisá `ASANA_SECTION_NAME` en
Environment variables (o creá la section en Asana).

**Paso 4 falla con HTTP 403 / 503 en la descarga del zip:** Falta el allowlist
de `asanausercontent.com` en Network access. Revisar Paso 3.

**El Paso 4 baja un archivo de pocos bytes y `file` no dice "Zip archive":**
La URL firmada expiró (duran ~29 min). Muy improbable si todo corre en un solo
batch, pero posible si hay un delay artificial entre Paso 1 y Paso 4. Basta
con re-ejecutar.

**Una task falla pero el batch sigue:** Es el comportamiento esperado (Paso 2
del PROMPT — errores per-task no abortan el batch). Revisá el comentario que
quedó en la task en Asana y los logs de la session de la Routine.

**Task con frontend detectado:** La Routine no corrige frontend todavía. Dejó
comentario en la task y Slack de aviso. Corregila manualmente.

**Quiero re-correr una task que ya fue corregida:** Borrá la subtask
`"Comentarios y corrección SCA"` de esa task en Asana. El próximo run la va a
volver a procesar.

**La Routine no encuentra el validator:** Verificá que el repo SCA esté
conectado y que `sca/validators/` + `sca/reporter/` existan en el repo.
