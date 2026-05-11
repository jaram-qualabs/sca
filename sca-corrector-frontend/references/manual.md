# SCA Frontend — Manual de Corrección (criterios fila por fila)

Detalle de los 35 criterios scoreables del checklist de frontend, mapeados al
template oficial (`Requerimientos/Template Frontend.xlsx`) y calibrados contra
las 3 correcciones humanas de muestra (`sca-corrector/references/frontend/`).

Cada fila se evalúa **0 o 1**. La suma da el puntaje X/35.

---

## 📚 Documentación

### F101 — Explica cómo correr el código

✅ El README documenta los comandos para instalar (`npm install` / `yarn` /
`pnpm install`) y correr (`npm run dev` / `npm start` / `npm run build`).

❌ El README no existe, o solo dice "es una app React" sin instrucciones
concretas.

### F102 — Documenta la versión de la tecnología

Aplica la lectura **estricta** definida en backend: si la versión solo aparece
en archivos de toolchain (`package.json` `engines`, `.nvmrc`, `.node-version`)
sin mención humana en el README/instrucciones, F102 = 0. Si está dicha en
lenguaje natural en el README ("Requires Node.js 18+", "Built with React 18"),
F102 = 1.

### F103 — Explica cómo funciona el código, decisiones, condiciones particulares

✅ El README explica al menos una decisión de diseño: por qué eligió Redux
vs Context, por qué SCSS vs CSS-in-JS, cómo organizó los componentes, qué
patrón de routing usó, etc.

❌ Solo instrucciones de ejecución sin ningún "por qué".

---

## 👨‍💻 Usabilidad (compartida con backend)

### F104 — Output consistente

Aplica solo a la Parte A si el candidato la entregó como script aparte. Si la
Parte A se calcula in-browser dentro de la app React, F104 se evalúa contra el
canal del front (todo se muestra en la UI, sin mezcla con `console.log`
escupiendo JSON al terminal mientras la UI hace otra cosa).

✅ Output consistente (todo por consola o todo por archivos / UI).

❌ Parte A imprime por consola y Parte B (UI) renderiza algo distinto sin
puente claro.

### F105 — Parametriza los archivos en la ejecución

✅ Acepta una constante centralizada, archivo de config, variable de
entorno, o argumento CLI. Una constante hardcoded centralizada en un solo
lugar **cuenta** (calibrado contra Manu).

❌ Path hardcoded esparcido en múltiples archivos.

### F106 — No hardcodea nombres de archivos

Igual que backend F10: no debe aparecer `u0.json`, `u1.json`, ... como
strings literales en el código. Tampoco prefijos como `'u' + i + '.json'`.
Usar `fs.readdirSync` / `import.meta.glob` / fetch dinámico → F106 = 1.

### F107 — No hardcodea la cantidad de archivos

✅ El código itera sobre lo que encuentra, no asume 20.

❌ Loop con `for (let i = 0; i < 20; i++)`.

### F108 — ❗ No hardcodea providers (CRÍTICO)

Si aparece cualquier string como `authn.provider_1`, `authz.provider_2`, etc.
en el código del candidato, **F108 = 0** y el nivel es automáticamente
`no_suficiente`. Aplica a Parte A y a Parte B (componentes hardcoded por
provider conocido también cuentan como hardcode).

---

## 👨‍💻 Usabilidad Front (específicos frontend)

### F109 — Queda seleccionado el botón del módulo o submódulo

✅ Cuando el usuario clickea una tab nivel 1 o nivel 2, el botón muestra un
estado visual de "seleccionado" (color distinto, borde, fondo, etc.) y el
estado se mantiene mientras navega el contenido.

❌ Los botones se ven todos iguales aunque haya uno activo, o el estado
visual se pierde.

### F110 — Los headers dicen lo que pide la letra

La letra muestra un header dinámico: **"Number of users in module N:"**.

✅ El header refleja el módulo seleccionado y usa exactamente la fórmula de
la letra.

❌ Header genérico ("Users:" o "Module list") o estático.

### F111 — Los botones dicen lo que pide la letra

La letra muestra cuatro botones inferiores: **Delete**, **Advice**, **Create**,
**Submit**. Cada uno con su ícono.

✅ Los cuatro botones están presentes con esos textos exactos (o traducción
fiel) y los íconos asociados.

❌ Faltan botones, o tienen textos distintos ("Eliminar" vs "Delete" puede ser
un detalle, pero "Borrar" cuando la letra dice "Delete" rompe fidelidad).

### F112 — Usa el ruteo de React

✅ Usa `react-router-dom` (o equivalente) para navegar entre tabs nivel 1 /
nivel 2, con URLs distintas por módulo seleccionado.

❌ Solo state local sin URLs reflejando la selección. Aunque la app funcione,
no usar routing es F112 = 0 según el template oficial.

### F113 — Similitud visual del módulo a la letra

Comparación visual contra el mock (ver `references/mock.png`).

✅ El layout general respeta la jerarquía: tabs nivel 1 arriba, tabs nivel 2
debajo, header con texto del módulo, lista vertical de usuarios al centro,
botones inferiores. Colores, formas y tipografía cercanos al mock.

❌ El layout es radicalmente distinto (tabs como dropdown, lista horizontal,
botones en otro lugar).

### F114 — Similitud visual de los botones a la letra

✅ Los botones usan colores cercanos al mock (rojo Delete, amarillo Advice,
rosado Create, verde Submit), forma de píldora, íconos asociados.

❌ Botones genéricos sin estilizar.

### F115 — Responsive

✅ La app se acomoda a anchos distintos sin romperse (≥320px mobile, ≥768px
tablet, ≥1024px desktop). Mínimamente: usa flex/grid o media queries.

❌ Layout quebrado en mobile (overflow horizontal, contenido solapado).

---

## 🍝 Calidad del código (compartida con backend)

### F116 — Nomenclatura consistente

✅ camelCase para variables/funciones, PascalCase para componentes y clases.
Sin mezcla aleatoria de estilos.

### F117 — Comentarios adecuados

✅ Comentarios que explican el "por qué" o aclaran código no obvio.

❌ Sin comentarios donde son necesarios, o comentarios que solo repiten el
código.

### F118 — Sin comentarios excesivos

✅ Comentarios puntuales.

❌ Cada línea comentada, código comentado dejado sin borrar, JSDoc generado
automáticamente sin contenido útil.

### F119 — Sigue convenciones de la tecnología

JS/TS: `const`/`let` (no `var`), ES modules (`import`/`export`), arrow
functions o function declarations consistentes, JSX bien formateado.

React específico:
- Componentes funcionales con hooks (estándar moderno).
- Props bien tipadas (TS) o validadas (PropTypes).
- No `document.getElementById` en código React (anti-pattern).
- No mutación directa de state.

### F120 — Divide en funciones / componentes

✅ Componentes con responsabilidad clara, hooks personalizados extraídos
cuando hay lógica compartida.

❌ Un componente de 300 líneas que hace todo (App.jsx con toda la lógica de
fetch, state, render).

### F121 — ❗ Sin código duplicado (CRÍTICO)

✅ DRY: lógica compartida está extraída.

❌ Mismo bloque de código repetido en 3 componentes. Si esto pasa de forma
sistemática → F121 = 0 y nivel `no_suficiente`.

### F122 — Sin código mal indentado

✅ Indentación consistente (2 o 4 espacios, no mezcla).

### F123 — Sin formato irregular

✅ Sin saltos de línea aleatorios, sin trailing whitespace, sin tabs/spaces
mezclados.

### F124 — Tiene error handling (bonus 😀)

Bonus criterion. Mismo criterio de "real" que en backend:

✅ `try/catch` que loguea, muestra mensaje al usuario, retorna fallback útil.
Componente que muestra "Error al cargar datos" si el fetch falla.

❌ Sin manejo, o `catch (e) { throw e }` (rerethrow sin hacer nada).

---

## 🍝 Calidad del código Front (específicos frontend)

### F125 — Componentes genéricos para el botón

✅ Existe un componente `<Button>` reusable usado por todos los botones (tabs,
inferiores). Acepta props (color, ícono, onClick, label).

❌ Cada botón se inlinea con su propio JSX y CSS.

### F126 — Componentes genéricos para el Contenedor (header + content)

✅ Existe un componente tipo `<Card>` o `<Panel>` que encapsula header +
content y se reusa.

❌ Layout repetido manualmente en cada lugar. (En Frontend 1 esto se marcó
con bonus 😀 cuando estaba bien hecho.)

### F127 — Usa destructuring de props

✅ `function MyComp({ name, onClick }) { ... }` en lugar de `function
MyComp(props) { props.name; props.onClick; }`.

❌ Acceso por `props.x` consistente en todos los componentes.

### F128 — Utiliza el redux store

Criterio específico del template. Si el candidato usa **Redux** (RTK o
classic) para manejar estado global → F128 = 1. Context API o Zustand
**no cuentan** según el template oficial.

✅ `@reduxjs/toolkit` con slices, `useSelector`/`useDispatch`.

❌ Solo `useState`/`useContext`, o estado pasado como props drilling.

### F129 — Carpeta separada para componentes genéricos

✅ Existe `src/components/` (o `src/common/`) con los componentes reusables,
separada de `src/features/`, `src/pages/` o equivalente.

❌ Todos los componentes mezclados en una sola carpeta.

### F130 — CSS desacoplado

✅ El CSS está en archivos separados (`Component.module.css`, `styles.scss`)
en lugar de inline o en strings dentro del JSX.

❌ Estilos inline esparcidos (`<div style={{ ... }}>`), o styled-components
mezclados con CSS modules sin criterio.

### F131 — Usa SCSS

Criterio específico del template oficial. CSS plano no cuenta — debe ser SCSS
(`.scss`).

✅ Archivos `.scss` con variables, mixins, nesting.

❌ Solo `.css` plano, o CSS-in-JS (styled-components, emotion).

### F132 — ❗ Componentes funcionales o no funcionales (no los mezcla, CRÍTICO)

Criterio crítico del template. Si el candidato mezcla **componentes class**
(`extends React.Component`) y **componentes funcionales** (hooks) sin razón
clara → F132 = 0 y nivel `no_suficiente`. La regla es: elegí un estilo y
mantenelo.

✅ Todos los componentes son funcionales con hooks (estándar moderno) O
todos son class-based (estilo legacy pero coherente).

❌ Mezcla aleatoria de los dos estilos.

### F133 — Constantes en archivos separados

✅ Existe `src/constants.js` o `src/config.js` con strings de UI, paths,
endpoints, etc.

❌ Strings mágicos esparcidos por todos los componentes.

### F134 — Arquitectura clara (CSS junto al componente)

✅ Cada componente vive en su carpeta o archivo con su CSS al lado:
`Button/Button.jsx + Button.module.scss + Button.test.jsx`.

❌ CSS suelto en `src/styles/all.css` con todas las reglas mezcladas.

---

## 🛠 Eficacia y Eficiencia

### F135 — ❗ Parte A correcta (CRÍTICO)

Si el candidato hizo Parte A como script aparte: validalo con
`sca/validators/part_a.py` igual que en backend.

Si la Parte A se calcula in-browser dentro de la app React: el corrector
inspecciona el state/output de la app (la lista de usuarios mostrada por cada
provider debería matchear `EXPECTED_OUTPUT`). Si la UI muestra los usuarios
correctos para cada combinación tab nivel 1 + tab nivel 2 → F135 = 1.

Si la lógica de inversión del JSON está rota (los usuarios mostrados no
matchean) → F135 = 0 y nivel `no_suficiente`.

---

## Calibración de niveles (visto en las 3 muestras)

| Muestra | Puntaje | Nivel | Observaciones |
|---|---|---|---|
| Frontend 1 | 22/35 | Junior | Border con Semi Senior si hubiera atendido feedback. Buena similitud visual, hooks bien usados. |
| Frontend 2 | 16/35 | Trainee | Generaba componentes genéricos pero formato inconsistente, mezcla idiomas. |
| Frontend 3 | 4/35 | No suficiente | Múltiples críticos fallados: F108 (providers), F107 (cantidad), F121 (duplicado). `document.getElementById` en React. |

### Heurística

- **Semi Senior**: ≥28/35, los 4 críticos en ✅, fidelidad mock alta, usa
  Redux + SCSS (los que el template marca explícitamente).
- **Junior**: 18-27/35, los 4 críticos en ✅, fidelidad mock razonable,
  componentes genéricos creados.
- **Trainee**: 12-17/35, los 4 críticos en ✅, código funciona pero arquitectura
  es mejorable.
- **No suficiente**: cualquier crítico en 0, o <12/35 con código que muestra
  desconocimiento básico (anti-patterns, código que no funciona, hardcodes
  generalizados).

Aplican las mismas **señales blandas** del backend: tono inadecuado en docs,
mezcla de idiomas, tiempo verbal en futuro, inconsistencias estéticas
sistemáticas pueden bajar un escalón aunque los criterios duros estén OK.
