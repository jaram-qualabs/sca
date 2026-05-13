# SCA Backend — Criterios y nivel (solo para la Routine)

Versión compacta del SKILL.md para uso en la Routine desatendida.
Contiene los 23 criterios, las guías de scoring y las reglas de nivel.
**No incluye** pasos de setup, instalación ni generación de Asana (eso está en PROMPT.md).

---

## Criterios (0/1 cada uno)

| Fila | Criterio | Clave para scorear |
|------|----------|--------------------|
| F3  | Explica cómo correr | README tiene comandos concretos de instalación y ejecución |
| F4  | Documenta versión tecnología | Versión en texto humano (README/comentario), NO solo en pyproject/package.json/Dockerfile |
| F5  | Explica decisiones | README o comentarios mencionan POR QUÉ eligió el enfoque, aunque sea brevemente |
| F8  | Output consistente | Mismo **canal** (ambas consola O ambas archivo). No penalizar por formato distinto |
| F9  | Parametriza carpeta de archivos | Path de datos es argumento/env var/config, no hardcodeado en el código |
| F10 | No hardcodea nombres de archivos | Sin `u0.json`, `u1.json`... ni prefijos como `'u'+i+'.json'`. Prefijo hardcodeado = F10=0 |
| F11 | No hardcodea cantidad | Sin `for i in range(20)` ni `i < 20`. Debe descubrir los archivos dinámicamente |
| F12 ❗ | No hardcodea providers | Sin `authn.provider_1`, `authz.provider_2` etc. en el código → si aparece, nivel=no_suficiente |
| F13 | Output correcto | Formato del output coincide con lo esperado (ver expected_output.md) |
| F16 | Nomenclatura consistente | camelCase / snake_case según lenguaje, sin mezcla aleatoria |
| F17 | Comentarios adecuados | Comentarios que explican el "por qué" o aclarán código no obvio |
| F18 | Sin comentarios excesivos | Sin líneas comentadas dejadas, sin JSDoc vacío, sin cada línea comentada |
| F19 | Sigue convenciones del lenguaje | Python: snake_case, `__main__`. JS: `const`/`let`, ES modules. Java: PascalCase clases |
| F20 | Divide en funciones | Responsabilidad única por función, **en AMBAS partes** (si parteA es monolítica → F20=0) |
| F21 | No repite código de Parte A | Parte B no copy-paste lógica de Parte A; importa o reimplementa adaptado |
| F22 | Sin código duplicado interno | Sin bloques repetidos dentro de un mismo archivo (independiente de F21) |
| F23 | Sin mala indentación | Indentación consistente (2 o 4 espacios, no mezcla) |
| F24 | Sin formato irregular | Sin trailing whitespace, saltos de línea aleatorios, tabs/spaces mezclados |
| F25 😀 | Error handling (bonus) | `try/except` que hace algo útil (loguea, retorna default, HTTP 500). Rerethrow puro = no cuenta |
| F28 ❗ | Parte A correcta | Validator SCA confirma agrupación correcta → si falla, nivel=no_suficiente |
| F29 ❗ | Parte B cubre 8 módulos | Validator SCA confirma cobertura → si falla, nivel=no_suficiente |
| F30 | Busca set reducido | Usa heurística de reducción (greedy, "rarest first", priority queue, etc.) |
| F31 😀 | Asegura mínimo absoluto (bonus) | Backtracking / fuerza bruta / ILP / SAT que *garantiza* el mínimo. Greedy que da 4 por suerte = F31=0 |
| F34 | Nivel (0-3) | 0=no_suficiente, 1=trainee, 2=junior, 3=semi_senior |

---

## Guías de scoring (los más confundidos)

**F4 — Versión:** archivo de toolchain no cuenta (`pyproject.toml requires-python`, `.python-version`, `package.json engines`). Solo vale si está escrito en lenguaje natural en el README o instrucciones.

**F5 — Decisiones:** no exigir análisis formal. Basta con mencionar POR QUÉ aunque sea brevemente. Nombres de funciones como `greedy_cover` o `rarest_first` también cuentan.

**F8 — Canal del output:** mismo canal = ambas consola O ambas archivo. Parte A en archivo + Parte B en consola = F8=0. Distinto formato en el mismo canal = no penalizar.

**F10 — Nombres de archivos:** prefijo hardcodeado cuenta como violación. `` `u${i}.json` `` o `'u' + i + '.json'` = F10=0 aunque el número sea dinámico.

**F20 — Divide en funciones:** evaluar AMBAS partes. Si parteB es un modelo de funciones pero parteA es una función monolítica de 40+ líneas → F20=0.

**F21 vs F22:** código duplicado que involucra Parte A → F21. Duplicado dentro de una sola parte → F22. Son independientes.

**F25 — Error handling:** `try/except` que solo hace `raise` o `throw error` = no cuenta. Debe hacer algo útil (log, mensaje al usuario, valor por defecto, HTTP 5xx).

**F30 vs F31:** F30 = intención de reducir (heurística presente). F31 = garantía del mínimo absoluto (solo backtracking/brute force/ILP/SAT). Greedy que da 4 por casualidad → F30=✅, F31=❌.

---

## Reglas de nivel

```
Si F12=0 O F28=0 O F29=0 → no_suficiente (sin excepciones)

tiempo > 6h
  O docs muy básica ("corré con python") o inexistente
  O código difícil de entender
  → trainee

tiempo 4-6h
  Y docs indica comando + versión de runtime (F4=1)
  Y organiza en funciones (F20=1)
  → junior

tiempo < 4h
  Y explica decisiones de diseño (F5=1)
  Y código limpio y consistente
  Y error handling (F25=1)
  → semi_senior
```

Tiempo sin reportar: no penalizar, anotar en `otras_notas`.

## Señales blandas (pueden bajar un escalón, no convierten en no_suficiente)

- README más grandilocuente que la solución entregada (promete técnicas que no están).
- Mezcla de idiomas en la documentación sin razón.
- Tiempo verbal en futuro ("voy a usar...") en vez de presente/pasado.
- Inconsistencias estéticas sistemáticas (typos repetidos, capitalización errática).
- README dice "solución robusta/production-ready" pero F25=0.

Cuando se usa una señal blanda para bajar nivel, mencionarlo explícitamente en `nivel_justif`.

## Justificación del nivel (obligatoria, 2-3 oraciones)

- Empezar: "Cumple X, Y, Z."
- Terminar: "No llega a [nivel superior] por W" / "No baja a [nivel inferior] porque V."
- Mencionar tiempo si pesó en la decisión.
