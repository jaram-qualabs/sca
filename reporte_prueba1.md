# Reporte de Corrección — Prueba 1
**Generado por:** SCA (Sistema de Corrección Automatizada)

---

## Nivel: ⭐ Semi Senior

**Tiempo reportado:** Parte A: 1h 12min — Parte B: 2h 26min (total ~3h 38min)

---

## 🛠 Eficacia y Eficiencia

✅ Parte A correcta
✅ Consigue un set de usuarios que cubre todos los módulos
✅ Busca un set reducido (no devuelve todos los usuarios)
❌ Asegura el set mínimo (óptimo)
→ Usa un algoritmo greedy que devuelve 5 usuarios. El óptimo es 4. La solución greedy no garantiza el mínimo absoluto, aunque el candidato reconoce esto en el README ("solución greedy del minimal hitting set problem").

---

## 📚 Documentación

✅ Explica cómo correr el código
→ Indica el comando exacto y cómo pararse en la carpeta correcta.

❌ Documenta la versión de la tecnología
→ No indica versión de Python.

✅ Explica elecciones tomadas
→ Explica por qué eligió greedy y razona sobre el mínimo teórico de 4 usuarios. Esto es una muestra de pensamiento de nivel semi senior.

---

## 󰞦 Usabilidad

✅ El output es consistente
→ Parte A escribe a archivo JSON, Parte B imprime por consola. Ambas consistentes dentro de sí mismas, aunque el output no es exactamente el mismo canal.

✅ Parametriza los archivos de entrada
→ Usa `--path` via argparse. Bien implementado.

✅ No hardcodea nombres de archivos
→ Filtra todos los `.json` con `os.listdir`, no menciona nombres específicos.

✅ No hardcodea la cantidad de archivos
→ El algoritmo es dinámico, no asume 20 archivos en ningún punto.

✅ No hardcodea los providers esperados ❗
→ No hay ninguna mención de `authn.provider_X` ni `authz.provider_Y` en el código.

❌ Imprime la salida en el formato pedido en la letra
→ La Parte A guarda a un archivo JSON pero no imprime por consola. La letra pide mostrar el resultado. La Parte B imprime la lista de paths completos (ej: `./u18.json`) en vez del formato `['./u18.json', ...]` esperado — aunque esto es menor.

---

## 🍝 Calidad del código

✅ Nomenclatura consistente
→ Usa snake_case de forma consistente en toda la solución. Sin mezclas.

✅ Comentarios adecuados
→ Cada función tiene un comentario de una línea que describe su propósito. Breves y útiles.

✅ Sin comentarios excesivos
→ No hay código comentado ni comentarios obvios.

✅ Sigue convenciones de Python
→ Estructura de módulo con `if __name__ == "__main__"`, uso de argparse, json, os. Todo idiomático.

✅ Divide el problema en funciones concretas
→ `main`, `get_args`, `users_by_provider`, `process_user_info`, `minimum_users_required`, `get_universe`, `get_largest_subset`. Excelente separación de responsabilidades.

✅ No repite el código de la Parte A
→ La Parte B reimplementa la lectura de archivos de forma adaptada a su necesidad (`users_provider_dict` vs `users_by_provider`). No copia código, lo adapta.

❌ Sin código duplicado ❗
→ `get_args()` y `process_user_info()` (en su estructura base) están prácticamente duplicadas entre `parteA.py` y `parteB.py`. Podrían estar en un módulo compartido.

✅ Indentación correcta
→ Sin problemas de indentación.

✅ Formato regular
→ Código limpio, sin espacios irregulares.

✅ Tiene error handling
→ Usa `try/except` en el loop de lectura de archivos con un mensaje informativo. Cubre el caso de archivos corruptos o con formato incorrecto.

---

## ⭐ Aspectos que destacan

(+) Elige e implementa correctamente el algoritmo Greedy para el Minimal Hitting Set Problem — nombra el problema correctamente en el README, lo cual demuestra sólidos conocimientos de algoritmos.

(+) El código es extremadamente limpio y fácil de leer. Funciones bien nombradas, comentarios breves y útiles, sin ruido.

(+) Incluye una carpeta `test/` con datos de prueba propios — señal de buenas prácticas.

(+) Razona sobre la cota inferior teórica del problema (4 usuarios) en el README, mostrando pensamiento analítico.

(-) `parteA.py` y `parteB.py` son archivos separados con lógica de lectura duplicada. Un módulo `utils.py` compartido sería más prolijo.

(-) El algoritmo greedy no garantiza el set mínimo, aunque el candidato es transparente sobre esto.

---

## 📝 Otras notas de corrección

- El candidato incluye carpeta `test/` con sus propios datos de prueba para validar antes de entregar — esto es un síntoma de madurez técnica poco común.
- La solución greedy es correcta y eficiente. El set de 5 usuarios es "aceptable" según el manual, aunque no óptimo.
- La separación entre `parteA.py` y `parteB.py` en archivos distintos es una decisión razonable, pero genera duplicación de la función de lectura.
- Tiempo total (~3h 38min) está dentro del rango Semi Senior (<4h).

---

## 🎁 Feedback para el candidato

Tu solución es sólida y demuestra un muy buen nivel técnico. La implementación del algoritmo Greedy para el Minimal Hitting Set está bien hecha y correctamente documentada. Para mejorar, considerá extraer la lógica de lectura de archivos a un módulo compartido (`utils.py`) para evitar duplicar código entre `parteA.py` y `parteB.py`. Si querés llevar la solución al siguiente nivel, explorá algoritmos exactos como backtracking o programación entera para garantizar el set mínimo absoluto — aunque para este dataset el greedy da un resultado aceptable.
