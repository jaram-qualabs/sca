# SCA Apps Script — Setup

## Paso 1 — Crear el Google Form

Creá un formulario con estas preguntas (los nombres tienen que coincidir exactamente):

| Pregunta              | Tipo              |
|-----------------------|-------------------|
| Nombre                | Respuesta corta   |
| Apellido              | Respuesta corta   |
| Email                 | Respuesta corta   |
| ZIP de la solución    | Carga de archivos |

En la configuración del campo de archivo:
- Tipos de archivo permitidos: `.zip`
- Tamaño máximo: 100 MB

---

## Paso 2 — Abrir el Apps Script

1. Abrí la hoja de respuestas del Form (Responses → Open in Sheets)
2. En Sheets: **Extensiones → Apps Script**
3. Borrá el código de ejemplo y pegá el contenido de `trigger.gs`
4. Guardá el proyecto (Ctrl+S) con el nombre "SCA Trigger"

---

## Paso 3 — Configurar los secrets

Antes de ejecutar `setup()`, necesitás los valores de la Routine (ver `routine/SETUP.md`).

En el editor de Apps Script, seleccioná la función `setup` en el dropdown y hacé click en **Ejecutar**. Reemplazá los valores en el código:

```javascript
props.setProperties({
  // URL del endpoint /fire (obtenela de claude.ai/code/routines → Edit → API trigger)
  ROUTINE_ENDPOINT_URL: "https://api.claude.ai/v1/routines/<routine_id>/fire",

  // Bearer token por-Routine (se genera en el mismo modal)
  ROUTINE_TOKEN: "sk-ant-oat01-...",
});
```

Los secrets quedan guardados en Script Properties — no en el código.

> **Nota:** Los secrets de Slack y Asana se configuran directamente en la Routine (en claude.ai/code/routines), no en Apps Script. Apps Script solo necesita saber cómo llamar a la Routine.

---

## Paso 4 — Configurar el trigger

1. En el editor: **Triggers** (ícono del reloj) → **+ Agregar trigger**
2. Configurar:
   - Función: `onFormSubmit`
   - Fuente de eventos: **Desde hoja de cálculo**
   - Tipo de evento: **Al enviar formulario**
3. Guardar — te va a pedir autorizar los permisos de Drive, Sheets y Mail

---

## Paso 5 — Probar

Antes de activar el trigger real, probá con la función `testTrigger()`:
1. Subí un ZIP de prueba a Drive y copiá su ID
2. Reemplazá `REPLACE_WITH_REAL_FILE_ID` en `testTrigger()`
3. Ejecutá `testTrigger()` desde el editor
4. Revisá los logs: **Ver → Registros**

Si todo funciona, deberías ver en los logs:
```
Candidato: García, Juan (juan@ejemplo.com)
File ID del ZIP: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
URL de descarga: https://drive.google.com/uc?export=download&id=...
Carpeta de resultados: 1a2b3c4d...
Session URL: https://claude.ai/code/sessions/ses_abc123
✅ Routine iniciada. Session ID: ses_abc123
```

Podés abrir la Session URL en el browser para ver la corrección en tiempo real.

---

## Estructura de carpetas en Drive

El script crea automáticamente esta estructura:

```
Mi Drive/
└── SCA - Resultados/
    ├── García_Juan/
    │   └── Checklist_García_Juan.xlsx
    └── Lopez_Maria/
        └── Checklist_Lopez_Maria.xlsx
```
