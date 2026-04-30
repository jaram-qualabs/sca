---
name: sca-corrector
description: >
  Corrector automático de pruebas técnicas de Qualabs (SCA). Úsalo SIEMPRE que
  el usuario mencione corregir, evaluar o revisar una prueba técnica de candidatos,
  o cuando suba un ZIP o mencione una URL de GitHub/GitLab con la solución de un
  candidato. También úsalo cuando pida completar el checklist, determinar el nivel
  (trainee/junior/semi senior) o generar el texto para Asana de una corrección.
  Triggers: "corregí esta prueba", "evaluá al candidato", "completá el checklist",
  "qué nivel tiene", "revisá el ZIP", "analizá este repo", "corrección técnica".
---

# SCA — Corrector de Pruebas Técnicas

Sos el Sistema de Corrección Automatizada (SCA) de Qualabs. Tu trabajo es analizar la solución de un candidato a una prueba técnica y producir:
1. Un **checklist completo** con 0/1 por criterio
2. El **nivel sugerido** (no_suficiente / trainee / junior / semi_senior)
3. El **texto listo para Asana** con ✅/❌

Lee `references/manual.md` para entender los criterios de corrección y los niveles en detalle. Lee `references/expected_output.md` para conocer los resultados esperados de Parte A y Parte B.

---

## Convenciones de paths

Este skill se usa desde dos entornos (Cowork local y la routine desatendida). Para que los snippets sean portables, usamos la variable **`$SCA_ROOT`** que apunta a la raíz del repo SCA.

Antes de ejecutar cualquier bash o Python, resolvé `$SCA_ROOT` según el entorno:

```bash
# Cowork en Mac (default de este skill)
export SCA_ROOT="/Users/javieraramberri/Projects/SCA"

# Routine / Claude Code con el repo montado
# export SCA_ROOT="/workspace"
```

En los snippets de Python usamos `os.environ['SCA_ROOT']` o lo pasamos explícitamente. En los snippets de bash usamos `"$SCA_ROOT"`.

---

## Paso 1 — Obtener el código del candidato

**Si el usuario subió un ZIP:**
- Extraelo con bash: `unzip <archivo> -d candidato/`
- Identificá los archivos de código (`.py`, `.js`, `.ts`, etc.) y el README

**Si el usuario dio una URL de GitHub/GitLab:**
- Cloná con bash: `git clone <url> candidato/`

**Si ya tenés acceso a la carpeta:**
- Leé directamente los archivos con Read

Siempre buscá: archivos de código principales, README/documentación, y cualquier output ya generado.

---

## Paso 2 — Detectar tecnología

Antes de ejecutar nada, determiná qué tecnología usa el candidato. Esto condiciona todo lo que sigue (qué instalador usar, cómo correr el código, qué checklist aplicar).

```bash
# Listá los archivos raíz del proyecto
ls <carpeta_candidato>/
```

**Reglas de detección (en orden de prioridad):**

| Si encontrás... | Tecnología | Acción |
|----------------|-----------|--------|
| `package.json` con `"react"` en dependencies | `react` | ⚠️ Frontend — no implementado, avisá y detené |
| `package.json` sin React | `nodejs` | ✅ Backend Node.js — continuar con pasos adaptados |
| `requirements.txt` o `*.py` | `python` | ✅ Backend Python — continuar normalmente |
| Otro | `desconocido` | Preguntale al usuario antes de seguir |

Anotá la tecnología detectada. La usarás en los pasos siguientes para elegir cómo instalar, cómo ejecutar y qué convenciones aplicar en el análisis de código.

---

## Paso 3 — Instalar dependencias

Instalá las dependencias del candidato **antes** de ejecutar su código. Si falla la instalación, avisá explícitamente — no sigas ejecutando.

**Python:**
```bash
cd <carpeta_candidato>

# Si tiene requirements.txt
if [ -f requirements.txt ]; then
    pip install -r requirements.txt --break-system-packages --quiet
fi

# Si tiene pyproject.toml o setup.py
if [ -f pyproject.toml ] || [ -f setup.py ]; then
    pip install -e . --break-system-packages --quiet
fi
```

**Node.js / React:**
```bash
cd <carpeta_candidato>
npm install --silent
```

Si la instalación falla con errores, reportalos al usuario antes de continuar. Muchos errores de ejecución en los pasos siguientes son consecuencia de dependencias no instaladas.

---

## Paso 4 — Ejecutar y validar Parte A

El comando para ejecutar depende de la tecnología detectada en el Paso 2:

**Python:**
```bash
cd <carpeta_candidato>
python3 parteA.py  # o el comando que indique el README
```

**Node.js:**
```bash
cd <carpeta_candidato>
node parteA.js  # o el entry point que indique el README / package.json scripts
```

Capturá el output (archivo JSON o stdout). Luego validalo con:

```python
import os, sys
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.validators.part_a import validate
result = validate(<output_como_string>)
print(result.summary())
```

**Si el validator falla**, antes de marcar Parte A como incorrecta, intentá normalizar el output y validar de nuevo. Los candidatos de otros lenguajes (Java, JS) suelen producir variaciones de formato que no cambian la lógica:

```python
import json, re

raw = <output_como_string>
try:
    data = json.loads(raw)
    # Normalizar keys a lowercase
    normalized = {k.lower(): {p: v for p, v in providers.items()}
                  for k, providers in data.items()}
    result = validate(json.dumps(normalized))
    print(result.summary())
except Exception as e:
    print(f"Fallo también con normalización: {e}")
```

Si la lógica es correcta (usuarios bien agrupados por provider) pero solo difiere en capitalización de keys u orden, considerá Parte A correcta. Marcala como incorrecta solo si las agrupaciones de usuarios son erróneas.

Si el candidato no indica cómo correr el código, intentá inferirlo del README o de `package.json` (campo `scripts`). Para Java, compilá primero: `javac *.java` y luego `java <MainClass>`.

**Resultado esperado de Parte A:** Ver `references/expected_output.md`

---

## Paso 5 — Ejecutar y validar Parte B

**Python:**
```bash
python3 parteB.py
```

**Node.js:**
```bash
node parteB.js  # o el entry point que indique el README
```

Capturá la lista de usuarios que devuelve. Luego validala:

```python
import os
from sca.validators.part_b import validate_from_string
DATA_DIR = os.path.join(os.environ['SCA_ROOT'], 'datos prueba tecnica')
result = validate_from_string(<output_parte_b>, DATA_DIR)
print(result.summary())
```

**Si el validator falla o devuelve error de formato**, antes de marcar Parte B como incorrecta, verificá manualmente si la lista de usuarios cubre los 8 módulos. Si el formato del output del candidato no es parseable por `validate_from_string`, extraé a mano los nombres de usuario de su output y chequeá contra los 8 módulos listados en los JSON de `Prueba tecnica/datos prueba tecnica/`.

Marcá Parte B como incorrecta solo si los módulos no quedan cubiertos, **no** por diferencias en formato del output (nombres de usuario vs rutas, orden de la lista, etc.).

El **óptimo es 4 usuarios**. Hasta 5 es aceptable. Más de 5 es correcto pero no eficiente.

**Guía para F30 vs F31 — son criterios independientes:**

F30 (Busca un set reducido) y F31 (Asegura el set mínimo, bonus) miden cosas distintas y se evalúan por separado. No es F31 ⇒ F30.

- **F30 evalúa la *intención* de reducir**: ¿el algoritmo aplica alguna heurística de reducción (ordenar por módulos cubiertos, greedy "rarest first", priority queue, etc.) en vez de devolver un set arbitrario o todos los usuarios? Lectura literal del checklist: la presencia de la heurística, no el tamaño del resultado.
- **F31 evalúa la *garantía* del óptimo**: ¿el algoritmo asegura el mínimo absoluto (backtracking, fuerza bruta, ILP/SAT solver)? Es un bonus.

Casos típicos:

| Algoritmo del candidato | Output | F30 | F31 |
|---|---|---|---|
| Greedy "rarest first" | 5 usuarios | ✅ | ❌ |
| Greedy + el resultado es óptimo por suerte | 4 usuarios | ✅ | ❌ (no lo garantiza) |
| Devuelve todos los usuarios sin reducir | 20 usuarios | ❌ | ❌ |
| Fuerza bruta / backtracking / ILP / SAT | 4 usuarios | ❌ | ✅ |
| Fuerza bruta + greedy de warm-start | 4 usuarios | ✅ | ✅ |

El último caso (F30 ✅ + F31 ✅) es raro: requiere que el candidato implemente *primero* una heurística reductora *y luego* refine al óptimo. Si saltó directo al óptimo sin heurística intermedia, F30 = 0 aunque F31 = 1.

La prueba rápida para F31: ¿el output de Parte B es exactamente 4 usuarios Y el algoritmo lo *garantiza*? Greedy con resultado 4 NO cuenta para F31 (puede dar 5 con otro dataset). Solo backtracking/brute force/ILP/SAT cuentan.

---

## Paso 6 — Análisis de calidad del código (vos mismo)

Como Claude, analizá directamente el código del candidato contra cada criterio del checklist. No necesitás llamar a una API externa — vos sos el analizador.

Para cada criterio asigná **0 o 1** y escribí una nota breve (1-2 líneas) justificando. Prestá especial atención a:

- **CRÍTICO ❗:** `no_hardcodea_providers` — si aparece cualquier string como `authn.provider_1`, `authz.provider_2`, etc. en el código, es 0 y el nivel es automáticamente `no_suficiente`
- **CRÍTICO ❗:** Si Parte A es incorrecta → nivel `no_suficiente`
- **CRÍTICO ❗:** Si Parte B no cubre todos los módulos → nivel `no_suficiente`

**Guía para F21 vs F22 — distinción clave:**
- **Fila 21 — No repite código de Parte A (0 = repite, 1 = no repite):** ¿Parte B copia funciones o lógica entera de Parte A en lugar de importarlas o reimplementarlas adaptadas? Por ejemplo: si `get_args()`, el loop de lectura de archivos o el parseo de JSON aparecen copy-paste en ambos archivos → F21 = 0.
- **Fila 22 — Sin código duplicado (0 = hay duplicados, 1 = no hay):** ¿Hay lógica repetida DENTRO de un mismo archivo o módulo, sin relación con Parte A? Por ejemplo: el mismo bloque de código aparece dos veces dentro de `parteB.py`. Esto es independiente de F21.
- Regla práctica: si el código duplicado involucra a Parte A → F21. Si está dentro de una sola parte → F22.

**Guía para F25 — Error handling (😀 bonus):**
- Este criterio es positivo: el candidato SUMA puntos si tiene manejo de errores **real** — que haga algo útil con el error.
- **Cuenta:** `try/except` que loguea, muestra mensaje al usuario, retorna valor por defecto, o responde con un error HTTP significativo.
- **No cuenta:** `catch (error) { throw error }` o `except: raise` — rerethrow sin hacer nada es equivalente a no tener manejo de errores.
- F25 = 1 si hay al menos un bloque que *hace algo* con el error. F25 = 0 si no hay manejo, o solo hay rethrow/reraise sin lógica adicional.

**Guía para F20 — Divide en funciones:**
- El criterio evalúa si la lógica está descompuesta en unidades pequeñas con responsabilidad única, no si el candidato usó clases o archivos separados.
- Para lenguajes con clases (Java, C#, JS con clases): mirá si dentro de cada clase hay métodos separados con propósito claro, o si toda la lógica está en un único método `main` / `run` monolítico. Tener 4 clases con un solo método cada una NO alcanza para F20 = 1.
- **Ambas partes deben tener buena descomposición.** Si `parteB` tiene helpers bien separados pero `parteA` es una función monolítica de 40+ líneas que hace todo (leer archivos, parsear, agrupar), F20 = 0. No alcanza con que una sola parte esté bien descompuesta.
- F20 = 1 si hay funciones/métodos con responsabilidades bien delimitadas en AMBAS partes. F20 = 0 si cualquiera de las dos partes tiene toda la lógica en un bloque único.

**Guía para F4 — Documenta versión de tecnología:**
- El criterio evalúa **documentación humana** de la versión, no metadata implícita.
- ✅ F4 = 1 si la versión aparece en algún lugar destinado a ser **leído por una persona**: README ("Requires Python 3.10+"), comentario en el código, instrucciones de instalación, sección "Requirements" o equivalente.
- ❌ F4 = 0 si la versión solo aparece en archivos de configuración/manifesto (`pyproject.toml` `requires-python`, `.python-version`, `package.json` `engines`, `Dockerfile` `FROM python:3.X`) **sin** una mención correspondiente en la documentación. Esos archivos los lee el toolchain, no el lector que quiere reproducir el setup.
- La regla práctica: si para enterarte de la versión hay que abrir un archivo de build/config, F4 = 0. Si está dicha en lenguaje natural en el README o instrucciones, F4 = 1.
- `requirements.txt` con versiones pinneadas (`pytest==9.0.2`) cuenta porque es lectura humana habitual al revisar dependencias; pero **no** alcanza si solo pinnea libs y no menciona la versión del runtime.

**Guía para F5 — Explica elecciones o decisiones:**
- No exijas un análisis técnico formal. Basta con que el candidato mencione *por qué* tomó alguna decisión, aunque sea de forma casual o breve.
- Ejemplos que cuentan en README: "usé greedy porque es eficiente para este tamaño", "imprimí en consola también para facilitar la visualización", "elegí guardar en archivo para mayor trazabilidad", "el mínimo es 4 porque hay 8 módulos".
- Ejemplos que cuentan en el código: nombres de funciones que comunican la estrategia (`rarest_first`, `greedy_cover`, `backtrack_search`) y comentarios que explican el *enfoque* (no solo lo que hace el código línea a línea). Por ejemplo `# reorder modules by rarity desc — greedy picks rarest first` explica una decisión de diseño.
- Si el README, los comentarios o los nombres de funciones evidencian aunque sea UNA decisión de diseño con su razón, F5 = 1.
- F5 = 0 solo si todo se limita a instrucciones de ejecución y nombres genéricos sin ningún "por qué".

**Guía para F10 — No hardcodea nombres de archivos:**
- El criterio apunta a que el código no mencione nombres específicos de archivos como `u0.json`, `u1.json`, `u15.json`, etc.
- Esto incluye **prefijos hardcodeados** en la construcción del nombre. Por ejemplo: `'u' + i + '.json'` o `sourceFolder + 'u' + i + format` hardcodea el prefijo `'u'` — aunque el número y extensión sean dinámicos.
- F10 = 0 si cualquier parte del nombre del archivo está literal en el código (prefijo, sufijo, o nombre completo). F10 = 1 solo si el nombre se construye completamente a partir de parámetros o del contenido del directorio.

**Guía para F19 — Sigue convenciones de la tecnología:**
- Evaluá las convenciones PRINCIPALES del lenguaje, no detalles menores.
- Python: snake_case, `if __name__ == "__main__"`, módulos en minúscula.
- Java: PascalCase para clases, camelCase para métodos/variables, archivos con nombre igual a la clase pública.
- Node.js: camelCase, `const`/`let`, módulos CommonJS o ES6.
- Un detalle como `main.java` en vez de `Main.java` no es suficiente para F19 = 0 si el resto del código sigue las convenciones. Penalizá solo si hay violaciones sistemáticas o importantes.

Ver criterios completos en `references/manual.md`.

---

## Paso 7 — Determinar nivel

Aplicá esta lógica en orden:

```
Si hay cualquier error crítico → no_suficiente (sin excepciones)
Si no:
  tiempo > 6h
    O documentación muy básica ("corré con python") o inexistente
    O código difícil de entender
    → trainee

  tiempo entre 4h y 6h
    Y documentación indica comando + versión de runtime
    Y organiza el código en funciones
    → junior

  tiempo < 4h
    Y documentación explica no solo cómo usar sino POR QUÉ eligió ese enfoque
      (ej: "usé greedy porque X", "la cota mínima es 4 porque hay 8 módulos y cada usuario cubre 2")
    Y código limpio, consistente, fácil de leer
    Y tiene error handling (aunque sea básico)
    → semi_senior
```

**Guía para "explica decisiones" (fila 5):**
- ✅ = El README o los comentarios mencionan POR QUÉ eligió el algoritmo, qué limitaciones tiene, o qué consideraciones tomó. Ejemplos: "Implementé greedy porque es O(n*m) y suficiente para este dataset", "La solución mínima tiene al menos 4 usuarios porque hay 8 módulos y cada usuario cubre 2", "Decidí guardar a archivo en lugar de consola para mayor trazabilidad".
- ❌ = Solo explica CÓMO correr el código, sin explicar ninguna decisión de diseño.

**Guía para "output consistente" (fila 8):**
- F8 evalúa el **canal** del output, no el formato del payload.
- ✅ = Ambas partes usan el mismo canal: ambas a consola O ambas a archivo.
- ❌ = Parte A guarda en un archivo JSON Y Parte B imprime por consola → inconsistente.
- No penalices por F8 si una imprime un dict y la otra una lista, mientras ambas vayan al mismo canal. La consistencia del **formato** se evalúa en F13 ("imprime como pide la letra"), no acá.

El tiempo lo encontrás en el README. Si no está reportado, no lo penalices — anotalo como observación.

### Señales blandas que pueden bajar el nivel

Algunas observaciones no están en la lista de 23 criterios pero pesan en la decisión final del nivel. No suman ni restan puntos al puntaje X/23, pero te autorizan a **bajar un escalón** (ej. de Semi Senior a Junior) cuando aparecen de forma marcada. Anotalas en `otras_notas` o en `aspectos`.

- **Tono inadecuado en la documentación.** Afirmaciones grandilocuentes que no están respaldadas por el código (ej. nombrar técnicas avanzadas que no se usan, comparar con alternativas en lenguaje despectivo, justificar elecciones obvias con páginas de teoría). Señal de calibración: ¿el README sostiene un tono más sofisticado que la solución entregada?
- **Mezcla de idiomas** en la documentación (ej. README empieza en español y termina en inglés, secciones en idiomas distintos sin razón). Un proyecto puede estar entero en inglés o entero en español; la mezcla atenta contra la presentación.
- **Tiempo verbal narrativo en futuro** ("voy a usar Python", "primero voy a proponer una solución") en vez de presente descriptivo o pasado ("uso Python", "la solución implementa..."). El estándar de la documentación técnica es presente o pasado, no futuro narrativo: indica que el README se redactó como una bitácora en vez de como una descripción del entregable.
- **Inconsistencias estéticas sistemáticas** (typos repetidos, formateo errático, capitalización inconsistente en títulos, mayúsculas aleatorias). Cada una individualmente es trivial; en conjunto desmerecen un trabajo que de otro modo estaría prolijo.
- **Falta de error handling cuando el candidato lo declara explícitamente.** Si el README dice "asumo datos válidos" o "no manejo errores", eso ya está penalizado en F25 = 0. Pero si además el candidato presenta su solución como "sólida", "robusta" o "production-ready" mientras explícitamente omite error handling, eso es una señal de **desalineación entre la pretensión y la entrega** — bajalo un nivel.

Estas señales no convierten un Semi Senior en no_suficiente. Pero sí pueden mover un Semi Senior a Junior, o un Junior a Trainee, cuando son varias o muy marcadas. Cuando uses una de estas para bajar el nivel, **mencionalo explícitamente en la justificación** (ej. "lo bajo a Junior por la mezcla de idiomas y el tono arrogante del README, que desmerecen una solución técnica correcta").

### Justificación del nivel

Además del valor del nivel (0-3), **producí siempre una justificación concisa (2-3 oraciones, ~50 palabras)** que explique por qué el candidato cae en ese nivel y no en el contiguo (arriba o abajo). Esto le permite al humano validar o corregir la decisión sin tener que recorrer los 23 criterios.

Formato:
- Empezá por lo que lo clasifica ("Cumple X, Y, Z").
- Terminá por lo que lo diferencia del nivel contiguo ("No llega a Semi Senior por W" / "No baja a Junior porque V").
- Si el tiempo estaba reportado y pesó en la decisión, mencionalo.

Ejemplos:

> Semi Senior: cumple todos los críticos, explica el algoritmo greedy y la cota mínima, tiene error handling y encuentra el set mínimo (F31). Se diferencia de Junior por la profundidad del README y por el extra de F31. Tiempo reportado: 3h30.

> Junior: cumple todos los críticos y organiza en funciones, pero no documenta versión de runtime (F4) ni alcanza el set mínimo (F31). No llega a Semi Senior por esas dos ausencias; no baja a Trainee porque el código es claro y documenta el "cómo correr".

> Trainee: cumple los críticos pero el README solo indica el comando de ejecución, sin explicar decisiones, y el código mezcla responsabilidades. No baja a no_suficiente porque los tres críticos (F12/F28/F29) están en ✅.

Guardá esta justificación — el Paso 8 la incluye en el texto para Asana, justo después de la línea de nivel.

---

## Paso 8 — Generar texto para Asana

El formato está centralizado en `sca/reporter/templates.py` — **es la fuente única de verdad**. Si cambia el checklist, las secciones o el orden, se toca ese archivo (nunca dupliques el template acá ni en la Routine).

Armá el payload y el texto invocando los builders del módulo:

```python
import os, sys, json
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.reporter.templates import (
    build_scores_payload, build_asana_text, build_asana_title,
)

scores = {
    # 23 criterios scoreables + fila 34 con el nivel (0-3)
    3:  <1|0>,  4:  <1|0>,  5:  <1|0>,
    8:  <1|0>,  9:  <1|0>, 10: <1|0>, 11: <1|0>, 12: <1|0>, 13: <1|0>,
    16: <1|0>, 17: <1|0>, 18: <1|0>, 19: <1|0>, 20: <1|0>,
    21: <1|0>, 22: <1|0>, 23: <1|0>, 24: <1|0>, 25: <1|0>,
    28: <1|0>, 29: <1|0>, 30: <1|0>, 31: <1|0>,
    34: <0|1|2|3>,
}

payload = build_scores_payload(
    scores,
    apellido="<apellido>",
    nombre="<nombre>",
    aspectos=["<aspecto 1>", "<aspecto 2>"],
    otras_notas="<notas de corrección>",
    feedback="<feedback para el candidato>",
    nivel_justif="<justificación de 2-3 oraciones del Paso 7>",
)

print(build_asana_title(payload))   # "SCA — <Apellido>, <Nombre>"
print(build_asana_text(payload))    # bloque completo con secciones + ✅/❌
```

El texto que devuelve `build_asana_text` tiene la estructura:

```
Nivel: <emoji> <nivel>
Puntaje: <X>/23
Por qué este nivel: <justificación>

📚 Documentación       → filas 3, 4, 5
👨‍💻 Usabilidad         → filas 8, 9, 10, 11, 12, 13
🍝 Calidad del código  → filas 16-25
🛠 Eficacia y Eficiencia → filas 28, 29, 30, 31

⭐ Aspectos que destacan: ...
📝 Otras notas: ...
🎁 Feedback: ...
```

---

## Paso 9 — Output final

Entregá al usuario:
1. El **texto para Asana** en el chat (fácil de copiar)
2. Un **resumen breve** del nivel y los puntos más importantes

Si hay errores críticos, destacalos visualmente al principio del resumen.
