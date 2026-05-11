---
name: sca-corrector-frontend
description: >
  Corrector automático de pruebas técnicas de **frontend** (React) de Qualabs.
  Úsalo cuando el usuario suba un ZIP/URL con una prueba de frontend, o cuando
  Claude detecte React (`package.json` con `"react"` en dependencies) en la
  prueba técnica. Equivalente al skill `sca-corrector` (backend) pero con
  checklist adaptado al template oficial de frontend (`Requerimientos/Template
  Frontend.xlsx`): 35 criterios, 6 secciones, 4 críticos.
  Triggers: "corregí esta prueba de frontend", "evaluá al candidato (React)",
  "es una prueba frontend", "completá el checklist frontend", "ranking nivel
  frontend", o cualquier corrección donde el repo del candidato use React.
---

# SCA Frontend — Corrector de Pruebas Técnicas (React)

Sos el SCA para pruebas de frontend. Tu trabajo es analizar la solución
React de un candidato y producir:

1. Un **checklist completo** con 0/1 por criterio (35 filas)
2. El **nivel sugerido** (no_suficiente / trainee / junior / semi_senior)
3. El **texto listo para Asana** con ✅/❌ por las 6 secciones

Lee `references/manual.md` para los criterios fila por fila y la calibración
de niveles. Lee `references/expected_part_a.md` para el ground truth de
Parte A. Lee `$SCA_ROOT/Prueba tecnica/Prueba técnica - Frontend.pdf` para
ver el **mock UX** que el candidato debe replicar (es el ground truth visual
para F113/F114).

> Si la prueba **no usa React**, este skill no aplica. Backend usa
> `sca-corrector`. Si es algo distinto (Vue, Svelte, plain HTML), avisar al
> usuario antes de seguir — la letra explícitamente pide React.

---

## Convenciones de paths

Mismas que en backend: la variable `$SCA_ROOT` apunta a la raíz del repo SCA.

```bash
# Cowork en Mac (default de este skill)
export SCA_ROOT="/Users/javieraramberri/Projects/SCA"

# Routine / Claude Code con el repo montado
# export SCA_ROOT="/workspace"
```

---

## Paso 1 — Obtener el código del candidato

**Si subió un ZIP:** `unzip <archivo> -d candidato/`

**Si dio una URL de GitHub/GitLab:** `git clone <url> candidato/`

**Si ya tenés acceso a la carpeta:** leé directo con Read.

Buscá: `package.json`, `src/`, README, archivos `.jsx`/`.tsx`/`.js`, archivos
de estilos (`.css`/`.scss`), config de routing/store si los hay.

---

## Paso 2 — Confirmar que es React

```bash
cd <carpeta_candidato>
cat package.json | grep -E '"react"|"react-dom"'
```

Si no hay React → **detené** y avisá al usuario. Este skill no cubre Vue,
Svelte ni HTML+JS plano.

Mirá también:
- ¿Usa Vite, CRA, Next.js, otro? (Define cómo levantar el dev server.)
- ¿Tiene `react-router-dom`? (Necesario para F112.)
- ¿Tiene `@reduxjs/toolkit` o `react-redux`? (Necesario para F128.)
- ¿Usa SCSS? (`.scss` en `src/` → necesario para F131.)

Anotalos — los vas a usar al scorear.

---

## Paso 3 — Instalar dependencias

```bash
cd <carpeta_candidato>

if [ -f package-lock.json ]; then
    npm ci --silent || npm install --silent
elif [ -f yarn.lock ]; then
    yarn install --silent
elif [ -f pnpm-lock.yaml ]; then
    pnpm install --silent
else
    npm install --silent
fi
```

Si la instalación falla → reportalo al usuario antes de seguir. Sin deps
instaladas, no podés levantar la app ni validar visualmente.

---

## Paso 4 — Validar Parte A

Detectá cómo entregó la Parte A:

**Caso 1 — script aparte** (ej. `parteA.js`, `scripts/buildIndex.js`):

```bash
node <ruta-script>  # o npm run <script-de-parteA>
```

Capturá el output (JSON) y validalo:

```python
import os, sys
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.validators.part_a import validate

result = validate(<output-string>)
print(result.summary())
```

**Caso 2 — calculada in-browser** (un `useEffect` o loader que invierte el
JSON dentro de la app): inspeccioná el código que arma el index y comparalo
mentalmente con `EXPECTED_OUTPUT` en `sca/validators/part_a.py`. La
verificación final ocurre en el Paso 5 cuando levantás la app y mirás los
usuarios que renderiza para cada provider.

Si Parte A no existe (datos hardcoded en el componente, sin lectura de
JSONs) → **F135 = 0** y nivel `no_suficiente`.

Ver `references/expected_part_a.md` para el detalle.

---

## Paso 5 — Levantar la app y tomar screenshots

Esta es la diferencia grande con backend. Para evaluar fidelidad mock
(F109-F114), navegación (F112) y responsive (F115), hay que ver la app
funcionando.

### 5.1 — Detectar el comando de dev

Mirá `package.json` → `scripts`:
- `"dev"` → Vite (default `http://localhost:5173`)
- `"start"` → CRA (default `http://localhost:3000`)
- `"dev"` con Next.js → `http://localhost:3000`

### 5.2 — Levantar el dev server en background

```bash
cd <carpeta_candidato>
nohup npm run dev > /tmp/sca-frontend-server.log 2>&1 &
SERVER_PID=$!
sleep 5  # esperar que arranque
curl -s http://localhost:5173 || curl -s http://localhost:3000 || echo "Server no responde"
```

Si no arranca, mirá `/tmp/sca-frontend-server.log` para diagnosticar.

### 5.3 — Tomar screenshots con Playwright

> **Pendiente de implementación**: el validador automatizado
> `sca/validators/part_b_frontend.py` (con Playwright) es la tarea #35,
> separada de este skill. Hasta entonces, hacelo así:

Si Playwright está disponible:

```python
from playwright.sync_api import sync_playwright

URL = "http://localhost:5173"  # ajustar según server detectado

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto(URL, wait_until='networkidle')
    page.screenshot(path='/tmp/sca-fe-1-initial.png', full_page=True)

    # Click en cada tab nivel 1 (auth_module / content_module)
    # y tomar screenshot
    for tab_text in ['Auth_module', 'Content_module']:
        try:
            page.get_by_text(tab_text, exact=False).first.click()
            page.wait_for_timeout(300)
            page.screenshot(path=f'/tmp/sca-fe-{tab_text}.png', full_page=True)
        except Exception as e:
            print(f"No pudo clickear {tab_text}: {e}")

    # Mobile viewport
    page.set_viewport_size({'width': 380, 'height': 800})
    page.screenshot(path='/tmp/sca-fe-mobile.png', full_page=True)

    browser.close()
```

Si Playwright no está instalado: `npm install -g playwright && npx
playwright install chromium`.

### 5.4 — Comparar contra el mock

Leé el PDF: `$SCA_ROOT/Prueba tecnica/Prueba técnica - Frontend.pdf`. Tiene
el mock UX en la página 2.

Mirando las screenshots de la app vs el mock, evaluá:

- F109 (selección visible): ¿el botón activo se ve distinto?
- F110 (headers): ¿dice "Number of users in module N:"?
- F111 (botones): ¿están Delete/Advice/Create/Submit con sus íconos?
- F113 (similitud módulo): layout general fiel.
- F114 (similitud botones): colores y forma cercanos.
- F115 (responsive): screenshot mobile no roto.

### 5.5 — Cerrar el dev server

```bash
kill $SERVER_PID 2>/dev/null
```

---

## Paso 6 — Análisis de calidad del código (vos mismo)

Lo mismo que en backend: como Claude, analizá directamente el código contra
cada criterio del checklist. Las guías detalladas están en
`references/manual.md`. Resumen de los puntos calientes:

### Críticos (si alguno = 0 → nivel `no_suficiente`)

- **F108 ❗** No hardcodea providers. `grep -rE 'authn\.provider_|authz\.provider_'
  src/` debería volver vacío en el código del candidato. Si encontrás
  cualquier string así → 0.
- **F121 ❗** Sin código duplicado. Si hay bloques de 10+ líneas repetidos en
  varios componentes → 0.
- **F132 ❗** Componentes funcionales o no funcionales (no mezcla). Buscá
  `class.*extends.*Component` y compará con la cantidad de funcionales con
  hooks. Si conviven los dos estilos sin razón → 0.
- **F135 ❗** Parte A correcta. Ver Paso 4.

### Específicos frontend (los que más se confunden)

- **F112 (ruteo de React)**: necesita `react-router-dom` o equivalente con
  URLs distintas por módulo. State local sin URLs → F112 = 0.
- **F128 (redux store)**: específicamente Redux (RTK o classic). Context
  API o Zustand **no cuentan**.
- **F131 (SCSS)**: tiene que haber archivos `.scss`. CSS-in-JS o `.css`
  plano → F131 = 0.
- **F132 (estilo coherente)**: la regla es "elegí uno". Funcional+hooks o
  class. Mezclar es F132 = 0.

### Sutilezas a tener en cuenta (calibrado contra correcciones reales)

- **F102 (versión)**: estricto — debe estar en doc humana, no solo
  `package.json`/`.nvmrc`.
- **F105 (parametriza)**: una constante centralizada cuenta. Hardcoded
  esparcido no.
- **F124 (error handling, bonus 😀)**: lo mismo que backend — `try/catch`
  que hace algo útil con el error.
- **F126 (componente Container)**: marcar bonus 😀 en `aspectos` cuando está
  bien hecho (ver Frontend 1).

---

## Paso 7 — Determinar nivel

Aplicá esta lógica en orden:

```
Si hay cualquier crítico fallado → no_suficiente (sin excepciones)
Si no:
  puntaje >= 28 Y los 4 críticos OK Y fidelidad mock alta Y Redux Y SCSS
    → semi_senior

  puntaje 18-27 Y los 4 críticos OK Y fidelidad mock razonable
    Y al menos 2 componentes genéricos creados
    → junior

  puntaje 12-17 Y los 4 críticos OK
    → trainee

  puntaje < 12 con anti-patterns claros (document.getElementById en React,
  hardcodes generalizados, no usa hooks)
    → trainee o no_suficiente según criterio
```

### Señales blandas

Aplican las mismas que en backend (ver SKILL backend Paso 7):

- Tono inadecuado en la documentación.
- Mezcla de idiomas en la documentación o en el código.
- Tiempo verbal narrativo en futuro.
- Inconsistencias estéticas sistemáticas.
- Desalineación entre la pretensión del README y lo entregado.

Pueden bajar un escalón aunque los criterios duros estén OK. Cuando uses una,
mencionalo explícitamente en `nivel_justif`.

### Justificación del nivel

Igual que backend: 2-3 oraciones (~50 palabras) que expliquen por qué cae
ahí y no en el contiguo.

Ejemplos calibrados con las muestras reales:

> Junior: cumple los 4 críticos, similitud visual alta con el mock, hooks
> bien usados, componentes genéricos para el contenedor (bonus). No llega a
> Semi Senior porque no usa Redux (F128) ni SCSS (F131) y le falta error
> handling. Border con Semi Senior si hubiera atendido el feedback.

> Trainee: cumple los 4 críticos y la app funciona, pero formato del código
> en React es inconsistente, mezcla idiomas en la documentación, los headers
> y botones no siguen los textos de la letra (F110/F111). No baja a No
> suficiente porque los 4 críticos están en ✅ y la similitud visual de los
> botones es razonable.

> No suficiente: F108 (hardcodea providers), F107 (hardcodea cantidad) y
> F121 (código duplicado generalizado). Usa `document.getElementById` en
> React, lo que es un anti-pattern. La página no se parece al mock, no tiene
> íconos en los botones, los users están separados por algo que no debería.

---

## Paso 8 — Generar texto para Asana

El formato está centralizado en `sca/reporter/templates_frontend.py` —
**fuente única de verdad para frontend**. Si cambia el checklist o las
secciones, se toca ese archivo.

```python
import os, sys, json
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.reporter.templates_frontend import (
    build_scores_payload, build_asana_text, build_asana_title,
)

scores = {
    # 35 criterios scoreables + fila 140 con el nivel (0-3)
    101: <1|0>, 102: <1|0>, 103: <1|0>,
    104: <1|0>, 105: <1|0>, 106: <1|0>, 107: <1|0>, 108: <1|0>,
    109: <1|0>, 110: <1|0>, 111: <1|0>, 112: <1|0>, 113: <1|0>, 114: <1|0>, 115: <1|0>,
    116: <1|0>, 117: <1|0>, 118: <1|0>, 119: <1|0>, 120: <1|0>,
    121: <1|0>, 122: <1|0>, 123: <1|0>, 124: <1|0>,
    125: <1|0>, 126: <1|0>, 127: <1|0>, 128: <1|0>, 129: <1|0>, 130: <1|0>,
    131: <1|0>, 132: <1|0>, 133: <1|0>, 134: <1|0>,
    135: <1|0>,
    140: <0|1|2|3>,
}

payload = build_scores_payload(
    scores,
    apellido="<apellido>",
    nombre="<nombre>",
    aspectos=["<aspecto 1>", "<aspecto 2>"],
    otras_notas="<notas de corrección>",
    feedback="<feedback para el candidato>",
    nivel_justif="<2-3 oraciones explicando por qué este nivel>",
)

print(build_asana_title(payload))   # "SCA — <Apellido>, <Nombre> (Frontend)"
print(build_asana_text(payload))    # bloque completo con 6 secciones
```

### Las cuatro secciones narrativas son OBLIGATORIAS

Misma regla que backend: `aspectos`, `otras_notas`, `feedback` y
`nivel_justif` deben tener contenido sustantivo. `build_scores_payload` lanza
`ValueError` si alguno está en blanco. Llená los cuatro antes de invocar.

Guía mínima por sección (igual que backend):

- **`aspectos`**: ≥ 2 ítems específicos del repo. Ejemplos: `"Generaliza
  los headers"`, `"Usa document.getElementById en React"`, `"Bonus: componente
  Container bien implementado"`.
- **`otras_notas`**: una o dos oraciones con datos de corrección que el
  humano usaría para validar.
- **`feedback`**: el mensaje **dirigido al candidato**, en segunda persona,
  con bloques *Lo que se destaca* y *Para mejorar*. Mínimo 5-6 líneas.
- **`nivel_justif`**: ver Paso 7.

---

## Paso 9 — Output final

Entregá al usuario:

1. El **texto para Asana** en el chat (fácil de copiar).
2. Un **resumen breve** del nivel y los puntos más importantes.
3. Si hay críticos fallados, destacalos al principio del resumen.
4. Si tomaste screenshots, compartí los paths/links — son útiles para que el
   humano que valida la corrección las pueda ver sin tener que levantar la
   app.

Persistí en `$SCA_WORK/<task_gid>/` (en la Routine) o `sca-corrector-frontend/candidato/`
(en local):

- `scores.json` — payload completo
- `texto_asana.txt` — output renderizado
- `titulo_asana.txt` — el título
- `screenshots/` — capturas tomadas en Paso 5

### Subir screenshots a Asana (solo en la Routine)

El conector MCP de Asana **no soporta** subir attachments. Para que las
screenshots aparezcan como archivos adjuntos en la subtask de corrección,
usá `sca.asana.attachments.upload_attachments` que postea directo al
endpoint REST con un PAT seteado como `ASANA_PAT`:

```python
import os, sys
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.asana.attachments import upload_attachments

pat = os.environ.get('ASANA_PAT')
if pat and screenshot_paths:
    result = upload_attachments(subtask_gid, screenshot_paths, pat)
    print(result.summary())  # ✅ por cada subida + ❌ por cada fallo
```

Es **no crítico**: si falta `ASANA_PAT` o el upload falla, el feedback
ya está en el texto de la subtask. El Paso 11.4 del PROMPT de la Routine
hace esto automáticamente. En modo manual local, presentá los paths como
`computer://` links — el humano las abre directo desde el chat.
