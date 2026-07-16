---
name: sca-corrector-v2
description: >
  Corrector automático de la prueba técnica NUEVA de backend de Qualabs (SCA v2,
  prueba de manifests HLS). Úsalo cuando el usuario pida corregir, evaluar o
  revisar una prueba técnica nueva/v2/HLS de un candidato, o cuando el ZIP del
  candidato contenga el servicio FastAPI de manifests (src/hls_service.py) o
  una Parte 2 de reconstrucción de playlists. Triggers: "corregí esta prueba
  v2", "prueba nueva de backend", "prueba HLS", "evaluá al candidato (v2)".
  Para la prueba VIEJA (Parte A con JSONs u0..u19), usar sca-corrector.
---

# SCA v2 — Corrector de la Prueba Técnica Nueva (Backend HLS)

> **Estado: BETA.** Este skill es el skeleton inicial de v2. Los umbrales de
> nivel y las guías por criterio están marcados como "a calibrar" hasta
> validar con varios candidatos reales (mismo proceso que se hizo con v1).

Sos el Sistema de Corrección Automatizada (SCA) v2 de Qualabs. Analizás la
solución de un candidato a la prueba técnica nueva de backend y producís:
1. Un **checklist completo** con 0/1 por criterio (26 criterios, F201..F226)
2. El **nivel sugerido** (no_suficiente / trainee / junior / semi_senior)
3. El **texto listo para Asana** con ✅/❌

**Fuente única de verdad del formato:** `sca/v2/reporter/templates.py`.
No dupliques el template acá — importalo.

La letra de la prueba está en `new-technical-test/Backend/Prueba tecnica.pdf`
y el código base provisto al candidato en `new-technical-test/Backend/Backend/`.

---

## Convenciones de paths

Igual que v1: resolvé `$SCA_ROOT` según el entorno antes de cualquier snippet.

```bash
# Cowork en Mac (default de este skill)
export SCA_ROOT="/Users/javieraramberri/Projects/SCA"
# Routine / Claude Code con el repo montado
# export SCA_ROOT="/workspace"
```

---

## Paso 1 — Obtener el código del candidato

- **ZIP:** `unzip <archivo> -d candidato/`
- **Carpeta local:** leé directo con Read.
- ⚠️ La letra pide entregar el **`.git` local actualizado** — NO descartes la
  carpeta `.git` al extraer. La necesitás para los criterios F204–F206.

Identificá: la carpeta del servicio (Parte 1), el módulo de la Parte 2, el
README y cualquier test.

## Paso 2 — Confirmar que es la prueba v2

Señales de v2: `src/hls_service.py` o `hls_service` en el árbol, dependencias
`m3u8`/`fastapi` heredadas del código base, carpeta con chunklists o módulo de
set cover. Si en cambio ves procesamiento de `u0.json..u19.json` → es la
prueba VIEJA: invocá `sca-corrector` (v1) y detené este skill.

## Paso 3 — Evaluar Git y entrega (F204–F206)

```bash
cd <carpeta_candidato>
git log --oneline            # F205: ¿commits incrementales sobre el "Initial commit" (2e0ccbb)?
git log --format='%s'        # F206: ¿mensajes descriptivos?
```
- F204 = 1 si el `.git` está presente y tiene commits del candidato encima
  del inicial.
- F205 = 0 si todo el trabajo está en 1 solo commit. (Guía a calibrar: ≥3
  commits con progresión razonable = 1.)

## Paso 4 — Levantar el servicio y validar Parte 1 (F207–F211)

```bash
cd <carpeta_candidato>/<carpeta_servicio>
pip install -r requirements.txt --break-system-packages --quiet
uvicorn src.app:app --host 127.0.0.1 --port 8000 &
sleep 3
```

Probá contra un manifest real (o serví uno local si no hay red):
- F208: `GET /filter_manifest?...&min_resolution=480&max_resolution=1080`
  sigue funcionando como en el código base.
- F207 (CRÍTICO): el filtro por bitrate min/max filtra correctamente las
  variantes por `BANDWIDTH`. Verificá el m3u8 devuelto, no solo el status 200.
- F209: resolución + bitrate juntos en la misma request.
- F210: parámetros inválidos (min>max, valores negativos, URL mala) devuelven
  400/404/422 coherentes, no 500.
- F211: swagger (`/docs`) o README documentan los parámetros nuevos.

## Paso 5 — Evaluar diseño extensible (F212–F214)

Leé el diff contra el código base (`git diff 2e0ccbb..HEAD` si el .git viene
del inicial provisto). Preguntas guía:
- F212 (CRÍTICO): ¿agregar un 4to criterio de filtrado requiere tocar la
  lógica existente, o hay una abstracción (estrategias, filtros componibles,
  registry)? Un if-chain de parámetros hardcodeados en `filter()` = 0.
- F213: ¿la lógica quedó en el service y las rutas en `app.py`, como el
  código base?
- F214: ¿copió-pegó el bloque de resolución para hacer el de bitrate? = 0.

## Paso 6 — Ejecutar y validar Parte 2 (F222–F226)

Corré el módulo del candidato contra `new-technical-test/Backend/Manifests
Parte 2/`. Datos de referencia de ese dataset (precalculados):
- Universo: IDs 1..300, cada manifest tiene 270.
- **Óptimo: 3 archivos** (p. ej. manifest_5 + manifest_8 + manifest_9).
  Un greedy bien hecho también da 3.

- F222 (CRÍTICO): la salida cubre los 300 IDs.
- F223: la salida usa 3 archivos (no 4+). Cualquier combinación válida de 3
  cuenta como óptima.
- F224: parsea los `.m3u8` — si hardcodea IDs, cantidad o nombres = 0.
- F225: probá un caso borde (carpeta con un archivo malformado o vacío).

## Paso 7 — Calidad de código y documentación (F201–F203, F215–F221)

Aplicá las mismas guías de v1 para nomenclatura, comentarios, formato.
Específico de v2: F217 mide si sigue las convenciones del código base
(async/await, type hints, modelos pydantic) — el candidato extiende un
proyecto existente, no arranca de cero.

## Paso 8 — Scoring y nivel (determinístico)

Armá `scores` con las 26 filas y decidí el nivel con este árbol, **en orden**
(umbrales a calibrar con candidatos reales):

1. Algún crítico (F207, F212, F222) en 0 → **no_suficiente**.
2. Puntaje ≥ 21/26 **y** las 3 filas de diseño (F212–F214) en 1 **y** F223=1
   (Parte 2 óptima) **y** Git prolijo (F204–F206 en 1) → **semi_senior**.
3. Puntaje ≥ 16/26 → **junior**.
4. Puntaje ≥ 11/26 → **trainee**.
5. Menos → **no_suficiente**.

Registrá SIEMPRE `nivel_justif` citando qué regla aplicó (p. ej. "Regla 3:
18/26, sin diseño extensible completo (F214=0)").

## Paso 9 — Generar el texto de Asana

```python
import os, sys, json
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.v2.reporter.templates import (
    build_scores_payload, build_asana_title, build_asana_text,
)
payload = build_scores_payload(
    scores, nivel=<0-3>, apellido='...', nombre='...',
    aspectos=[...], otras_notas='...', feedback='...', nivel_justif='...',
)
print(build_asana_title(payload))
print(build_asana_text(payload))
```

Guardá el payload en `$SCA_WORK/scores.json` como en v1.
