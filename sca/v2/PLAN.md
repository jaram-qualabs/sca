# SCA v2 — Plan de convivencia y migración

Estado: **beta**. v2 corrige la prueba técnica nueva (HLS) y convive con v1
(la prueba de Parte A/B con JSONs) hasta que la vieja se elimine.

## Principio rector

**v2 nunca importa de v1.** Todo lo de v2 vive en tres lugares y nada más:

```
sca/v2/                        Paquete Python de v2
  reporter/templates.py        ⭐ Fuente única de verdad BACKEND v2 (26 criterios)
  reporter/templates_frontend.py  ⭐ Fuente única de verdad FRONTEND v2 (29 criterios)
  PLAN.md                      Este archivo
sca-corrector-v2/              Skill de corrección manual BACKEND v2 (beta)
sca-corrector-frontend-v2/     Skill de corrección manual FRONTEND v2 (beta)
new-technical-test/            Material de la prueba nueva (letra, código base, manifests)
```

`NIVEL_LABEL` está duplicado deliberadamente en `sca/v2/reporter/templates.py`
(v1 lo tiene en `sca/reporter/templates.py`). Es la única duplicación y es el
precio de poder borrar v1 sin tocar v2. `sca/asana/attachments.py` (upload de
screenshots vía PAT) es infraestructura neutral: no es de v1 ni de v2, se
conserva.

## Checklist de eliminación de v1 (cuando llegue el momento)

Borrar, en este orden, y nada más que esto:

1. `sca/reporter/` y `sca/validators/` (templates y validators v1)
2. `sca-corrector/` y `sca-corrector-frontend/` (skills v1)
3. `Prueba tecnica/` y las referencias a `datos prueba tecnica/`
4. En `routine/PROMPT.md`: la rama de detección v1 (queda solo v2)
5. `apps-script/` + `routine/PROMPT-form.md.legacy` si aún existen
6. Actualizar `CLAUDE.md`: eliminar las secciones v1 y promover v2 a "el SCA"

Verificación post-borrado: correr los smoke tests de v2 (abajo) y una
corrección manual con un zip real.

## Mapeo de criterios v1 → v2 (backend)

| v1 | v2 | Nota |
|----|----|------|
| F3–F5 Documentación | F201–F203 | F203 ahora pide explícitamente justificar el diseño extensible |
| F8–F13 Usabilidad (archivos/providers) | — | La prueba nueva no procesa archivos de entrada; eje eliminado |
| F12 hardcodea providers (crítico) | F212 diseño no extensible (crítico) | Mismo espíritu: generalizar vs hardcodear |
| F16–F25 Calidad | F215–F221 | Compactado (comentarios en 1 fila); F217 nuevo: convenciones del código base (async/typing/pydantic); F221 nuevo bonus: tests |
| F28 Parte A correcta (crítico) | F207 filtro bitrate funciona (crítico) | El "core funcional" de la Parte 1 |
| F29 Parte B cubre módulos (crítico) | F222 cubre todos los segmentos (crítico) | El "core funcional" de la Parte 2 |
| F30 set reducido / F31 set mínimo (bonus) | F223 subconjunto óptimo | En v2 el óptimo es criterio pleno: el dataset tiene óptimo conocido = 3 archivos |
| — | F204–F206 Git (nuevo eje) | La letra nueva exige entregar el `.git` actualizado |
| — | F208–F211, F213–F214 (nuevos) | Evolucionar un servicio existente: no romper lo previo, API coherente, capas |
| — | F224–F226 (nuevos) | Parte 2: parseo real de .m3u8, casos borde |

## Mapeo de criterios v1 → v2 (frontend)

| v1 | v2 | Nota |
|----|----|------|
| F101–F103 Documentación | F301–F303 | Igual estructura |
| F104–F108 Usabilidad (archivos/providers) | — | Eje eliminado (no aplica a la prueba nueva) |
| F109–F115 Usabilidad Front (botones/headers/ruteo) | F307–F316 | Reemplazado por funcionalidad de los 3 requerimientos (dashboard, filtro, player) |
| F113–F115 similitud visual/responsive | F317–F319 | Ahora contra el Figma de referencia |
| F116–F124 Calidad | F320–F328 | Compactado |
| F121 código duplicado (crítico) | F325 (crítico) | Se mantiene |
| F125–F134 Calidad Front (redux, SCSS, etc.) | F320–F326 | Redux/SCSS eran de la letra vieja; v2 pide estado adecuado y estilos organizados sin imponer librería |
| F132 mezcla componentes (crítico) | F324 (no crítico) | Sigue siendo criterio, deja de ser crítico |
| F135 Parte A correcta (crítico) | F307/F312/F314 (críticos) | El core funcional ahora son los 3 requerimientos |
| — | F304–F306 Git (nuevo eje) | La letra nueva exige el `.git` |
| — | F329 tests (bonus, nuevo) | |

## Diferencias de API respecto de v1 (intencionales)

- `nivel` es un kwarg explícito de `build_scores_payload`, no una fila mágica
  (34/140) dentro de `scores`.
- `build_scores_payload` valida los críticos: si alguno está en 0 y
  `nivel != 0`, lanza `ValueError`. En v1 esa regla vivía solo en el skill.
- `build_slack_text` usa `source_url` + `email` opcional (resuelve el
  pendiente documentado en CLAUDE.md sobre el label "Repo:").
- El título de Asana lleva prefijo `SCA v2 —` para distinguir correcciones
  durante la convivencia.
- El árbol de decisión del nivel en los skills v2 es determinístico por
  diseño (reglas numeradas con umbrales), atacando de entrada el pendiente
  de no-determinismo de v1. Umbrales **a calibrar** con candidatos reales.

## Detección v1 vs v2 en la Routine (implementada 2026-07-16)

Diseñada para costo de tokens casi nulo:

1. **Tag de Asana `sca-v2`** (señal primaria, configurable vía `ASANA_V2_TAG`):
   RRHH lo agrega a las tasks de la prueba nueva. Se lee gratis en el listado
   del Paso 1.2 (`opt_fields=tags.name`), sin calls extra.
2. **Sniff del zip** (fallback si falta el tag): un grep de una línea sobre lo
   ya descomprimido (`hls_service.py`, `filter_manifest`/`parse_manifest` en
   el código, `hls.js` en package.json, `m3u8` en requirements). Output de una
   palabra.
3. **Sub-flujo v2 lazy**: `routine/v2/CORRECCION.md` es autocontenido
   (criterios inline + árbol de nivel + snippets) y la Routine lo lee UNA vez
   por batch, solo si aparece una task v2. Batches 100% v1 no pagan nada;
   cuando todas las tasks son v2, se saltea la pre-carga de criterios v1 del
   Paso 1.5.

Estado: **v2 backend y v2 frontend corren completos** en la Routine.
Backend: batería funcional con fixture local, diff contra el commit inicial,
Parte 2 contra el dataset oficial. Frontend (habilitado 2026-07-16): validador
`sca/v2/validators/frontend.py` (Playwright + screenshots) contra el backend
provisto y un fixture HLS local generado por `sca/v2/validators/fixture.py`.

Dos aprendizajes técnicos del frontend que NO hay que revertir:

1. **El fixture del player es VP9+Opus, no H.264.** El chromium de Playwright
   no trae codecs propietarios: con el stream h264 de la letra, hls.js corta
   en `manifestIncompatibleCodecsError` y el chequeo de reproducción da falso
   negativo siempre. Con VP9+Opus la reproducción es real (`currentTime`
   avanza, se piden segmentos). La señal robusta de F314 es
   `segment_requests > 0`.
2. **Los segmentos del fixture fuerzan keyframes exactos cada 4s.** Sin eso,
   EXTINF (p. ej. 5.12s) excede TARGETDURATION y el `validate()` del backend
   provisto rechaza la media playlist → `parse_manifest` devuelve **500**
   (bug del código base: `media_playlist={}` rompe su response_model). Ojo:
   un candidato puede toparse con este mismo 500 usando manifests reales —
   no es culpa de su app; tenerlo en cuenta al corregir F308/F327.

## Datos de referencia de la prueba nueva

- Código base provisto: FastAPI + m3u8 + httpx, commit inicial `2e0ccbb`.
  Endpoints: `/validate_manifest`, `/parse_manifest`, `/filter_manifest`.
- Dataset Parte 2 (`new-technical-test/Backend/Manifests Parte 2/`):
  10 manifests, universo de IDs 1..300, 270 IDs por archivo, sin huecos
  globales. **Óptimo = 3 archivos** (p. ej. 5+8+9); greedy también logra 3.
- Manifest vivo de prueba: `https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8`.

## Smoke test v2

```bash
cd "$SCA_ROOT"
SCA_ROOT="$PWD" python3 - <<'EOF'
import sys, json; sys.path.insert(0, '.')
from sca.v2.reporter.templates import (
    CRITERIOS_BACKEND_V2, build_scores_payload, build_asana_text, build_slack_text)
scores = {f: 1 for f in CRITERIOS_BACKEND_V2}
p = build_scores_payload(scores, nivel=3, apellido='Test', nombre='User',
    aspectos=['x'], otras_notas='x', feedback='x', nivel_justif='x')
p = json.loads(json.dumps(p))
print(build_asana_text(p)[:200])
print(build_slack_text(p, source_url='s', asana_url='a'))

from sca.v2.reporter import templates_frontend as fe
scores = {f: 1 for f in fe.CRITERIOS_FRONTEND_V2}
p = fe.build_scores_payload(scores, nivel=3, apellido='Test', nombre='User',
    aspectos=['x'], otras_notas='x', feedback='x', nivel_justif='x')
print(fe.build_asana_title(p))
EOF
```

## Pendientes de v2

- **Calibrar umbrales de nivel** (Paso 8 BE / Paso 7 FE de los skills) con
  correcciones reales, como se hizo con v1. Primer dato (2026-07-16, ver
  `candidatos-v2/resultados/README.md`): los perfiles junior simulados
  (críticos OK, funcionalidad completa, entrega desprolija) dieron 15/26 (BE)
  y 13/29 (FE) → trainee. Propuestas en discusión: bajar umbral junior
  (BE ≥14, FE ≥13) o regla de piso funcional (críticos + funcionalidad
  completa → mínimo junior).
- ~~Habilitar frontend v2 en la Routine~~ — hecho (2026-07-16): flujo completo
  en `routine/v2/CORRECCION.md` §V2.2 con validador + fixture. Verificado
  contra los dos candidatos simulados (el validador discriminó bien: SS con
  4 charts y filtro OK; JR con 0 charts canvas/svg). Falta calibrar con
  candidatos reales.
- **Validators v2** (opcional): script que verifique la Parte 2 del candidato
  contra el óptimo calculado por fuerza bruta/ILP (`sca/v2/validators/`),
  y validación funcional de la Parte 1 con requests parametrizadas.
- **Guías detalladas por criterio** (`references/manual.md` de cada skill v2),
  a escribir cuando haya ejemplos reales de candidatos.
