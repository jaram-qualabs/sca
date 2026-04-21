# SCA Routine — Setup

Guía para crear y configurar la Routine en Claude Code que ejecuta la corrección
automática cuando un candidato envía el formulario.

---

## Prerequisitos

- Cuenta claude.ai con plan **Pro, Max, Team o Enterprise**
- Claude Code on the web habilitado (Settings → Claude Code)
- El repositorio SCA en GitHub (necesario para que la Routine acceda a los
  validadores Python y al skill)
- Workspace de **Slack** donde vas a postear resultados y alertas
- Proyecto de **Asana** donde se crean las tasks de corrección, y su GID
  (lo sacás de la URL: `app.asana.com/0/<PROJECT_GID>/...`)

> No necesitás webhook de Slack ni Personal Access Token de Asana — la Routine
> usa **conectores MCP** con OAuth del dueño de la Routine. Ver Paso 4.

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

> La Routine conecta el repo para tener acceso al código Python de los validadores
> (`sca/validators/`) y al skill de corrección (`sca-corrector/SKILL.md`).

---

## Paso 2 — Crear la Routine

1. Ir a [claude.ai/code/routines](https://claude.ai/code/routines)
2. Click en **New routine**
3. Completar el formulario:

### Nombre
```
SCA — Corrector de Pruebas Técnicas
```

### Prompt
Copiar el contenido completo de `routine/PROMPT.md` (este repo).

### Repositorio
Conectar el repo `qualabs/sca` (o el nombre que le hayas dado).

---

## Paso 3 — Configurar el entorno (Cloud Environment)

En la sección **Environment** de la Routine:

### Setup script
```bash
# El candidato trae sus propias deps — la Routine las instala dinámicamente
# en el Paso 4 del PROMPT. Acá solo chequeamos que las herramientas base
# estén disponibles.
cd /workspace
which git curl unzip python3 pip node npm
echo "✅ Entorno listo"
```

> Ya no instalamos `openpyxl` ni `requests`: sacamos el paso del Excel y los
> conectores MCP se llaman con tools, no con `curl`.

### Network access
Seleccionar **Full** — la Routine necesita clonar el repo del candidato
(GitHub/GitLab) e instalar dependencias (pip/npm).

### Environment variables
Agregar solo estas dos referencias (no son secretos — son IDs/nombres):

| Variable            | Valor                                                              |
|---------------------|--------------------------------------------------------------------|
| `SLACK_CHANNEL`     | Canal destino, ej. `#sca-correcciones` (o el ID del canal)         |
| `ASANA_PROJECT_GID` | GID del proyecto en Asana, ej. `1234567890123456`                  |

> Los secretos de Slack y Asana **no van acá** — se configuran vía OAuth
> en los conectores MCP del Paso 4.

---

## Paso 4 — Configurar conectores MCP (requerido)

La Routine usa dos conectores MCP con OAuth del dueño. Activalos en la sección
**Connectors** de la Routine:

1. **Slack** — para postear correcciones (Paso 10 del PROMPT) y alertas de
   error de los pasos críticos (Paso 0 del PROMPT).
2. **Asana** — para crear la task con el feedback formateado (Paso 9 del PROMPT).

Para cada uno, hacer click en **Connect**, autorizar el workspace correcto, y
verificar que el panel muestre "Connected" antes de seguir.

> **Trade-off conocido:** los mensajes de Slack y las tasks de Asana quedan
> creados con la identidad del dueño de la Routine (no con una voz de bot
> dedicada). Aceptable para v1; migrar a API keys (webhook Slack + PAT Asana)
> cuando se necesite separación de identidad o más robustez en modo
> unattended.

---

## Paso 5 — Agregar el trigger de API

1. En la sección **Triggers** → **Add trigger** → **API**
2. Click en **Generate token**
3. El modal te muestra:
   - **Endpoint URL**: algo como `https://api.claude.ai/v1/routines/<routine_id>/fire`
   - **Bearer token**: algo como `sk-ant-oat01-...`
4. **Copiá ambos valores** — los vas a necesitar en el Paso siguiente.
   No los vas a poder ver de nuevo (podés regenerar si los perdés).

---

## Paso 6 — Cargar los secrets en Apps Script

Con el endpoint URL y el token del paso anterior:

1. Abrir el editor de Apps Script del Google Sheet de respuestas
2. En `trigger.gs`, reemplazar los valores en la función `setup()`:
   ```javascript
   ROUTINE_ENDPOINT_URL: "https://api.claude.ai/v1/routines/<routine_id>/fire",
   ROUTINE_TOKEN:        "sk-ant-oat01-...",
   ```
3. Seleccionar la función `setup` en el dropdown y hacer click en **Ejecutar**
4. Verificar en los logs que dice `✅ Secrets guardados en Script Properties.`

---

## Paso 7 — Probar el flujo completo

### Prueba rápida (sin formulario)

1. En el editor de Apps Script, abrir `trigger.gs`
2. Ajustar los valores de prueba en `testTrigger()` (repo URL del candidato
   y datos del candidato)
3. Ejecutar `testTrigger()`
4. Revisar los logs — deberías ver la Session URL

### Prueba completa

1. Completar el Google Form con datos de prueba y la URL del repo del candidato
2. El trigger `onFormSubmit` se ejecuta automáticamente
3. En el Sheets deberías ver el Session ID en la última columna de la fila
4. Abrir la Session URL para ver la corrección en tiempo real
5. Al finalizar, verificar:
   - Una task nueva en el proyecto de Asana (con el checklist formateado)
   - Un mensaje en el canal de Slack `$SLACK_CHANNEL`

---

## Estructura resultante

```
Google Form  →  Sheets (datos del candidato + repo URL)
                        ↓
              Apps Script (onFormSubmit)
                        ↓
              Claude Routine API (/fire)
                        ↓
              Routine session (cloud):
                1. Clona el repo del candidato
                2. Corre validadores Python (Parte A y B)
                3. Analiza calidad del código
                4. Determina nivel + justificación
                5. Persiste scores.json
                6. Crea task en Asana (registro autoritativo)
                7. Notifica en Slack (best-effort)
```

---

## Troubleshooting

**Error 401 en Apps Script:** El `ROUTINE_TOKEN` es incorrecto o venció.
Regenerá el token en claude.ai/code/routines → Edit → API trigger → Regenerate.

**Error 400 "invalid_request_error":** Falta el header `anthropic-beta`.
Ya está incluido en `trigger.gs` — verificá que estés usando la versión más reciente.

**La Routine no encuentra el validador:**
Verificar que el repo SCA esté conectado y que `sca/validators/` exista en el repo.

**El Paso 9 falla con "tool not available" o similar:** El conector de Asana no
está habilitado en la Routine. Ir a **Connectors** y verificar que diga
"Connected". Misma idea para Slack en el Paso 10.

**El Paso 0 aborta con "faltan env vars":** No configuraste `SLACK_CHANNEL`
o `ASANA_PROJECT_GID` en la sección Environment variables de la Routine.

**No se pudo clonar el repo del candidato:** Si el candidato usó un repo
privado sin darte acceso, el `git clone` falla. En ese caso, la Routine
alerta a Slack con el error y corta antes del análisis.
