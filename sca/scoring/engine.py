"""
RF-04: Motor de calificación y nivelación.
Une los resultados de los validadores (A, B) y el análisis de IA.
"""

from dataclasses import dataclass, field
from ..validators.part_a import PartAResult
from ..validators.part_b import PartBResult
from ..analyzer.ai_analyzer import AIAnalysisResult


@dataclass
class ScoringResult:
    # Inputs
    part_a: PartAResult = None
    part_b: PartBResult = None
    ai_analysis: AIAnalysisResult = None

    # Errores críticos (nivel forzado a no_suficiente)
    critical_errors: list = field(default_factory=list)

    # Nivel final (puede diferir del sugerido por IA si hay errores críticos)
    nivel_final: str = ""
    nivel_override: bool = False  # True si el nivel fue forzado por errores críticos

    def __post_init__(self):
        self._compute_nivel()

    def _compute_nivel(self):
        """Determina el nivel final, considerando errores críticos."""
        # Detectar errores críticos (reglas duras del manual)
        if self.part_a and not self.part_a.passed:
            self.critical_errors.append("❗ Parte A incorrecta")

        if self.part_b and not self.part_b.passed:
            self.critical_errors.append("❗ Parte B no cubre todos los módulos")

        if self.ai_analysis and self.ai_analysis.checklist:
            providers_check = (
                self.ai_analysis.checklist
                .get("usabilidad", {})
                .get("no_hardcodea_providers", {})
                .get("score", 1)
            )
            if providers_check == 0:
                self.critical_errors.append("❗ Hardcodea los providers esperados")

        if self.critical_errors:
            self.nivel_final = "no_suficiente"
            self.nivel_override = True
        elif self.ai_analysis:
            self.nivel_final = self.ai_analysis.nivel_sugerido
        else:
            self.nivel_final = "sin_evaluar"

    @property
    def nivel_emoji(self) -> str:
        return {
            "no_suficiente": "🔴",
            "trainee": "🟡",
            "junior": "🟢",
            "semi_senior": "⭐",
        }.get(self.nivel_final, "❓")

    def summary(self) -> str:
        lines = ["=" * 50, "  RESULTADO FINAL — SCA", "=" * 50, ""]

        if self.part_a:
            lines.append(self.part_a.summary())
            lines.append("")

        if self.part_b:
            lines.append(self.part_b.summary())
            lines.append("")

        if self.critical_errors:
            lines.append("🚨 ERRORES CRÍTICOS detectados:")
            for err in self.critical_errors:
                lines.append(f"   {err}")
            lines.append("")

        if self.ai_analysis and not self.ai_analysis.error:
            lines.append(self.ai_analysis.summary())
            lines.append("")

        lines.append("=" * 50)
        lines.append(f"  NIVEL FINAL: {self.nivel_emoji} {self.nivel_final.replace('_', ' ').upper()}")
        if self.nivel_override and self.ai_analysis and self.ai_analysis.nivel_sugerido:
            lines.append(f"  (IA sugería: {self.ai_analysis.nivel_sugerido} — sobreescrito por errores críticos)")
        lines.append("=" * 50)

        return "\n".join(lines)

    def to_asana_text(self) -> str:
        """Texto final listo para pegar en Asana."""
        if self.ai_analysis and not self.ai_analysis.error:
            text = self.ai_analysis.to_asana_text()
            if self.nivel_override:
                # Reemplazar el nivel en el texto
                text = text.replace(
                    self.ai_analysis.nivel_sugerido.replace("_", " ").title(),
                    f"{self.nivel_final.replace('_', ' ').title()} (forzado por errores críticos)",
                    1,
                )
            return text
        else:
            # Fallback sin análisis de IA
            lines = [
                f"Nivel: {self.nivel_emoji} {self.nivel_final.replace('_', ' ').title()}",
                "",
                "Validación automática:",
            ]
            if self.part_a:
                lines.append(f"  Parte A: {'✅' if self.part_a.passed else '❌'}")
            if self.part_b:
                lines.append(f"  Parte B: {'✅' if self.part_b.passed else '❌'}")
            if self.critical_errors:
                lines.append("\nErrores críticos:")
                for err in self.critical_errors:
                    lines.append(f"  {err}")
            return "\n".join(lines)
