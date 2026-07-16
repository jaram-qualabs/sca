# SCA v2 — Sub-flujo de corrección (prueba nueva HLS)

> La Routine lee este archivo SOLO cuando el Paso 5.0 de `routine/PROMPT.md`
> detectó `PRUEBA_VERSION=v2` (tag `sca-v2` o sniff del zip). Es autocontenido:
> criterios, árbol de nivel y snippets están acá para no cargar nada más.
> Reemplaza los Pasos 5-12 del flujo v1; el manejo de errores per-task
> (comentario + continuar), el cleanup (Paso 13) y el resumen (Paso 14) son
> los mismos del PROMPT principal.

## V2.1 — Detectar tipo (backend / frontend)

```bash
C="$SCA_WORK/$TASK_GID/candidato"
if grep -qs '"react"' $(find "$C" -maxdepth 3 -name package.json -not -path "*/node_modules/*" 2>/dev/null) 2>/dev/null; then
  export TIPO_V2=frontend
else
  export TIPO_V2=backend
fi
echo "Tipo v2: $TIPO_V2"
```

## V2.2 — Frontend v2: corrección completa

### V2.2.a — Setup (una vez por batch, solo si hay tasks FE v2)

```bash
# Playwright + chromium (mismo stack que FE v1)
python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null \
  || pip install --break-system-packages playwright --quiet
python3 -m playwright install chromium --with-deps 2>&1 | tail -1

# Backend FastAPI provisto (la SPA del candidato lo consume)
cd "$SCA_ROOT/new-technical-test/Frontend/Backend"
pip install -r requirements.txt --break-system-packages --quiet
python3 -m uvicorn src.app:app --port 8000 &>/tmp/sca_v2_backend.log &
for i in $(seq 1 15); do curl -s -o /dev/null http://127.0.0.1:8000/docs && break; sleep 1; done

# Fixture HLS local (VP9+Opus). ⚠️ NO usar el stream de mux para el chequeo
# del player: el chromium de Playwright no decodifica h264/aac y daría falso
# negativo siempre. El fixture local reproduce de verdad.
python3 -m sca.v2.validators.fixture --dir /tmp/sca_hls_fixture --port 9000 &
sleep 2
```

### V2.2.b — Por task: instalar, validar, screenshots

```bash
cd "$SCA_WORK/$TASK_GID/candidato" && git log --oneline | head -10   # F304-F306
npm install --no-audit --no-fund
```

```python
import os, sys
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.v2.validators.frontend import validate

work = f"{os.environ['SCA_WORK']}/{os.environ['TASK_GID']}"
r = validate(
    f"{work}/candidato",
    manifest_url='http://127.0.0.1:9000/master.m3u8',
    output_dir=f"{work}/screenshots",
)
print(r.summary())
```

**Mapeo señales → criterios** (el validador junta evidencia; el score lo
decidís vos mirando también las screenshots y el código):

| Señal | Criterio | Nota |
|---|---|---|
| `validation_shown` + screenshot 02 | F307 ❗ | Verificá en la screenshot que sea el resultado de validación, no un error genérico de la app |
| `charts_count ≥ 3` + screenshot 02 | F309; F310 se juzga mirando la screenshot | Barras CSS no cuentan como canvas/svg — mirá la screenshot antes de dar 0 |
| `sliders_count ≥ 2` | F311 | 1 solo slider o inputs de texto = 0 |
| `filter_applied` + screenshot 03 | F312 ❗ | |
| `segment_requests > 0` | F314 ❗ | `video_ready/playing` son bonus de evidencia |
| `media_selectors_count` + código | F315/F316 | Confirmar en el código que los selects cambian `currentLevel` / `audioTrack` |
| screenshots 01-04 vs Figma | F317, F319 | El Figma está linkeado en el PDF de la letra |
| screenshot 05 (mobile) | F318 | |

F308 (errores claros) y F313 (estados de carga): evaluar por código
(try/catch + render del error) y, si hace falta, repetir el validate con
`manifest_url='http://127.0.0.1:9000/no-existe.m3u8'`.

### V2.2.c — Criterios FE (29) y árbol de nivel

**Documentación:** F301 cómo correr · F302 versiones/deps · F303 decisiones.
**Git:** F304 `.git` con commits del candidato · F305 incrementales (≥3) ·
F306 mensajes descriptivos.
**Dashboard:** F307 ❗ valida en tiempo real · F308 errores claros · F309
gráficos (resolución, bandwidth, codecs, duración) · F310 gráficos acordes.
**Filtro:** F311 sliders · F312 ❗ obtiene el manifest filtrado · F313
loading/errores/rango vacío.
**Player:** F314 ❗ reproduce variante del parse_manifest · F315 cambio de
resolución · F316 cambio de pista de audio.
**UI:** F317 similitud Figma · F318 responsive · F319 consistencia visual.
**Calidad:** F320 componentes chicos/reutilizables · F321 separa lógica de
presentación (hooks/servicios) · F322 manejo de estado · F323 naming y
convenciones · F324 solo funcionales+hooks · F325 ❗ sin código duplicado ·
F326 estilos organizados · F327 error handling con la API · F328 comentarios
adecuados · F329 tests (bonus).

**Nivel (determinístico, en orden):**
1. Algún ❗ (F307/F312/F314/F325) = 0 → `no_suficiente` (0).
2. Puntaje ≥ 24/29 **y** F307-F316 todos 1 **y** F304-F306 = 1 → `semi_senior` (3).
3. Puntaje ≥ 18/29 → `junior` (2).
4. Puntaje ≥ 12/29 → `trainee` (1).
5. Menos → `no_suficiente` (0).

### V2.2.d — Payload, subtask, screenshots y Slack

```python
import os, sys, json
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.v2.reporter.templates_frontend import (
    build_scores_payload, build_asana_text, build_slack_text)

scores = {f: <0|1> for f in range(301, 330)}  # completar los 29
payload = build_scores_payload(
    scores, nivel=<0-3>,
    apellido=os.environ['CANDIDATE_APELLIDO'], nombre=os.environ['CANDIDATE_NOMBRE'],
    aspectos=["<...>"], otras_notas="<incluir el summary() del validador>",
    feedback="<...>", nivel_justif="<regla aplicada + 1-2 oraciones>",
)
work = f"{os.environ['SCA_WORK']}/{os.environ['TASK_GID']}"
json.dump(payload, open(f"{work}/scores.json", 'w'), ensure_ascii=False, indent=2)
texto = build_asana_text(payload)
# Subtask: name = "Comentarios y corrección SCA" (marcador), notes = texto.
# Screenshots: subirlas a la subtask con el MISMO snippet del Paso 11.4 del
#   PROMPT principal (sca.asana.attachments + ASANA_PAT) — los PNG están en
#   $SCA_WORK/<task_gid>/screenshots/.
mensaje = build_slack_text(payload,
    source_url=os.environ['TASK_PERMALINK'], asana_url='<subtask_url>')
```

Al terminar el batch FE v2: matar uvicorn y el fixture server. Resumen del
Paso 14 con `[v2-FE]`.

## V2.3 — Backend v2: preparar y levantar el servicio del candidato

```bash
# Ubicar el servicio (donde vive src/hls_service.py) y el .git
SVC=$(dirname "$(dirname "$(find "$C" -name hls_service.py -not -path "*/node_modules/*" | head -1)")")
cd "$SVC"
git log --oneline | head -15            # → F204-F206 (ver criterios abajo)
pip install -r requirements.txt --break-system-packages --quiet

# Fixture local para probar filtros (no depender de red externa)
mkdir -p "$SCA_WORK/$TASK_GID/fixture"
cat > "$SCA_WORK/$TASK_GID/fixture/master.m3u8" <<'EOF'
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="Es",LANGUAGE="es",DEFAULT=YES,URI="a.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.42c01e,mp4a.40.2",AUDIO="aud"
360p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480,CODECS="avc1.4d401f,mp4a.40.2",AUDIO="aud"
480p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720,CODECS="avc1.64001f,mp4a.40.2",AUDIO="aud"
720p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",AUDIO="aud"
1080p.m3u8
EOF
python3 -m http.server 9000 --directory "$SCA_WORK/$TASK_GID/fixture" &>/dev/null &
python3 -m uvicorn src.app:app --port 8000 &>"$SCA_WORK/$TASK_GID/uvicorn.log" & sleep 4
```

## V2.4 — Batería funcional Parte 1 (F207-F211)

```bash
M="http://127.0.0.1:9000/master.m3u8"; B="http://127.0.0.1:8000/filter_manifest?manifest_url=$M"
echo "T1 resolución:"; curl -s "$B&min_resolution=480&max_resolution=1080" | grep -c RESOLUTION   # espera 3
echo "T2 bitrate:";    curl -s "$B&min_bitrate=1000000&max_bitrate=3000000" | grep -c RESOLUTION  # espera 2 (480p,720p) → F207
echo "T3 combinado:";  curl -s "$B&min_resolution=480&max_resolution=1080&min_bitrate=2000000&max_bitrate=6000000" | grep -c RESOLUTION  # espera 2 → F209
echo "T4 min>max:";    curl -s -o /dev/null -w "%{http_code}" "$B&min_bitrate=5000000&max_bitrate=1000000"; echo  # 422 → F210 ok; 404/500/200 → F210=0
echo "T5 sin match:";  curl -s -o /dev/null -w "%{http_code}" "$B&min_bitrate=90000000&max_bitrate=99000000"; echo  # espera 404
echo "T6 swagger:";    curl -s http://127.0.0.1:8000/openapi.json | grep -o '"min_bitrate"[^}]*"description"' | head -1  # con descripción → F211 (junto con README)
```

Verificá **el contenido** del m3u8 devuelto en T2 (que sean las variantes
correctas, no solo el count). Si el README documenta otro shape de params
(p. ej. otro nombre de query), adaptá la batería a lo que el candidato
documentó — lo que se evalúa es que funcione, no el nombre exacto.

## V2.5 — Diseño extensible (F212-F214)

Mirá **el diff contra el commit inicial**, no todo el código:
`git log --oneline | tail -1` (el inicial provisto) y
`git diff <inicial>..HEAD -- '*.py' | head -200`.
- F212 ❗: ¿agregar un criterio nuevo requiere modificar la lógica existente
  (if-chain en `filter()`) → 0, o hay abstracción (predicados/estrategias/
  registry/lista de checks) → 1?
- F213: rutas en `app.py`, lógica en el service (como el código base).
- F214: ¿copió-pegó el bloque de resolución para bitrate? → 0.

## V2.6 — Parte 2 (F222-F226)

```bash
# Localizar el módulo de Parte 2 (README del candidato) y correrlo contra el dataset oficial
DATASET="$SCA_ROOT/new-technical-test/Backend/Manifests Parte 2"
cd "$SVC" && <comando del README> "$DATASET" > "$SCA_WORK/$TASK_GID/part2_out.json"
python3 - <<'PY'
import json, os, re, glob
out = json.load(open(f"{os.environ['SCA_WORK']}/{os.environ['TASK_GID']}/part2_out.json"))
DS = os.path.join(os.environ['SCA_ROOT'], 'new-technical-test', 'Backend', 'Manifests Parte 2')
ids = lambda p: {int(m) for m in re.findall(r'_(\d+)\.ts', open(p).read())}
uni = set().union(*(ids(p) for p in glob.glob(f'{DS}/*.m3u8')))
cov = set().union(*(ids(os.path.join(DS, n)) for n in out))
print('F222 cobertura total:', cov == uni)          # ❗ crítico
print('F223 óptimo (== 3 archivos):', len(out) == 3)
print('F224 formato JSON lista de nombres: OK si llegaste acá')
PY
# F226: caso borde — carpeta vacía debe avisar/fallar limpio, no imprimir [] ni crashear feo
mkdir -p /tmp/v2vacio && cd "$SVC" && <comando> /tmp/v2vacio; echo "exit=$?"
```

F225 (no hardcodea): `grep` rápido en el módulo por listas de IDs o
`manifest_1`..`manifest_10` literales → si hay, 0.

## V2.7 — Criterios (26) y árbol de nivel

**Documentación:** F201 explica cómo correr (ambas partes) · F202 versiones/
deps · F203 decisiones de diseño (en especial el filtrado extensible).
**Git:** F204 `.git` presente con commits del candidato · F205 commits
incrementales (≥3 con progresión; 1-2 gruesos = 0) · F206 mensajes descriptivos.
**API (Parte 1):** F207 ❗ bitrate funciona · F208 resolución sigue andando ·
F209 combinables · F210 validación y errores HTTP coherentes · F211 doc de API
actualizada (Swagger y/o README).
**Diseño:** F212 ❗ extensible sin tocar lo existente · F213 capas · F214 sin
duplicación al extender.
**Calidad:** F215 nomenclatura · F216 comentarios adecuados · F217 convenciones
del código base (async/typing/pydantic) · F218 funciones con responsabilidad
clara · F219 formato · F220 error handling (bonus) · F221 tests (bonus).
**Parte 2:** F222 ❗ cobertura total · F223 óptimo (3 archivos) · F224 salida
JSON de la letra · F225 parsea .m3u8 sin hardcodear · F226 casos borde.

**Nivel (determinístico, en orden):**
1. Algún ❗ (F207/F212/F222) = 0 → `no_suficiente` (0).
2. Puntaje ≥ 21/26 **y** F212-F214 = 1 **y** F223 = 1 **y** F204-F206 = 1 → `semi_senior` (3).
3. Puntaje ≥ 16/26 → `junior` (2).
4. Puntaje ≥ 11/26 → `trainee` (1).
5. Menos → `no_suficiente` (0).

Citá la regla aplicada en `nivel_justif`. (Umbrales en calibración — ver
`sca/v2/PLAN.md`.)

## V2.8 — Payload, subtask y Slack (templates v2)

```python
import os, sys, json
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.v2.reporter.templates import (
    build_scores_payload, build_asana_text, build_slack_text)

work = f"{os.environ['SCA_WORK']}/{os.environ['TASK_GID']}"
scores = {f: <0|1> for f in range(201, 227)}  # completar los 26
payload = build_scores_payload(
    scores, nivel=<0-3>,   # ojo: nivel es kwarg, NO una fila de scores
    apellido=os.environ['CANDIDATE_APELLIDO'], nombre=os.environ['CANDIDATE_NOMBRE'],
    aspectos=["<...>"], otras_notas="<...>", feedback="<...>",
    nivel_justif="<regla aplicada + 1-2 oraciones>",
)
json.dump(payload, open(f"{work}/scores.json", 'w'), ensure_ascii=False, indent=2)
texto = build_asana_text(payload)
# Subtask (mismo marcador de idempotencia que v1):
#   name  = "Comentarios y corrección SCA"
#   notes = texto     · parent = task_gid
# Slack (no crítico) — la firma v2 difiere de v1:
mensaje = build_slack_text(payload,
    source_url=os.environ['TASK_PERMALINK'], asana_url='<subtask_url>')
```

Después: matar uvicorn/http.server (`kill %1 %2` o por PID), Paso 13
(cleanup) y sumar al resumen del Paso 14 como `[v2-BE]`.
