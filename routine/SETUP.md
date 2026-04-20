# SCA Routine — Setup

Guía para crear y configurar la Routine en Claude Code que ejecuta la corrección
automática cuando un candidato envía el formulario.

---

## Prerequisitos

- Cuenta claude.ai con plan **Pro, Max, Team o Enterprise**
- Claude Code on the web habilitado (Settings → Claude Code)
- El repositorio SCA en GitHub (necesario para que la Routine acceda a los
  validadores Python y al template del Excel)
- Slack Webhook URL
- Asana Personal Access Token + Project GID

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
> (`sca/validators/`) y al template del Excel (`Correccion/Checklist corrección.xlsx`).

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
# Instalar dependencias del SCA
cd /workspace
pip install -r requirements.txt --break-system-packages --quiet 2>/dev/null || true
pip install openpyxl requests --break-system-packages --quiet

# Instalar curl, unzip (disponibles en el entorno por defecto)
which curl unzip python3
echo "✅ Entorno listo"
```

### Network access
Seleccionar **Full** — la Routine necesita descargar ZIPs desde Google Drive
y llamar a las APIs de Slack y Asana.

### Environment variables
Agregar las siguientes variables:

| Variable              | Valor                                        |
|-----------------------|----------------------------------------------|
| `SLACK_WEBHOOK_URL`   | `https://hooks.slack.com/services/...`       |
| `ASANA_PAT`           | `1/123456:...` (Personal Access Token)       |
| `ASANA_PROJECT_GID`   | `123456789` (GID del proyecto en Asana)      |

> Los secretos de Slack y Asana van acá, NO en Apps Script.

---

## Paso 4 — Configurar connectors MCP (opcional)

Si querés que la Routine use MCP para Drive o Slack en lugar de llamadas curl:

1. Ir a la sección **Connectors** de la Routine
2. Agregar **Google Drive** — para subir el Excel directamente a la carpeta de resultados
3. Agregar **Slack** — para enviar el mensaje de resultado

> Si no configurás connectors, la Routine usará curl con las variables de entorno.

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
2. Reemplazar `REPLACE_WITH_REAL_FILE_ID` en `testTrigger()` con el ID real de
   un ZIP de prueba en Drive
3. Ejecutar `testTrigger()`
4. Revisar los logs — deberías ver la Session URL

### Prueba completa

1. Completar el Google Form con datos de prueba y subir un ZIP real
2. El trigger `onFormSubmit` se ejecuta automáticamente
3. En el Sheets deberías ver el Session ID en la última columna de la fila
4. Abrir la Session URL para ver la corrección en tiempo real

---

## Estructura resultante

```
Google Form  →  Drive (ZIP) + Sheets (datos)
                        ↓
              Apps Script (onFormSubmit)
                        ↓
              Claude Routine API (/fire)
                        ↓
              Routine session (cloud):
                1. Descarga ZIP
                2. Corre validadores Python
                3. Analiza código
                4. Genera Excel
                5. Sube Excel a Drive
                6. Notifica Slack
                7. Crea tarea Asana
```

---

## Troubleshooting

**Error 401 en Apps Script:** El `ROUTINE_TOKEN` es incorrecto o venció.
Regenerá el token en claude.ai/code/routines → Edit → API trigger → Regenerate.

**Error 400 "invalid_request_error":** Falta el header `anthropic-beta`.
Ya está incluido en `trigger.gs` — verificá que estés usando la versión más reciente.

**La Routine no encuentra el validador:**
Verificar que el repo SCA esté conectado y que `sca/validators/` exista en el repo.

**ZIP no se descarga:** El archivo de Drive no está compartido como "anyone with link".
El script `makeFileDownloadable()` en Apps Script lo hace automáticamente.
