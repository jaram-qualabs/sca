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

## V2.2 — Frontend v2: aún no automatizado (skip con marca)

El corrector FE v2 (`sca-corrector-frontend-v2`) está en beta sin calibrar.
Hasta habilitarlo, crear la subtask marcadora (misma idempotencia que v1) y
seguir con la próxima task — **no** es un error per-task:

- `name`: `"Comentarios y corrección SCA"`
- `notes`: `"Prueba v2 de FRONTEND detectada. La corrección automática v2-FE
  todavía no está habilitada en la Routine — corregir manualmente con el
  skill sca-corrector-frontend-v2 (Cowork/Claude Code) y pegar el resultado
  acá."`
- Postear en Slack (no crítico): `⚠️ *SCA v2 — FE detectado, corrección manual
  pendiente* — <permalink de la task>`.

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
