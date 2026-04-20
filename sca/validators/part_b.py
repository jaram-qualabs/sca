"""
RF-02B: Validador de Parte B
Verifica que el set de usuarios elegido por el candidato cubre todos los módulos.
Basado en la lógica de verificador.py del manual.
"""

import json
import glob
import os
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class PartBResult:
    passed: bool = False
    covers_all_modules: bool = False
    user_count: int = 0
    is_minimal: bool = False        # ¿usó 4 usuarios (óptimo)?
    is_acceptable: bool = False     # ¿usó 5 o menos (aceptable)?
    uncovered_modules: list = field(default_factory=list)
    candidate_users: list = field(default_factory=list)
    error: str = ""

    # El óptimo conocido para este dataset es 4 usuarios
    OPTIMAL_COUNT = 4
    ACCEPTABLE_COUNT = 5

    def summary(self) -> str:
        lines = ["=== Parte B ==="]
        lines.append(f"  Usuarios elegidos:    {self.user_count} → {self.candidate_users}")
        lines.append(f"  Cubre todos módulos:  {'✅' if self.covers_all_modules else '❌'}")
        if self.covers_all_modules:
            if self.is_minimal:
                lines.append(f"  Set mínimo (óptimo):  ✅😀 ({self.OPTIMAL_COUNT} usuarios)")
            elif self.is_acceptable:
                lines.append(f"  Set reducido:         ✅ ({self.user_count} usuarios, óptimo={self.OPTIMAL_COUNT})")
            else:
                lines.append(f"  Set reducido:         ⚠️  ({self.user_count} usuarios, óptimo={self.OPTIMAL_COUNT})")
        if self.uncovered_modules:
            lines.append(f"  Módulos sin cubrir:   {self.uncovered_modules}")
        lines.append(f"  Resultado FINAL:      {'✅ CORRECTO' if self.passed else '❌ INCORRECTO'}")
        if self.error:
            lines.append(f"  Error: {self.error}")
        return "\n".join(lines)


def _load_module_map(json_dir: str) -> tuple[dict, dict]:
    """
    Lee todos los .json de la carpeta y construye:
    - user_to_modules: { 'u0.json': ['authz.provider_4', 'authn.provider_3'] }
    - modules: { 'authz.provider_4': ['u0.json', ...] }  (qué usuarios usan cada módulo)
    """
    user_to_modules = {}
    modules = defaultdict(list)

    for filepath in glob.glob(os.path.join(json_dir, "*.json")):
        filename = os.path.basename(filepath)
        with open(filepath, "r") as f:
            data = json.load(f)

        content = data["provider"]["content_module"]
        auth = data["provider"]["auth_module"]

        user_to_modules[filename] = [content, auth]
        modules[content].append(filename)
        modules[auth].append(filename)

    return user_to_modules, dict(modules)


def _normalize_user(user: str) -> str:
    """Convierte './u0.json', 'u0', 'u0.json' → 'u0.json'"""
    name = Path(user).stem   # 'u0'
    return f"{name}.json"


def validate(candidate_users: list, json_dir: str) -> PartBResult:
    """
    Valida el output de la Parte B.

    Args:
        candidate_users: lista de usuarios elegidos por el candidato,
                         ej: ['./u18.json', './u9.json', './u0.json', './u4.json']
        json_dir: carpeta donde están los archivos u*.json de prueba

    Returns:
        PartBResult con el resultado detallado
    """
    result = PartBResult()

    # Normalizar usuarios del candidato
    normalized = [_normalize_user(u) for u in candidate_users]
    result.candidate_users = normalized
    result.user_count = len(normalized)

    # Cargar mapa de módulos
    try:
        user_to_modules, all_modules = _load_module_map(json_dir)
    except Exception as e:
        result.error = f"Error leyendo archivos JSON: {e}"
        return result

    if not all_modules:
        result.error = "No se encontraron archivos .json en el directorio"
        return result

    # Verificar cobertura: para cada usuario elegido, "tachar" sus módulos
    remaining_modules = set(all_modules.keys())

    for user in normalized:
        if user not in user_to_modules:
            result.error = f"Usuario no encontrado en los datos: {user}"
            return result
        content_mod, auth_mod = user_to_modules[user]
        remaining_modules.discard(content_mod)
        remaining_modules.discard(auth_mod)

    result.covers_all_modules = len(remaining_modules) == 0
    result.uncovered_modules = list(remaining_modules)
    result.passed = result.covers_all_modules

    # Evaluar eficiencia
    if result.covers_all_modules:
        result.is_minimal = result.user_count <= result.OPTIMAL_COUNT
        result.is_acceptable = result.user_count <= result.ACCEPTABLE_COUNT

    return result


def validate_from_string(candidate_output: str, json_dir: str) -> PartBResult:
    """
    Parsea el output del candidato (puede ser una lista Python o JSON)
    y valida la Parte B.

    Acepta formatos como:
        ['./u18.json', './u9.json', './u0.json', './u4.json']
        ["u18.json", "u9.json"]
    """
    result = PartBResult()
    raw = candidate_output.strip()

    # Intentar parsear como JSON primero
    try:
        users = json.loads(raw)
        if not isinstance(users, list):
            raise ValueError("Se esperaba una lista")
        return validate(users, json_dir)
    except json.JSONDecodeError:
        pass

    # Intentar parsear como lista Python (con eval seguro)
    try:
        import ast
        users = ast.literal_eval(raw)
        if not isinstance(users, list):
            raise ValueError("Se esperaba una lista")
        return validate(users, json_dir)
    except Exception as e:
        result.error = f"No se pudo parsear el output de Parte B: {e}\nOutput recibido: {raw[:200]}"
        return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python part_b.py <json_dir> <output_parte_b>")
        print('  Ej: python part_b.py ./datos "[\'./u18.json\', \'./u9.json\', \'./u0.json\', \'./u4.json\']"')
        sys.exit(1)

    json_dir = sys.argv[1]
    candidate_output = sys.argv[2]

    result = validate_from_string(candidate_output, json_dir)
    print(result.summary())
    sys.exit(0 if result.passed else 1)
