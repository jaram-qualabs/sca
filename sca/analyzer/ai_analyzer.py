"""
RF-03 + RF-05: Analizador de código con IA (Claude API)
Evalúa la calidad del código del candidato y genera el reporte final.

El prompt que se envía a Claude se construye a partir del SKILL.md — la fuente
de verdad única para los criterios y guías de corrección. Si el SKILL.md se
actualiza, el prompt cambia automáticamente en el próximo build de la imagen.

Orden de búsqueda del SKILL.md:
  1. Variable de entorno SKILL_MD_PATH
  2. sca-corrector/SKILL.md relativo a la raíz del proyecto
  3. Prompt de fallback hardcodeado (solo para tests sin el repo completo)
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


# ─── Ubicación del SKILL.md ───────────────────────────────────────────────────

def _find_skill_md() -> Path | None:
    """Localiza el SKILL.md en el filesystem."""
    # 1. Variable de entorno explícita (útil en el contenedor Docker)
    env_path = os.environ.get("SKILL_MD_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    # 2. Relativo a este archivo: sca/analyzer/ → ../../sca-corrector/SKILL.md
    candidates = [
        Path(__file__).parent.parent.parent / "sca-corrector" / "SKILL.md",
        Path("/home/sca/sca-corrector/SKILL.md"),  # ruta en el contenedor Docker
    ]
    for p in candidates:
        if p.exists():
            return p

    return None


def _load_skill_md() -> str:
    """Carga el contenido del SKILL.md o retorna string vacío."""
    path = _find_skill_md()
    if path:
        return path.read_text(encoding="utf-8")
    return ""


def _extract_skill_sections(skill_md: str) -> dict[str, str]:
    """
    Extrae secciones relevantes del SKILL.md para incluir en el prompt.
    Retorna un dict con las secciones clave.
    """
    sections = {}

    # Extraer por encabezados ## Paso N
    paso_pattern = re.compile(r"(## Paso \d+[^\n]*\n)(.*?)(?=\n## |\Z)", re.DOTALL)
    for match in paso_pattern.finditer(skill_md):
        titulo = match.group(1).strip()
        cuerpo = match.group(2).strip()
        sections[titulo] = cuerpo

    return sections


# ─── Criterios del checklist ──────────────────────────────────────────────────
# Mantenemos este dict como referencia estructural para parsear la respuesta
# de Claude. Los textos descriptivos vienen del SKILL.md.

CHECKLIST_CRITERIA = {
    "documentacion": {
        "explica_como_correr": "Explica cómo correr el código (mínimo una línea de comando concreta)",
        "documenta_version_tecnologia": "Documenta la versión de la tecnología en la que programó",
        "explica_decisiones": "Explica cómo funciona, elecciones tomadas, o condiciones particulares",
    },
    "usabilidad": {
        "output_consistente": "El output es consistente (todo por consola o todo por archivos, no mezclado)",
        "parametriza_archivos": "Parametriza los archivos de entrada (no hardcodeado en el código principal)",
        "no_hardcodea_nombres": "No hardcodea nombres de archivos (ej: u0.json, u1.json, etc.)",
        "no_hardcodea_cantidad": "No hardcodea la cantidad de archivos (ej: range(20))",
        "no_hardcodea_providers": "NO hardcodea los providers esperados (authn.provider_1, authz.provider_1, etc.) ❗CRÍTICO",
        "imprime_formato_correcto": "Imprime la salida con el formato pedido en la letra (JSON válido con comas)",
    },
    "calidad_codigo": {
        "nomenclatura_consistente": "Es consistente con la nomenclatura (camelCase o snake_case, no mezcla)",
        "comentarios_adecuados": "Los comentarios son adecuados (dicen cosas útiles, no obviedades)",
        "sin_comentarios_excesivos": "No hay comentarios excesivos ni código comentado",
        "sigue_convenciones": "Escribe de acuerdo a las convenciones de la tecnología usada",
        "divide_en_funciones": "Divide el problema en funciones pequeñas y concretas",
        "no_repite_codigo_parte_a": "No repite el código de la Parte A en la Parte B (reutiliza)",
        "sin_codigo_duplicado": "No hay código duplicado dentro de cada parte ❗",
        "indentacion_correcta": "No tiene código mal indentado",
        "formato_regular": "No tiene formato irregular (espacios o saltos de línea innecesarios)",
        "tiene_error_handling": "Tiene manejo de errores (try/except, validaciones de input)",
    },
    "eficacia": {
        "parte_a_correcta": "Parte A correcta (se completa automáticamente con el validador)",
        "parte_b_cubre_modulos": "Consigue un set de usuarios que cubre todos los módulos",
        "busca_set_reducido": "Busca un set reducido (no devuelve todos los usuarios)",
        "asegura_set_minimo": "😀 Asegura el set mínimo posible (backtracking, combinatoria, etc.)",
    },
}

_PROMPT_FALLBACK = """
NIVELES:
- No suficiente: Parte A incorrecta, Parte B no cubre módulos, o hardcodea providers.
- Trainee: más de 6h, documentación muy básica, código difícil de leer.
- Junior: menos de 6h, documentación con comando + versión, organiza en funciones.
- Semi Senior: menos de 4h, explica decisiones técnicas, código limpio con error handling.
"""


def _build_prompt(
    validation_results: str,
    candidate_code: str,
    readme_content: str,
    time_reported: str,
) -> str:
    """
    Construye el prompt para Claude leyendo el SKILL.md como fuente de verdad.
    Si el SKILL.md no está disponible, usa el fallback hardcodeado.
    """
    skill_md = _load_skill_md()

    if skill_md:
        # Usamos el SKILL.md completo como contexto de instrucciones.
        # Solo extraemos las secciones de análisis y criterios (Pasos 5-9),
        # omitiendo los pasos de setup (1-4) que son operativos, no evaluativos.
        sections = _extract_skill_sections(skill_md)
        evaluation_steps = "\n\n".join(
            f"{titulo}\n{cuerpo}"
            for titulo, cuerpo in sections.items()
            if any(n in titulo for n in ["Paso 6", "Paso 7", "Paso 8", "Paso 9"])
        )
        instructions_block = evaluation_steps if evaluation_steps else skill_md
        skill_source = f"# Instrucciones de corrección (desde SKILL.md)\n\n{instructions_block}"
    else:
        skill_source = f"# Criterios de evaluación\n{_PROMPT_FALLBACK}"

    return f"""Sos un evaluador técnico senior en Qualabs. Tu tarea es analizar el código de un candidato que resolvió una prueba técnica de programación y producir una evaluación estructurada en JSON.

{skill_source}

---

## Datos del candidato a evaluar

### Resultados de validación automática (ya ejecutados y verificados)
{validation_results}

### Código fuente del candidato
{candidate_code}

### README / Documentación del candidato
{readme_content or "(Sin README)"}

### Tiempo reportado por el candidato
{time_reported}

---

## Formato de respuesta requerido

Respondé ÚNICAMENTE con un JSON válido con esta estructura. No agregues texto antes ni después.

{{
  "checklist": {{
    "documentacion": {{
      "explica_como_correr": {{"score": 0, "note": "..."}},
      "documenta_version_tecnologia": {{"score": 0, "note": "..."}},
      "explica_decisiones": {{"score": 0, "note": "..."}}
    }},
    "usabilidad": {{
      "output_consistente": {{"score": 0, "note": "..."}},
      "parametriza_archivos": {{"score": 0, "note": "..."}},
      "no_hardcodea_nombres": {{"score": 0, "note": "..."}},
      "no_hardcodea_cantidad": {{"score": 0, "note": "..."}},
      "no_hardcodea_providers": {{"score": 0, "note": "..."}},
      "imprime_formato_correcto": {{"score": 0, "note": "..."}}
    }},
    "calidad_codigo": {{
      "nomenclatura_consistente": {{"score": 0, "note": "..."}},
      "comentarios_adecuados": {{"score": 0, "note": "..."}},
      "sin_comentarios_excesivos": {{"score": 0, "note": "..."}},
      "sigue_convenciones": {{"score": 0, "note": "..."}},
      "divide_en_funciones": {{"score": 0, "note": "..."}},
      "no_repite_codigo_parte_a": {{"score": 0, "note": "..."}},
      "sin_codigo_duplicado": {{"score": 0, "note": "..."}},
      "indentacion_correcta": {{"score": 0, "note": "..."}},
      "formato_regular": {{"score": 0, "note": "..."}},
      "tiene_error_handling": {{"score": 0, "note": "..."}}
    }},
    "eficacia": {{
      "parte_a_correcta": {{"score": 0, "note": "Ya validado automáticamente"}},
      "parte_b_cubre_modulos": {{"score": 0, "note": "Ya validado automáticamente"}},
      "busca_set_reducido": {{"score": 0, "note": "..."}},
      "asegura_set_minimo": {{"score": 0, "note": "..."}}
    }}
  }},
  "nivel_sugerido": "no_suficiente|trainee|junior|semi_senior",
  "nivel_justificacion": "Explicación de 2-3 oraciones del nivel asignado.",
  "aspectos_destacados": [
    {{"tipo": "positivo|negativo", "descripcion": "..."}}
  ],
  "feedback_candidato": "Feedback constructivo para enviar al candidato. 3-5 oraciones en español."
}}

Para cada criterio: score 1 = cumple, 0 = no cumple. Sé específico en las notas, citá líneas o fragmentos concretos.
"""


@dataclass
class AIAnalysisResult:
    checklist: dict = field(default_factory=dict)
    nivel_sugerido: str = ""
    nivel_justificacion: str = ""
    aspectos_destacados: list = field(default_factory=list)
    feedback_candidato: str = ""
    raw_response: str = ""
    error: str = ""

    @property
    def nivel_emoji(self) -> str:
        return {
            "no_suficiente": "🔴",
            "trainee": "🟡",
            "junior": "🟢",
            "semi_senior": "⭐",
        }.get(self.nivel_sugerido, "❓")

    def get_total_score(self) -> tuple[int, int]:
        """Retorna (puntos_obtenidos, total_posible)"""
        total = 0
        obtained = 0
        for category in self.checklist.values():
            for criterion in category.values():
                total += 1
                obtained += criterion.get("score", 0)
        return obtained, total

    def summary(self) -> str:
        obtained, total = self.get_total_score()
        lines = [
            "=== Análisis de Código (IA) ===",
            f"  Nivel sugerido: {self.nivel_emoji} {self.nivel_sugerido.replace('_', ' ').title()}",
            f"  Puntaje total:  {obtained}/{total}",
            "",
        ]

        category_names = {
            "documentacion": "📚 Documentación",
            "usabilidad": "󰞦 Usabilidad",
            "calidad_codigo": "🍝 Calidad del código",
            "eficacia": "🛠 Eficacia y Eficiencia",
        }

        for cat_key, cat_data in self.checklist.items():
            lines.append(f"  {category_names.get(cat_key, cat_key)}")
            for criterion_key, criterion_data in cat_data.items():
                score = criterion_data.get("score", 0)
                note = criterion_data.get("note", "")
                icon = "✅" if score else "❌"
                lines.append(f"    {icon} {criterion_key}")
                if note and note != "Ya validado automáticamente":
                    lines.append(f"       → {note}")
            lines.append("")

        if self.aspectos_destacados:
            lines.append("  ⭐ Aspectos destacados:")
            for aspecto in self.aspectos_destacados:
                tipo = aspecto.get("tipo", "")
                desc = aspecto.get("descripcion", "")
                icon = "(+)" if tipo == "positivo" else "(-)"
                lines.append(f"    {icon} {desc}")
            lines.append("")

        lines.append(f"  🎚 Nivel: {self.nivel_justificacion}")
        lines.append("")
        lines.append("  🎁 Feedback para el candidato:")
        lines.append(f"  {self.feedback_candidato}")

        return "\n".join(lines)

    def to_asana_text(self) -> str:
        """Genera el texto formateado listo para copiar en Asana."""
        obtained, total = self.get_total_score()
        lines = [
            f"Nivel: {self.nivel_emoji} {self.nivel_sugerido.replace('_', ' ').title()}",
            f"Puntaje: {obtained}/{total}",
            "",
        ]

        category_names = {
            "documentacion": "📚 Documentación",
            "usabilidad": "󰞦 Usabilidad",
            "calidad_codigo": "🍝 Calidad del código",
            "eficacia": "🛠 Eficacia y Eficiencia",
        }

        criteria_labels = {k: v for cat in CHECKLIST_CRITERIA.values() for k, v in cat.items()}

        for cat_key, cat_data in self.checklist.items():
            lines.append(category_names.get(cat_key, cat_key))
            for criterion_key, criterion_data in cat_data.items():
                score = criterion_data.get("score", 0)
                label = criteria_labels.get(criterion_key, criterion_key)
                icon = "✅" if score else "❌"
                lines.append(f"{icon} {label}")
            lines.append("")

        if self.aspectos_destacados:
            lines.append("⭐ Aspectos que destacan:")
            for aspecto in self.aspectos_destacados:
                tipo = aspecto.get("tipo", "")
                desc = aspecto.get("descripcion", "")
                icon = "(+)" if tipo == "positivo" else "(-)"
                lines.append(f"{icon} {desc}")
            lines.append("")

        lines.append("📝 Otras notas:")
        lines.append(self.nivel_justificacion)
        lines.append("")
        lines.append("🎁 Feedback:")
        lines.append(self.feedback_candidato)

        return "\n".join(lines)


def _call_claude_api(prompt: str, api_key: str) -> str:
    """Llama a la API de Anthropic usando urllib (sin dependencias externas)."""
    import urllib.request
    import urllib.error

    body = json.dumps({
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        data = json.loads(response.read())
        return data["content"][0]["text"]


def analyze(
    candidate_code: str,
    readme_content: str,
    validation_results: str,
    time_reported: str = "No reportado",
    api_key: str | None = None,
) -> AIAnalysisResult:
    """
    Analiza el código del candidato usando Claude API.

    Args:
        candidate_code: código fuente completo del candidato
        readme_content: contenido del README o documentación
        validation_results: resumen de los resultados de Part A y Part B
        time_reported: tiempo que el candidato reportó haber tardado
        api_key: Anthropic API key (si None, busca en ANTHROPIC_API_KEY env var)

    Returns:
        AIAnalysisResult con la evaluación completa
    """
    result = AIAnalysisResult()
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    if not key:
        result.error = "ANTHROPIC_API_KEY no configurada"
        return result

    skill_path = _find_skill_md()
    if skill_path:
        print(f"  📄 SKILL.md cargado desde: {skill_path}", flush=True)
    else:
        print("  ⚠️  SKILL.md no encontrado — usando prompt de fallback", flush=True)

    prompt = _build_prompt(
        validation_results=validation_results,
        candidate_code=candidate_code,
        readme_content=readme_content,
        time_reported=time_reported,
    )

    try:
        raw = _call_claude_api(prompt, key)
        result.raw_response = raw

        # Parsear JSON de la respuesta
        # Claude puede devolver el JSON dentro de ```json ... ```
        json_str = raw.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])

        parsed = json.loads(json_str)
        result.checklist = parsed.get("checklist", {})
        result.nivel_sugerido = parsed.get("nivel_sugerido", "")
        result.nivel_justificacion = parsed.get("nivel_justificacion", "")
        result.aspectos_destacados = parsed.get("aspectos_destacados", [])
        result.feedback_candidato = parsed.get("feedback_candidato", "")

    except json.JSONDecodeError as e:
        result.error = f"Error parseando respuesta de Claude: {e}\nRespuesta: {raw[:500]}"
    except Exception as e:
        result.error = f"Error llamando a Claude API: {e}"

    return result


def analyze_from_directory(
    solution_dir: str,
    validation_results: str,
    api_key: str | None = None,
) -> AIAnalysisResult:
    """
    Lee todos los archivos de código del directorio del candidato y analiza.

    Args:
        solution_dir: carpeta con la solución del candidato
        validation_results: resumen de validación automática (de part_a y part_b)
        api_key: Anthropic API key
    """
    solution_path = Path(solution_dir)
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".cs"}
    readme_extensions = {".md", ".txt", ".rst"}

    code_parts = []
    readme_content = ""
    time_reported = "No reportado"

    for filepath in sorted(solution_path.rglob("*")):
        if filepath.is_dir():
            continue

        # Ignorar node_modules, .git, __pycache__, etc.
        if any(part in filepath.parts for part in ["node_modules", ".git", "__pycache__", ".venv", "venv"]):
            continue

        ext = filepath.suffix.lower()
        relative = filepath.relative_to(solution_path)

        if ext in readme_extensions:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            readme_content += f"\n\n### {relative}\n{content}"
            # Buscar tiempo reportado
            for line in content.lower().split("\n"):
                if any(word in line for word in ["hora", "hour", "minuto", "minute", "tardé", "tomó", "took"]):
                    time_reported = line.strip()
                    break

        elif ext in code_extensions:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            code_parts.append(f"\n\n### {relative}\n```{ext[1:]}\n{content}\n```")

    candidate_code = "".join(code_parts) if code_parts else "(No se encontró código fuente)"

    return analyze(
        candidate_code=candidate_code,
        readme_content=readme_content,
        validation_results=validation_results,
        time_reported=time_reported,
        api_key=api_key,
    )
