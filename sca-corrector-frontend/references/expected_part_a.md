# Parte A — Output esperado (frontend)

La Parte A de la prueba de frontend es **idéntica** a la de backend. El
ground truth está en:

- `$SCA_ROOT/sca/validators/part_a.py` → constante `EXPECTED_OUTPUT`
- `$SCA_ROOT/Prueba tecnica/datos prueba tecnica/` → 20 archivos `u*.json`

## Cómo validar

### Caso 1 — Parte A entregada como script aparte (Node, Python, etc.)

Mismo flow que backend:

```python
import os, sys
sys.path.insert(0, os.environ['SCA_ROOT'])
from sca.validators.part_a import validate

# Suponiendo que el output del candidato está en $SCA_WORK/parte_a.json
with open(f"{os.environ['SCA_WORK']}/parte_a.json") as f:
    raw = f.read()

result = validate(raw)
print(result.summary())
```

Si el validator devuelve `passed=True` → F135 = 1.

### Caso 2 — Parte A calculada in-browser dentro de la app React

El validator estricto no aplica directamente. El corrector debe inspeccionar
manualmente el estado de la UI:

1. Levantar la app del candidato (`npm install && npm run dev`).
2. Para cada combinación de tab nivel 1 (Content_module / Auth_module) y tab
   nivel 2 (cada provider), verificar que la lista de usuarios mostrada
   matchee con el grupo correspondiente de `EXPECTED_OUTPUT`.
3. Si todas las combinaciones matchean → F135 = 1. Si alguna falla → F135 = 0.

Helper para chequear un grupo específico:

```python
import json
from sca.validators.part_a import EXPECTED_OUTPUT

# Lo que la UI debería mostrar al seleccionar Content_module > authz.provider_1
expected_users = EXPECTED_OUTPUT["content_module"]["authz.provider_1"]
# → ['./u14.json', './u4.json']
```

### Casos límite

- **Si la Parte A no existe** (el candidato hardcodeó los usuarios en el
  componente o usó datos ficticios) → F135 = 0 y nivel `no_suficiente`.
- **Si el formato del output es Python dict en vez de JSON** (caso visto en
  qualabs-master de backend): aceptar si los datos son correctos pero
  penalizar F4/F13 según corresponda. No es razón para F135 = 0.
