# Manual de Corrección — Criterios Detallados

## Criterios del checklist (columna A = 0 o 1)

### 📚 Documentación (filas 3-5)
| Fila | Criterio | Notas |
|------|----------|-------|
| 3 | Explica cómo correr el código | Mínimo: un comando concreto. "Correr el archivo" no alcanza. |
| 4 | Documenta la versión de la tecnología | Ej: "Python 3.10", "Node 18". Si no lo indica → 0. |
| 5 | Explica elecciones o condiciones particulares | ¿Explica POR QUÉ eligió cierto algoritmo? ¿Menciona limitaciones o razonamiento? Ejemplos que cuentan: "Usé greedy porque es O(n*m)", "La cota mínima es 4 porque hay 8 módulos y cada usuario cubre 2", "Guardé a archivo para mayor trazabilidad". Solo decir "corré con python" NO cuenta. |

### 👨‍💻 Usabilidad (filas 8-13)
| Fila | Criterio | Notas |
|------|----------|-------|
| 8 | Output consistente | Todo por consola O todo por archivos, considerando AMBAS partes juntas. Si Parte A va a archivo JSON y Parte B imprime por consola → 0 (inconsistente). Si ambas van a consola → 1. Si ambas van a archivo → 1. |
| 9 | Parametriza los archivos | Usa argparse, variable de config, o constante. No hardcodeado en el medio del código. |
| 10 | No hardcodea nombres de archivos | No debe mencionar "u0.json", "u1.json", etc. en el código. |
| 11 | No hardcodea cantidad de archivos ❗ | No debe tener `range(20)` o similares. |
| 12 | No hardcodea providers ❗ CRÍTICO | Si aparece `authn.provider_1`, `authz.provider_2`, etc. → 0 y nivel NO SUFICIENTE automático |
| 13 | Imprime salida como en la letra 😀 | La letra tiene un JSON inválido (sin comas). Si el candidato lo nota y lo menciona/corrige → 1. Es bonus. |

### 🍝 Calidad del código (filas 16-25)
| Fila | Criterio | Notas |
|------|----------|-------|
| 16 | Nomenclatura consistente | camelCase O snake_case, no mezcla. |
| 17 | Comentarios adecuados | Dicen algo útil. No obviedades como `# opens file`. |
| 18 | Sin comentarios excesivos | No hay bloques de código comentado ni comentarios de ruido. |
| 19 | Sigue convenciones de la tecnología | Python: snake_case, if __name__, etc. JS: const/let, arrow functions, etc. |
| 20 | Divide en funciones pequeñas | No todo en main(). Funciones con responsabilidad única. |
| 21 | No repite código de Parte A | Parte B puede reimplementar adaptado, pero no copy-paste. |
| 22 | Sin código duplicado ❗ | Dentro de cada parte, lógica no repetida. También entre archivos si comparten módulos. |
| 23 | Sin código mal indentado | En Python esto es imposible que compile mal, pero puede haber inconsistencias. |
| 24 | Sin formato irregular | Sin espacios extra, saltos de línea innecesarios, etc. |
| 25 | Tiene error handling 😀 | try/except, validaciones de input, manejo de archivos corruptos. Es bonus si lo hace bien. |

### 🛠 Eficacia y Eficiencia (filas 28-31)
| Fila | Criterio | Notas |
|------|----------|-------|
| 28 | Parte A correcta ❗ CRÍTICO | Validado automáticamente. Si falla → nivel NO SUFICIENTE. |
| 29 | Parte B cubre todos los módulos ❗ CRÍTICO | Validado automáticamente. Si falla → nivel NO SUFICIENTE. |
| 30 | Busca un set reducido | No devuelve todos los 20 usuarios. Ordena por cobertura o similar. |
| 31 | Asegura el set mínimo 😀 | 4 usuarios es el óptimo. Si usa backtracking, combinatoria o fuerza bruta completa → 1. |

---

## Nivel (fila 34, valor 0-3)

### 0 — No suficiente 🔴
Cuando ocurre CUALQUIERA de:
- Parte A con errores
- Parte B no cubre todos los módulos
- Hardcodea los providers (`authn.provider_1`, etc.)
- Tiempo > 12h (backend) o > 24h (frontend)
- Frontend: toda la lógica en un solo archivo

### 1 — Trainee 🟡
- Tiempo > 6h (backend) o > 16h (frontend)
- Documentación muy básica ("correr con python") o inexistente
- Sin comentarios o comentarios de poca utilidad
- Le faltan criterios de reutilización
- Código difícil de entender

### 2 — Junior 🟢
- Tiempo < 6h (backend) o entre 8h y 16h (frontend)
- Documentación adecuada: indica comando, versión de runtime, dónde poner archivos
- Organiza el código en funciones
- Código comprensible

### 3 — Semi Senior ⭐
- Tiempo < 4h
- Documentación explica no solo cómo usar sino también decisiones técnicas tomadas y limitaciones
- Código consistente, fácil de leer, bien organizado, con comentarios donde agregan valor
- Hace error handling
- Posiblemente tiene tests unitarios

---

## Errores marcados como CRÍTICOS en el checklist
Los marcados con ❗ generan nivel NO SUFICIENTE si fallan:
- Fila 11: no hardcodea cantidad de archivos
- Fila 12: no hardcodea providers ← el más importante
- Fila 22: sin código duplicado ← no fuerza nivel, pero es grave
- Fila 28: Parte A correcta
- Fila 29: Parte B cubre módulos

---

## Iconos en el checklist
- ✅ = cumple (score 1)
- ❌ = no cumple (score 0)
- ❗ = error crítico (puede forzar nivel No suficiente)
- 😀 = bonus positivo (es 1 si lo hace, no penaliza si no)
