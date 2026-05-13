# SCA Frontend — Criterios y nivel (solo para la Routine)

Versión compacta del SKILL.md + manual.md para uso en la Routine desatendida.
Contiene los 35 criterios, las guías de scoring y las reglas de nivel.
**No incluye** pasos de setup, instalación ni generación de Asana (eso está en PROMPT.md).

---

## Criterios (0/1 cada uno)

### 📚 Documentación

| Fila | Criterio | Clave para scorear |
|------|----------|--------------------|
| F101 | Explica cómo correr | README tiene comandos concretos (install + dev/start) |
| F102 | Documenta versión tecnología | Versión de Node/runtime en README en lenguaje natural, NO solo en package.json/engines/.nvmrc |
| F103 | Explica decisiones | README/comentarios mencionan POR QUÉ eligió Redux vs Context, SCSS, estructura de componentes, etc. |

### 👨‍💻 Usabilidad

| Fila | Criterio | Clave para scorear |
|------|----------|--------------------|
| F104 | Output consistente | Todo en la UI, sin mezcla con console.log escupiendo JSON mientras la UI hace otra cosa |
| F105 | Parametriza archivos | Constante centralizada, env var o config. Una constante hardcoded en un solo lugar cuenta |
| F106 | No hardcodea nombres de archivos | Sin `u0.json`, `u1.json`... ni prefijos como `'u'+i+'.json'` en el cliente |
| F107 | No hardcodea cantidad | Sin `for i < 20` ni `i < 20` en el cliente (si la lógica está en la API, no aplica al cliente) |
| F108 ❗ | No hardcodea providers | Sin `authn.provider_1`, `authz.provider_2` etc. → si aparece, nivel=no_suficiente |

### 👨‍💻 Usabilidad Front

| Fila | Criterio | Clave para scorear |
|------|----------|--------------------|
| F109 | Botón activo seleccionado | Tab activo tiene estilo visual diferente (color, borde, fondo) que se mantiene |
| F110 | Headers correctos | Header dinámico dice exactamente `"Number of users in [module N]:"` |
| F111 | Botones correctos | Los cuatro botones: Delete, Advice, Create, Submit — con sus íconos |
| F112 | Ruteo de React | `react-router-dom` o equivalente (nuqs con history:push también cuenta) con URLs que reflejan selección |
| F113 | Similitud visual módulo | Layout: tabs nivel 1 arriba, tabs nivel 2 abajo, header, lista usuarios, botones inferiores |
| F114 | Similitud visual botones | Colores cercanos al mock (rojo Delete, amarillo Advice, rosado Create, verde Submit), íconos |
| F115 | Responsive | Usa flex/grid o breakpoints. `w-2/3` fijo sin breakpoints en mobile = F115=0 |

### 🍝 Calidad del código

| Fila | Criterio | Clave para scorear |
|------|----------|--------------------|
| F116 | Nomenclatura consistente | camelCase variables/funciones, PascalCase componentes |
| F117 | Comentarios adecuados | Al menos algún comentario que explica el "por qué" en código no obvio |
| F118 | Sin comentarios excesivos | Sin código comentado dejado, sin cada línea comentada |
| F119 | Sigue convenciones React/TS | `const`/`let`, ES modules, hooks en funcionales, no `document.getElementById`, no mutación directa de state |
| F120 | Divide en funciones/componentes | Componentes con responsabilidad clara, hooks personalizados para lógica compartida |
| F121 ❗ | Sin código duplicado | Sin bloques de 10+ líneas repetidos en varios componentes → si sistemático, nivel=no_suficiente |
| F122 | Sin mala indentación | Indentación consistente (2 o 4 espacios) |
| F123 | Sin formato irregular | Sin trailing whitespace, sin saltos de línea aleatorios |
| F124 😀 | Error handling (bonus) | `try/catch` que muestra error al usuario, retorna fallback. Rerethrow puro = no cuenta |

### 🍝 Calidad del código Front

| Fila | Criterio | Clave para scorear |
|------|----------|--------------------|
| F125 | Componente genérico Button | Existe `<Button>` reusable con props (variant, onClick, icon, etc.) |
| F126 😀 | Componente genérico Contenedor | Existe `<Card>` / `<Panel>` / `<Layout>` que encapsula header+content reusable |
| F127 | Destructuring de props | `function Comp({ name, onClick })` en lugar de `props.name` / `props.onClick` |
| F128 | Redux store | Específicamente Redux (RTK o classic). Context API, Zustand, useState global = F128=0 |
| F129 | Carpeta componentes genéricos | Existe `src/components/` (o `src/common/`) separada de pages/features |
| F130 | CSS desacoplado | Estilos en archivos separados o Tailwind. Sin inline styles (`<div style={{...}}>`) esparcidos |
| F131 | Usa SCSS | Archivos `.scss` con variables/mixins/nesting. Solo `.css` o CSS-in-JS = F131=0 |
| F132 ❗ | Funcionales o class (no mezcla) | Todos funcionales con hooks O todos class-based. Mezcla aleatoria = F132=0, nivel=no_suficiente |
| F133 | Constantes en archivos separados | Existe `src/constants.ts` o `src/config.ts` con strings de UI, paths, endpoints |
| F134 | CSS junto al componente | Cada componente con su CSS al lado (módulo/archivo propio). Sin `all.css` global con todo mezclado. Con Tailwind: ✅ por defecto |

### 🛠 Eficacia

| Fila | Criterio | Clave para scorear |
|------|----------|--------------------|
| F135 ❗ | Parte A correcta | La UI muestra los usuarios correctos por cada combinación tab nivel 1 + nivel 2. Si incorrecto → nivel=no_suficiente |
| F140 | Nivel (0-3) | 0=no_suficiente, 1=trainee, 2=junior, 3=semi_senior |

---

## Guías de scoring (los más confundidos)

**F102 — Versión:** `package.json engines` o `.nvmrc` no cuentan. Solo lenguaje natural en README ("Requires Node 18+").

**F104 — Output consistente (monorepo full stack):** si el frontend solo consume una API y muestra en UI, F104=1. Solo falla si hay mezcla (UI renderiza algo distinto a lo que la API devuelve sin razón).

**F105/F106/F107 — Monorepo full stack:** si el frontend delega el acceso a archivos al backend (API), evaluar desde el rol del cliente. El frontend no maneja archivos → F106=1, F107=1 por diseño correcto.

**F112 — Ruteo:** `react-router-dom` o equivalente. `nuqs` con `history:"push"` y URLs que reflejan la selección también cuenta.

**F115 — Responsive:** sin breakpoints (`sm:`, `md:`, `lg:`) + contenedor de ancho fijo (`w-2/3`) = F115=0. Overflow-scroll previene rotura pero no hace la app responsive.

**F121 — Duplicado (CRÍTICO):** bloques de 10+ líneas repetidos en múltiples componentes. Un copy-paste de 3 líneas no alcanza para F121=0.

**F128 — Redux:** solo Redux (RTK con slices + useSelector/useDispatch, o classic). Context API, Zustand, Jotai, Recoil = F128=0 aunque funcionen bien.

**F131 — SCSS:** debe haber archivos `.scss`. Tailwind + CSS custom properties en `.css` = F131=0. El template oficial pide SCSS explícitamente.

**F132 — Mezcla (CRÍTICO):** buscar `class.*extends.*Component` o `extends React.Component`. Si conviven con componentes funcionales sin razón → F132=0.

---

## Reglas de nivel

```
Si F108=0 O F121=0 O F132=0 O F135=0 → no_suficiente (sin excepciones)

puntaje < 12 con anti-patterns claros (document.getElementById en React,
  hardcodes generalizados, app no funciona) → trainee o no_suficiente

puntaje 12-17, los 4 críticos OK → trainee

puntaje 18-27, los 4 críticos OK, fidelidad mock razonable,
  al menos 2 componentes genéricos → junior

puntaje >= 28, los 4 críticos OK, fidelidad mock alta,
  Redux (F128=1) Y SCSS (F131=1) → semi_senior
```

**Nota:** sin Redux y sin SCSS, el techo es Junior aunque el puntaje sea ≥28.

## Señales blandas (pueden bajar un escalón)

Mismas que backend: README más grandilocuente que la solución, mezcla de idiomas, tiempo verbal en futuro, inconsistencias estéticas sistemáticas, desalineación entre pretensión y entrega.

Cuando se usa una señal blanda para bajar nivel, mencionarlo explícitamente en `nivel_justif`.

## Justificación del nivel (obligatoria, 2-3 oraciones)

- Empezar: "Cumple X, Y, Z."
- Terminar: "No llega a [nivel superior] por W" / "No baja a [nivel inferior] porque V."
- Mencionar fidelidad visual y Redux/SCSS siempre que sean relevantes.

Ejemplos calibrados:

> Junior: cumple los 4 críticos, fidelidad visual alta, hooks bien usados, Button y Layout genéricos. No llega a Semi Senior porque no usa Redux (F128) ni SCSS (F131). Con 29/35 es el techo del rango Junior.

> Trainee: cumple los 4 críticos y la app funciona, pero headers y botones no siguen los textos de la letra (F110/F111), formato del código inconsistente. No baja a No suficiente porque los 4 críticos están en ✅.
