# SCA Apps Script — Setup

Este Apps Script corre detrás de un Google Form: cuando un candidato lo envía,
el script dispara la Claude Routine pasándole la URL del repositorio del
candidato. La Routine se encarga del resto (clonar, corregir, crear task en
Asana, postear en Slack). **No se usa Drive ni se sube nada al Drive del
propietario del Form** — ver `CLAUDE.md` "Decisiones de diseño".

---

## Paso 1 — Crear el Google Form

Creá un formulario con estas preguntas (los nombres tienen que coincidir
exactamente con los definidos en `trigger.gs` — si cambiás uno, cambiá el
otro):

| Pregunta                                         | Tipo            | Requerido |
|--------------------------------------------------|-----------------|-----------|
| Nombre                                           | Respuesta corta | Sí        |
| Apellido                                         | Respuesta corta | Sí        |
| Correo Electrónico (Email)                       | Respuesta corta | Sí        |
| Enlace al Repositorio (Link al Repositorio)      | Respuesta corta | Sí        |

En el campo "Enlace al Repositorio" conviene agregar una descripción breve
para el candidato:

> Pegá la URL HTTPS de tu repo público en GitHub, GitLab o Bitbucket.
> Ejemplo: `https://github.com/tu-usuario/prueba-sca`

> **Repo privado:** por ahora sólo andan repos públicos. Si el candidato manda
> un repo privado, la Routine falla al clonar en el Paso 2 y aborta. Ver
> `CLAUDE.md` → "Pendientes conocidos".

---

## Paso 2 — Abrir el Apps Script

1. Abrí la hoja de respuestas del Form (Responses → Open in Sheets)
2. En Sheets: **Extensiones → Apps Script**
3. Borrá el código de ejemplo y pegá el contenido de `trigger.gs`
4. Guardá el proyecto (Ctrl+S) con el nombre "SCA Trigger"

---

## Paso 3 — Configurar los secrets

Antes de ejecutar `setup()`, necesitás los valores de la Routine (ver
`routine/SETUP.md`, Paso 5 — API trigger).

En el editor de Apps Script, abrí la función `setup`, reemplazá los valores en
el código con los reales, seleccioná `setup` en el dropdown y hacé click en
**Ejecutar**:

```javascript
props.setProperties({
  // URL del endpoint /fire (obtenela de claude.ai/code/routines → Edit → API trigger)
  ROUTINE_ENDPOINT_URL: "https://api.claude.ai/v1/routines/<routine_id>/fire",

  // Bearer token por-Routine (se genera en el mismo modal)
  ROUTINE_TOKEN: "sk-ant-oat01-...",
});
```

Los secrets quedan guardados en Script Properties — no en el código.

> **Nota:** Slack y Asana se configuran directamente en la Routine (conectores
> MCP + env vars `SLACK_CHANNEL` y `ASANA_PROJECT_GID`), no en Apps Script.
> Apps Script sólo necesita saber cómo llamar a la Routine.

---

## Paso 4 — Configurar el trigger

1. En el editor: **Triggers** (ícono del reloj) → **+ Agregar trigger**
2. Configurar:
   - Función: `onFormSubmit`
   - Fuente de eventos: **Desde hoja de cálculo**
   - Tipo de evento: **Al enviar formulario**
3. Guardar — te va a pedir autorizar los permisos. Con el flujo actual el
   script sólo necesita:
   - **Sheets** (para escribir el Session ID en la fila de la respuesta)
   - **URL Fetch** (para llamar el endpoint de la Routine)
   - **Mail** (para mandar el email de error si algo revienta)

---

## Paso 5 — Probar

Antes de depender del Form real, probá con la función `testTrigger()`:

1. En `testTrigger()`, reemplazá la URL del repo de ejemplo por una URL real
   de un repo de prueba público.
2. Ejecutá `testTrigger()` desde el editor (la primera vez te pedirá
   autorizar los permisos).
3. Revisá los logs: **Ver → Registros** (o `Executions` en el panel lateral).

Si todo funciona, deberías ver en los logs algo parecido a:

```
Nueva respuesta recibida
Candidato: García, Juan (juan@ejemplo.com)
Repositorio: https://github.com/juangarcia/prueba-tecnica
Session URL: https://claude.ai/code/sessions/ses_abc123
✅ Routine iniciada. Session ID: ses_abc123
```

Podés abrir la Session URL en el browser para ver la corrección corriendo en
tiempo real.

Una vez confirmado, mandá el Form "real" desde otro navegador o modo incógnito
para verificar el trigger automático.

---

## Qué pasa después (flujo completo)

```
Candidato completa Form
  │
  ▼
onFormSubmit(e)  ← este script
  │
  ├── Valida que la URL sea un repo Git reconocido
  ├── Llama POST /v1/routines/<id>/fire
  │   body: { text: JSON.stringify({ repo_url, candidate }) }
  │
  ▼
Claude Routine (claude.ai/code/routines)
  │
  ├── Paso 1..7: clonar + validar + scorear
  ├── Paso 8:    consolidar scores.json
  ├── Paso 9:    crear task en Asana (vía conector MCP)
  └── Paso 10:   postear en Slack (vía conector MCP)
```

El único rastro en Google Workspace es la fila en la hoja de respuestas del
Form, con el Session ID de la Routine agregado en la última columna para
trazabilidad.

---

## Troubleshooting

**`ROUTINE_ENDPOINT_URL no configurado`** → Correr `setup()` después de
pegar los valores reales.

**`Routines API error 401`** → El `ROUTINE_TOKEN` caducó o es inválido.
Regenerarlo desde `claude.ai/code/routines → Edit → API trigger`.

**`URL inválida o no reconocida`** → El candidato escribió algo que no
matchea GitHub / GitLab / Bitbucket. El script manda un email al dueño
avisando y no dispara la Routine.

**La Routine arranca pero falla al clonar** → Casi siempre es repo privado
o URL tipeada con una letra de más. Revisá el Session URL para ver el
mensaje exacto del `git clone`.
