"""
SCA — Sistema de Corrección Automatizada
Punto de entrada principal.

Uso:
    python -m sca.main --solution ./ruta/candidato --part-a output_a.json --part-b "['./u0.json', './u4.json']"
    python -m sca.main --help
"""

import argparse
import sys
import os
from pathlib import Path

from .validators.part_a import validate as validate_a, validate_from_file as validate_a_from_file
from .validators.part_b import validate as validate_b, validate_from_string as validate_b_from_string
from .analyzer.ai_analyzer import analyze_from_directory, AIAnalysisResult
from .scoring.engine import ScoringResult

DATA_DIR = str(Path(__file__).parent.parent / "datos prueba tecnica")


def run(
    solution_dir: str | None = None,
    part_a_output: str | None = None,
    part_b_output: str | None = None,
    api_key: str | None = None,
    skip_ai: bool = False,
    output_asana: bool = False,
) -> ScoringResult:
    """
    Corre el SCA sobre la solución de un candidato.

    Args:
        solution_dir:  carpeta con el código fuente del candidato
        part_a_output: ruta a un .json con el output de la Parte A, o el string JSON directamente
        part_b_output: lista de usuarios (string) para la Parte B
        api_key:       Anthropic API key (si None, usa ANTHROPIC_API_KEY env var)
        skip_ai:       si True, omite el análisis de IA (solo validación determinista)
        output_asana:  si True, imprime el texto listo para Asana al final
    """

    print("\n🔍 SCA — Iniciando análisis...\n")

    # ── Parte A ──────────────────────────────────────────────────────────────
    part_a_result = None
    if part_a_output:
        print("  [1/3] Validando Parte A...")
        path = Path(part_a_output)
        if path.exists():
            part_a_result = validate_a_from_file(str(path))
        else:
            # Tratar como string JSON directo
            part_a_result = validate_a(part_a_output)
        print(part_a_result.summary())
    else:
        print("  [1/3] Parte A: no se proporcionó output → saltando")

    # ── Parte B ──────────────────────────────────────────────────────────────
    part_b_result = None
    if part_b_output:
        print("\n  [2/3] Validando Parte B...")
        part_b_result = validate_b_from_string(part_b_output, DATA_DIR)
        print(part_b_result.summary())
    else:
        print("  [2/3] Parte B: no se proporcionó output → saltando")

    # ── Análisis de IA ───────────────────────────────────────────────────────
    ai_result = None
    if not skip_ai and solution_dir:
        print("\n  [3/3] Analizando código con IA...")
        validation_summary = _build_validation_summary(part_a_result, part_b_result)
        ai_result = analyze_from_directory(
            solution_dir=solution_dir,
            validation_results=validation_summary,
            api_key=api_key,
        )
        if ai_result.error:
            print(f"  ⚠️  Error en análisis IA: {ai_result.error}")
        else:
            print(ai_result.summary())
    elif skip_ai:
        print("\n  [3/3] Análisis IA: omitido (--skip-ai)")
    else:
        print("\n  [3/3] Análisis IA: no se proporcionó carpeta de solución → saltando")

    # ── Resultado final ──────────────────────────────────────────────────────
    scoring = ScoringResult(
        part_a=part_a_result,
        part_b=part_b_result,
        ai_analysis=ai_result,
    )

    print("\n" + scoring.summary())

    if output_asana:
        print("\n" + "─" * 50)
        print("📋 TEXTO PARA ASANA (copiar desde aquí):")
        print("─" * 50)
        print(scoring.to_asana_text())
        print("─" * 50)

    return scoring


def _build_validation_summary(part_a, part_b) -> str:
    """Construye un resumen de texto de los resultados de validación automática."""
    lines = []
    if part_a:
        lines.append(f"Parte A: {'CORRECTA' if part_a.passed else 'INCORRECTA'}")
        if not part_a.passed:
            if not part_a.is_valid_json:
                lines.append("  - El output no es un JSON válido")
            if part_a.missing_providers:
                lines.append(f"  - Providers faltantes: {part_a.missing_providers}")
            if part_a.wrong_users:
                for prov, diff in part_a.wrong_users.items():
                    if diff.get("missing"):
                        lines.append(f"  - [{prov}] faltan usuarios: {diff['missing']}")
                    if diff.get("extra"):
                        lines.append(f"  - [{prov}] sobran usuarios: {diff['extra']}")
    else:
        lines.append("Parte A: no validada")

    if part_b:
        lines.append(f"Parte B: {'CORRECTA' if part_b.passed else 'INCORRECTA'}")
        lines.append(f"  - Usuarios usados: {part_b.user_count} (óptimo: {part_b.OPTIMAL_COUNT})")
        if not part_b.passed:
            lines.append(f"  - Módulos sin cubrir: {part_b.uncovered_modules}")
        elif part_b.is_minimal:
            lines.append("  - ✅ Set mínimo óptimo encontrado")
        elif part_b.is_acceptable:
            lines.append("  - ✅ Set aceptable (1 usuario extra sobre el óptimo)")
    else:
        lines.append("Parte B: no validada")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="SCA — Sistema de Corrección Automatizada de Pruebas Técnicas"
    )
    parser.add_argument(
        "--solution", "-s",
        help="Carpeta con el código fuente del candidato"
    )
    parser.add_argument(
        "--part-a", "-a",
        help="Output de la Parte A: ruta a un .json o el JSON como string"
    )
    parser.add_argument(
        "--part-b", "-b",
        help="Output de la Parte B: lista de usuarios, ej: \"['./u0.json', './u4.json']\""
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (alternativa a la variable ANTHROPIC_API_KEY)"
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Omitir análisis de IA (solo validación determinista)"
    )
    parser.add_argument(
        "--asana",
        action="store_true",
        help="Imprimir el texto listo para pegar en Asana"
    )

    args = parser.parse_args()

    if not any([args.solution, args.part_a, args.part_b]):
        parser.print_help()
        print("\n⚠️  Debés proporcionar al menos uno de: --solution, --part-a, --part-b")
        sys.exit(1)

    run(
        solution_dir=args.solution,
        part_a_output=args.part_a,
        part_b_output=args.part_b,
        api_key=args.api_key,
        skip_ai=args.skip_ai,
        output_asana=args.asana,
    )


if __name__ == "__main__":
    main()
