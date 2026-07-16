---
name: sca-corrector-frontend-v2
description: >
  Corrector automático de la prueba técnica NUEVA de frontend de Qualabs (SCA
  v2, dashboard HLS + player). Úsalo cuando el usuario pida corregir una prueba
  técnica nueva/v2 de frontend, o cuando el ZIP contenga una SPA (React u otro
  framework) que consume el servicio FastAPI de manifests HLS
  (validate_manifest / parse_manifest / filter_manifest). Triggers: "corregí
  esta prueba frontend v2", "prueba nueva de frontend", "dashboard HLS".
  Para la prueba VIEJA de frontend (módulos con redux), usar
  sca-corrector-frontend.
---

# SCA v2 — Corrector de la Prueba Técnica Nueva (Frontend HLS)

> **Estado: BETA.** Skeleton inicial de v2. Umbrales de nivel y guías por
> criterio a calibrar con candidatos reales.

Analizás la solución de un candidato a la prueba nueva de frontend y producís:
1. Un **checklist completo** con 0/1 por criterio (29 criterios, F301..F329)
2. El **nivel sugerido** (no_suficiente / trainee / junior / semi_senior)
3. El **texto listo para Asana** con ✅/❌

**Fuente única de verdad del formato:** `sca/v2/reporter/templates_frontend.py`.

La letra está en `new-technical-test/Frontend/Prueba Tecnica.pdf` (páginas de
"Prueba Frontend"), el backend provisto en `new-technical-test/Frontend/Backend/`
y el Figma de referencia linkeado en el PDF.

---

## Convenciones de paths

```bash
export SCA_ROOT="/Users/javieraramberri/Projects/SCA"   # Cowork en Mac
# export SCA_ROOT="/workspace"                          # Routine
```

---

## Paso 1 — Obtener el código y confirmar que es v2

- Extraé el ZIP conservando `.git` (necesario para F304–F306).
- Señales de v2: la SPA llama a `validate_manifest` / `parse_manifest` /
  `filter_manifest`, usa `hls.js` / `video.js` / librería de charts. Si en
  cambio ves los módulos con redux de la prueba vieja → invocá
  `sca-corrector-frontend` (v1) y detené este skill.

## Paso 2 — Levantar backend provisto + app del candidato

```bash
# Backend FastAPI (el provisto en la prueba)
cd "$SCA_ROOT/new-technical-test/Frontend/Backend"
pip install -r requirements.txt --break-system-packages --quiet
uvicorn src.app:app --host 127.0.0.1 --port 8000 &

# App del candidato
cd <carpeta_candidato>
npm install --silent
npm run dev &   # o el script que indique el README
```

Si el candidato modificó/embebió el backend, usá su versión y anotalo en
`otras_notas`.

## Paso 3 — Evaluar Git y entrega (F304–F306)

Igual que backend v2: `.git` presente con commits del candidato (F304),
commits incrementales (F305), mensajes descriptivos (F306).

## Paso 4 — Validación funcional con Playwright (F307–F316)

Usá Playwright (como el validator de FE v1) para recorrer la app y sacar
screenshots como evidencia. Manifest de prueba:
`https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8`

**Req 1 — Dashboard (F307–F310):**
- F307 (CRÍTICO): ingresar la URL valida y muestra el resultado sin recargar.
- F308: con una URL inválida o un manifest roto, el error se muestra claro.
- F309: hay gráficos para resolución, bandwidth, codecs y duración total.
- F310: los tipos de gráfico son razonables y legibles (a calibrar).

**Req 2 — Filtro (F311–F313):**
- F311: sliders de rango de resolución (no inputs de texto).
- F312 (CRÍTICO): aplicar el filtro obtiene el manifest filtrado (verificar
  la respuesta, no solo la UI).
- F313: estados de loading/error/rango vacío.

**Req 3 — Player (F314–F316):**
- F314 (CRÍTICO): reproduce una variante del `parse_manifest`.
- F315: cambia de resolución dinámicamente sin romper la reproducción.
- F316: cambia de pista de audio si el manifest las tiene.

Sacá screenshots de cada requerimiento y subilos a Asana con
`sca/asana/attachments.py` (requiere `ASANA_PAT`), igual que FE v1.

## Paso 5 — UI y fidelidad (F317–F319)

Compará screenshots contra el Figma de referencia (F317). Achicá la ventana
para verificar responsive (F318). F319: consistencia entre vistas.

## Paso 6 — Calidad del código (F320–F329)

Guías clave:
- F321: las llamadas al backend viven en hooks/servicios, no inline en JSX.
- F324: no mezcla componentes de clase y funcionales (heredado de v1, era
  crítico allá; acá F325 duplicado sigue siendo el crítico).
- F329 (bonus): tiene tests (`vitest`/`jest`/`testing-library`).
- Nota: la letra prefiere React pero el framework es libre — si no es React,
  aplicá F320–F328 con los equivalentes del framework y anotalo en
  `otras_notas`.

## Paso 7 — Scoring y nivel (determinístico)

Árbol **en orden** (umbrales a calibrar):

1. Algún crítico (F307, F312, F314, F325) en 0 → **no_suficiente**.
2. Puntaje ≥ 24/29 **y** los 3 requerimientos completos (F307–F316 todos 1)
   **y** Git prolijo (F304–F306 en 1) → **semi_senior**.
3. Puntaje ≥ 18/29 → **junior**.
4. Puntaje ≥ 12/29 → **trainee**.
5. Menos → **no_suficiente**.

Registrá SIEMPRE `nivel_justif` citando la regla aplicada.

## Paso 8 — Generar el texto de Asana

```python
import os, sys
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.v2.reporter.templates_frontend import (
    build_scores_payload, build_asana_title, build_asana_text,
)
payload = build_scores_payload(
    scores, nivel=<0-3>, apellido='...', nombre='...',
    aspectos=[...], otras_notas='...', feedback='...', nivel_justif='...',
)
print(build_asana_title(payload))
print(build_asana_text(payload))
```
