"""
RF-02A: Validador de Parte A
Compara el JSON output del candidato contra el resultado esperado.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field


# Resultado esperado (extraído del Manual de Corrección)
EXPECTED_OUTPUT = {
    "auth_module": {
        "authn.provider_1": ["./u17.json", "./u19.json", "./u3.json", "./u4.json"],
        "authn.provider_2": ["./u1.json", "./u10.json", "./u13.json", "./u14.json", "./u16.json", "./u18.json", "./u6.json", "./u8.json"],
        "authn.provider_3": ["./u0.json", "./u11.json", "./u12.json", "./u15.json", "./u7.json"],
        "authn.provider_4": ["./u2.json", "./u5.json", "./u9.json"],
    },
    "content_module": {
        "authz.provider_1": ["./u14.json", "./u4.json"],
        "authz.provider_2": ["./u13.json", "./u15.json", "./u16.json", "./u17.json", "./u8.json", "./u9.json"],
        "authz.provider_3": ["./u10.json", "./u11.json", "./u18.json", "./u2.json", "./u3.json", "./u5.json"],
        "authz.provider_4": ["./u0.json", "./u1.json", "./u12.json", "./u19.json", "./u6.json", "./u7.json"],
    },
}


@dataclass
class PartAResult:
    passed: bool = False
    is_valid_json: bool = False
    has_correct_structure: bool = False
    auth_module_correct: bool = False
    content_module_correct: bool = False
    missing_providers: list = field(default_factory=list)
    wrong_users: dict = field(default_factory=dict)  # provider -> {missing, extra}
    output_matches_format: bool = False  # ¿usó comillas y comas correctas?
    raw_output: str = ""
    parsed_output: dict = field(default_factory=dict)
    error: str = ""

    def summary(self) -> str:
        lines = ["=== Parte A ==="]
        lines.append(f"  JSON válido:          {'✅' if self.is_valid_json else '❌'}")
        lines.append(f"  Estructura correcta:  {'✅' if self.has_correct_structure else '❌'}")
        lines.append(f"  auth_module OK:       {'✅' if self.auth_module_correct else '❌'}")
        lines.append(f"  content_module OK:    {'✅' if self.content_module_correct else '❌'}")
        lines.append(f"  Resultado FINAL:      {'✅ CORRECTO' if self.passed else '❌ INCORRECTO'}")
        if self.missing_providers:
            lines.append(f"  Providers faltantes:  {self.missing_providers}")
        if self.wrong_users:
            for provider, diff in self.wrong_users.items():
                if diff.get("missing"):
                    lines.append(f"  [{provider}] faltan: {diff['missing']}")
                if diff.get("extra"):
                    lines.append(f"  [{provider}] sobran: {diff['extra']}")
        if self.error:
            lines.append(f"  Error: {self.error}")
        return "\n".join(lines)


def _normalize_users(users: list) -> set:
    """Normaliza la lista de usuarios para comparación flexible.
    Acepta './u0.json', 'u0.json', 'u0', etc.
    """
    normalized = set()
    for u in users:
        name = Path(u).stem  # 'u0'
        normalized.add(name)
    return normalized


def _compare_module(candidate: dict, expected: dict) -> tuple[bool, list, dict]:
    """
    Compara un módulo (auth o content) entre candidato y esperado.
    Retorna (ok, providers_faltantes, diffs_por_provider)
    """
    missing_providers = []
    wrong_users = {}
    ok = True

    for provider, expected_users in expected.items():
        if provider not in candidate:
            missing_providers.append(provider)
            ok = False
            continue

        expected_set = _normalize_users(expected_users)
        candidate_set = _normalize_users(candidate[provider])

        missing = list(expected_set - candidate_set)
        extra = list(candidate_set - expected_set)

        if missing or extra:
            wrong_users[provider] = {}
            if missing:
                wrong_users[provider]["missing"] = missing
            if extra:
                wrong_users[provider]["extra"] = extra
            ok = False

    return ok, missing_providers, wrong_users


def validate(candidate_output: str) -> PartAResult:
    """
    Valida el output de la Parte A del candidato.

    Args:
        candidate_output: string con el JSON producido por el candidato
                          (puede venir de stdout, un archivo, etc.)

    Returns:
        PartAResult con el resultado detallado
    """
    result = PartAResult(raw_output=candidate_output)

    # 1. ¿Es JSON válido?
    # Nota: la letra original tiene un "detalle" — el JSON de ejemplo no tiene
    # comas al final de línea. Si el candidato lo nota y lo corrige, es un +.
    try:
        parsed = json.loads(candidate_output)
        result.is_valid_json = True
        result.parsed_output = parsed
    except json.JSONDecodeError as e:
        result.is_valid_json = False
        result.error = f"JSON inválido: {e}"
        return result

    # 2. ¿Tiene la estructura correcta? (auth_module + content_module)
    has_auth = "auth_module" in parsed
    has_content = "content_module" in parsed
    result.has_correct_structure = has_auth and has_content

    if not result.has_correct_structure:
        missing_keys = []
        if not has_auth:
            missing_keys.append("auth_module")
        if not has_content:
            missing_keys.append("content_module")
        result.error = f"Faltan claves en el output: {missing_keys}"
        return result

    # 3. Comparar auth_module
    auth_ok, auth_missing, auth_wrong = _compare_module(
        parsed["auth_module"], EXPECTED_OUTPUT["auth_module"]
    )
    result.auth_module_correct = auth_ok
    result.missing_providers.extend(auth_missing)
    result.wrong_users.update(auth_wrong)

    # 4. Comparar content_module
    content_ok, content_missing, content_wrong = _compare_module(
        parsed["content_module"], EXPECTED_OUTPUT["content_module"]
    )
    result.content_module_correct = content_ok
    result.missing_providers.extend(content_missing)
    result.wrong_users.update(content_wrong)

    # 5. Resultado final
    result.passed = auth_ok and content_ok

    return result


def validate_from_file(path: str) -> PartAResult:
    """Lee el output desde un archivo y valida."""
    try:
        content = Path(path).read_text(encoding="utf-8")
        return validate(content)
    except FileNotFoundError:
        r = PartAResult()
        r.error = f"Archivo no encontrado: {path}"
        return r


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python part_a.py <archivo_output.json>")
        print("     python part_a.py --stdin   (lee desde stdin)")
        sys.exit(1)

    if sys.argv[1] == "--stdin":
        raw = sys.stdin.read()
        result = validate(raw)
    else:
        result = validate_from_file(sys.argv[1])

    print(result.summary())
    sys.exit(0 if result.passed else 1)
