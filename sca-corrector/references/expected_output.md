# Resultados Esperados — Prueba Técnica

## Parte A — Output esperado

```json
{
  "auth_module": {
    "authn.provider_1": ["./u17.json", "./u19.json", "./u3.json", "./u4.json"],
    "authn.provider_2": ["./u1.json", "./u10.json", "./u13.json", "./u14.json", "./u16.json", "./u18.json", "./u6.json", "./u8.json"],
    "authn.provider_3": ["./u0.json", "./u11.json", "./u12.json", "./u15.json", "./u7.json"],
    "authn.provider_4": ["./u2.json", "./u5.json", "./u9.json"]
  },
  "content_module": {
    "authz.provider_1": ["./u14.json", "./u4.json"],
    "authz.provider_2": ["./u13.json", "./u15.json", "./u16.json", "./u17.json", "./u8.json", "./u9.json"],
    "authz.provider_3": ["./u10.json", "./u11.json", "./u18.json", "./u2.json", "./u3.json", "./u5.json"],
    "authz.provider_4": ["./u0.json", "./u1.json", "./u12.json", "./u19.json", "./u6.json", "./u7.json"]
  }
}
```

**Nota de validación:** El orden de los usuarios dentro de cada provider no importa. Lo que importa es que estén todos los usuarios correctos en el provider correcto. Usá el validador para comparar, que normaliza los nombres (acepta `./u0.json`, `u0.json`, `u0`, etc.).

## Parte B — Output esperado

El set mínimo óptimo es de **4 usuarios**: `['./u18.json', './u9.json', './u0.json', './u4.json']`

Otros sets de 4 usuarios también pueden ser válidos si cubren todos los módulos.
Un set de **5 usuarios** es aceptable (1 punto sobre el óptimo).
Más de 5 usuarios es correcto pero no eficiente.

**Módulos que deben quedar cubiertos (los 8):**
- authn.provider_1, authn.provider_2, authn.provider_3, authn.provider_4
- authz.provider_1, authz.provider_2, authz.provider_3, authz.provider_4

Usá el validador para verificar:
```python
from sca.validators.part_b import validate_from_string
result = validate_from_string(output_candidato, '/Users/javieraramberri/Projects/SCA/datos prueba tecnica')
```

## Datos de prueba

Los 20 archivos JSON están en:
`/Users/javieraramberri/Projects/SCA/datos prueba tecnica/`

Cada archivo tiene esta estructura:
```json
{"name": "User X", "provider": {"content_module": "authz.provider_N", "auth_module": "authn.provider_M"}}
```
