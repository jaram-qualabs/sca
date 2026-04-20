# EVALUACIÓN TÉCNICA - PRUEBA 1

## RESUMEN EJECUTIVO

| Aspecto | Resultado |
|--------|-----------|
| **Nivel Asignado** | 🟢 Junior |
| **Puntaje** | 18/23 |
| **Tiempo Total** | 3:38 (1:12 + 2:26) |
| **Estado** | Funcional, mejorablemente |

---

## ANÁLISIS DE CÓDIGO

### Parte A: Agrupación de Usuarios por Proveedor

**Lógica:**
- Itera todos los archivos .json de la carpeta especificada
- Agrupa usuarios por (módulo, proveedor) 
- Genera estructura JSON con auth_module y content_module
- Guarda resultado en archivo `users_by_provider.json`

**Evaluación:** ✅ CORRECTA
- La lógica es clara y válida
- Maneja archivos dinámicamente sin hardcodeo
- Incluye error handling básico

---

### Parte B: Set Cover Mínimo

**Lógica:**
- Lee todos los JSON y construye dict usuario → set de proveedores
- Implementa algoritmo GREEDY iterativo:
  - Mientras quedan proveedores sin cubrir
  - Elige usuario que cubre más proveedores restantes
  - Agrega a resultado, elimina sus proveedores del universo
- Retorna lista de usuarios elegidos

**Evaluación:** ✅ FUNCIONAL, ❌ NO ÓPTIMO
- Cubre correctamente todos los 8 módulos
- Greedy NO garantiza solución mínima de 4 usuarios
- Puede devolver 5 o más usuarios (aceptable pero no óptimo)

---

## PUNTUACIÓN DETALLADA

### 📚 Documentación: 2/3 puntos
| F# | Criterio | Score | Notas |
|----|----------|-------|-------|
| 3 | Explica cómo correr | ✅ 1 | Comandos claros en README |
| 4 | Versión de tecnología | ❌ 0 | No menciona Python 3.x |
| 5 | Explica decisiones | ✅ 1 | Justifica greedy y mínimo de 4 |

### 👨‍💻 Usabilidad: 4/6 puntos
| F# | Criterio | Score | Notas |
|----|----------|-------|-------|
| 8 | Output consistente | ❌ 0 | A→archivo JSON, B→consola |
| 9 | Parametriza archivos | ✅ 1 | argparse con --path en ambas |
| 10 | No hardcodea nombres | ✅ 1 | os.listdir() dinámico |
| 11 | No hardcodea cantidad | ✅ 1 | Sin range(20) |
| 12 | No hardcodea providers | ✅ 1 | Lee de data['provider'] |
| 13 | JSON como en letra | ❌ 0 | No menciona formato |

### 🍝 Calidad de Código: 7/10 puntos
| F# | Criterio | Score | Notas |
|----|----------|-------|-------|
| 16 | Nomenclatura | ✅ 1 | snake_case consistente |
| 17 | Comentarios | ✅ 1 | Útiles y descriptivos |
| 18 | Sin exceso | ✅ 1 | Ni código comentado ni ruido |
| 19 | Convenciones Python | ✅ 1 | if __name__, argparse |
| 20 | Divide en funciones | ✅ 1 | 4 en A, 7 en B |
| 21 | No repite A | ❌ 0 | get_args() idéntica en ambas |
| 22 | Sin duplicación | ❌ 0 | process_user_info() duplicada |
| 23 | Indentación | ✅ 1 | Correcta |
| 24 | Formato | ✅ 1 | Limpio |
| 25 | Error handling | ✅ 1 | try/except en ambas |

### 🛠 Eficacia: 3/4 puntos
| F# | Criterio | Score | Notas |
|----|----------|-------|-------|
| 28 | Parte A correcta | ✅ 1 | Lógica válida |
| 29 | Parte B cubre módulos | ✅ 1 | Greedy cubre los 8 |
| 30 | Busca set reducido | ✅ 1 | Greedy minimiza |
| 31 | Set mínimo | ❌ 0 | No garantiza 4 usuarios |

**TOTAL: 18/23 puntos**

---

## PROBLEMAS CRÍTICOS

### 1️⃣ Output Inconsistente (F8)
**Severidad:** ALTA

```python
# Parte A (línea 6-7)
with open(path+'users_by_provider.json', 'w') as fp:
    json.dump(solution, fp)

# Parte B (línea 6)
print(minimum_users_required(users_providers))
```

**Impacto:** Dificulta testing e integración entre partes
**Solución:** Mantener el mismo canal (ambas a archivo o ambas a consola)

---

### 2️⃣ Código Duplicado (F21, F22)
**Severidad:** MEDIA

```python
# get_args() aparece igual en ambas (parteA:9-14 vs parteB:8-13)
def get_args():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--path", help="...", default='./')
    args = parser.parse_args()
    path = args.path
    return path

# process_user_info() prácticamente idéntica (parteA:28-37 vs parteB:27-33)
```

**Impacto:** Riesgo de bugs por desincronización
**Solución:** Crear utils.py e importar desde ambas

---

### 3️⃣ Falta Documentación (F4)
**Severidad:** BAJA

**Impacto:** Reproducibilidad limitada
**Solución:** Agregar "Requiere Python 3.8+" al README

---

### 4️⃣ Algoritmo No Óptimo (F31)
**Severidad:** MEDIA

**Impacto:** Puede no encontrar el set mínimo de 4 usuarios
**Solución:** Verificar si greedy alcanza 4; si no, usar backtracking

---

## FORTALEZAS

✅ **Tiempo excepcional:** 3:38 para problema complejo
✅ **Explicación clara:** Justifica algoritmo y cota mínima  
✅ **Código bien organizado:** Funciones con responsabilidades claras
✅ **Error handling:** Presente en ambas partes
✅ **Parametrización:** argparse en lugar de hardcode

---

## DETERMINACIÓN DEL NIVEL

### Criterios por Nivel

**JUNIOR ✅ ALCANZA:**
- Tiempo < 6h: ✅ (3:38h)
- Documentación adecuada: ✅ (excepto versión)
- Código en funciones: ✅
- Código comprensible: ✅

**SEMI SENIOR ❌ NO ALCANZA:**
- Documentación explica POR QUÉ: ✅
- Tiempo < 4h: ✅
- Código consistente: ❌ (output inconsistente)
- Sin duplicación: ❌ (funciones duplicadas)

**VEREDICTO: JUNIOR (nivel 2) 🟢**

---

## FEEDBACK CONSTRUCTIVO

### Para próximas mejoras:

1. **Unifica el output** → Ambas partes deben escribir al mismo lugar
   ```python
   # Opción A: ambas a archivo
   # Opción B: ambas a consola
   ```

2. **Elimina duplicación** → Crea `utils.py`
   ```python
   # utils.py
   def get_args():
       ...
   def process_user_info(...):
       ...
   
   # parteA.py y parteB.py
   from utils import get_args, process_user_info
   ```

3. **Documenta versión** → README
   ```
   Requiere Python 3.8+
   ```

4. **Verifica minimalidad** → Valida si greedy alcanza 4
   ```python
   # Si no alcanza 4, considera backtracking
   ```

5. **Nota el detalle** → JSON malformado del enunciado
   ```
   README: "Nota: El JSON del ejemplo tiene un formato inválido..."
   ```

---

## PUNTAJE FINAL

| Componente | Puntaje |
|-----------|---------|
| Documentación | 2/3 |
| Usabilidad | 4/6 |
| Calidad de Código | 7/10 |
| Eficacia | 3/4 |
| **TOTAL** | **18/23** |

**Nivel:** 🟢 Junior  
**Recomendación:** Aplicar mejoras sugeridas para alcanzar Semi-Senior
