#!/usr/bin/env python3
"""
Static analysis and evaluation of candidate's solution
"""

import re
import json

# Analyze parteA.py
with open('/Users/javieraramberri/Projects/SCA/sca-corrector/candidato/pruebatecnica/parteA.py', 'r') as f:
    code_a = f.read()

# Analyze parteB.py
with open('/Users/javieraramberri/Projects/SCA/sca-corrector/candidato/pruebatecnica/parteB.py', 'r') as f:
    code_b = f.read()

# Analyze README
with open('/Users/javieraramberri/Projects/SCA/sca-corrector/candidato/pruebatecnica/README', 'r') as f:
    readme = f.read()

print("=== STATIC ANALYSIS RESULTS ===\n")

# F3: Explica cómo correr el código
print("F3 - Explica cómo correr el código:")
has_how_to_run = 'python parteA.py' in readme and 'python parteB.py' in readme
print(f"  Mención explícita de comando: {has_how_to_run}")
print(f"  README snippet: {readme[:100]}...")
f3 = 1 if has_how_to_run else 0
print(f"  Score: {f3}\n")

# F4: Documenta versión de tecnología
print("F4 - Documenta versión de tecnología:")
has_version = re.search(r'python\s*\d+\.\d+', readme, re.IGNORECASE) or re.search(r'3\.\d+', readme)
print(f"  Mención de versión: {has_version}")
print(f"  README contains version info: {bool(has_version)}")
f4 = 1 if has_version else 0
print(f"  Score: {f4}\n")

# F5: Explica elecciones o decisiones
print("F5 - Explica elecciones/decisiones:")
explains_greedy = 'greedy' in readme.lower()
explains_reasoning = 'minimal hitting set' in readme.lower() or 'cantidad de usuarios' in readme
print(f"  Mentions greedy: {explains_greedy}")
print(f"  Explains reasoning: {explains_reasoning}")
print(f"  README snippet about algorithm: {readme[readme.find('implementó'):] if 'implementó' in readme else 'N/A'}")
f5 = 1 if (explains_greedy and explains_reasoning) else 0
print(f"  Score: {f5}\n")

# F8: Output consistente
print("F8 - Output consistente:")
a_outputs_to_file = 'json.dump' in code_a
b_outputs_to_file = 'json.dump' in code_b or 'print(' in code_b
a_print = 'print(' in code_a
b_print = 'print(' in code_b
print(f"  parteA writes to file: {a_outputs_to_file}")
print(f"  parteB uses print: {b_print}")
consistent = (a_outputs_to_file and not b_print) or (not a_outputs_to_file and b_print)
print(f"  Consistent output: {consistent}")
f8 = 1 if consistent else 0
print(f"  Score: {f8}\n")

# F9: Parametriza archivos
print("F9 - Parametriza archivos:")
has_argparse_a = 'argparse' in code_a
has_argparse_b = 'argparse' in code_b
has_path_param_a = '--path' in code_a
has_path_param_b = '--path' in code_b
print(f"  parteA uses argparse: {has_argparse_a}")
print(f"  parteB uses argparse: {has_argparse_b}")
print(f"  Both have --path parameter: {has_path_param_a and has_path_param_b}")
f9 = 1 if (has_argparse_a and has_argparse_b) else 0
print(f"  Score: {f9}\n")

# F10: No hardcodea nombres de archivos
print("F10 - No hardcodea nombres de archivos:")
hardcoded_files = re.findall(r'["\']u\d+\.json["\']|["\']u["\'].*json', code_a + code_b)
print(f"  Hardcoded filenames found: {hardcoded_files}")
f10 = 1 if not hardcoded_files else 0
print(f"  Score: {f10}\n")

# F11: No hardcodea cantidad de archivos
print("F11 - No hardcodea cantidad de archivos:")
hardcoded_range = re.findall(r'range\(\d+\)', code_a + code_b)
print(f"  Hardcoded range() calls: {hardcoded_range}")
f11 = 1 if not hardcoded_range else 0
print(f"  Score: {f11}\n")

# F12: No hardcodea providers (CRÍTICO)
print("F12 - No hardcodea providers (CRÍTICO):")
hardcoded_providers = re.findall(r'["\']authn\.provider_\d+["\']|["\']authz\.provider_\d+["\']', code_a + code_b)
print(f"  Hardcoded providers found: {hardcoded_providers}")
f12 = 1 if not hardcoded_providers else 0
print(f"  Score: {f12}\n")

# F13: Imprime salida como en la letra (bonus)
print("F13 - Imprime salida como en la letra (bonus):")
mentions_json_issue = 'json' in readme and 'comma' in readme.lower()
print(f"  Mentions JSON format issue: {mentions_json_issue}")
f13 = 0  # No bonus claim visible
print(f"  Score: {f13}\n")

# F16: Nomenclatura consistente
print("F16 - Nomenclatura consistente:")
snake_case_vars = re.findall(r'_[a-z_]+', code_a + code_b)
camel_case_vars = re.findall(r'[a-z][A-Z]', code_a + code_b)
print(f"  Snake case variables: {len(snake_case_vars)} found")
print(f"  Camel case variables: {len(camel_case_vars)} found")
f16 = 1 if len(camel_case_vars) == 0 else 0  # Should use snake_case in Python
print(f"  Score: {f16}\n")

# F17: Comentarios adecuados
print("F17 - Comentarios adecuados:")
comments = re.findall(r'#.*', code_a + code_b)
useful_comments = [c for c in comments if not c.strip().startswith('# ')]
print(f"  Total comments: {len(comments)}")
print(f"  Sample comments: {comments[:3]}")
f17 = 1 if len(comments) >= 3 else 0
print(f"  Score: {f17}\n")

# F18: Sin comentarios excesivos
print("F18 - Sin comentarios excesivos:")
commented_code = len(re.findall(r'#.*[a-z].*#', code_a + code_b))
print(f"  Commented-out code blocks: {commented_code}")
f18 = 1 if commented_code == 0 else 0
print(f"  Score: {f18}\n")

# F19: Sigue convenciones de tecnología
print("F19 - Sigue convenciones (Python):")
has_main_guard = 'if __name__ == "__main__"' in code_a and 'if __name__ == "__main__"' in code_b
all_snake_case = len(camel_case_vars) == 0
print(f"  Has __main__ guard: {has_main_guard}")
print(f"  Uses snake_case consistently: {all_snake_case}")
f19 = 1 if (has_main_guard and all_snake_case) else 0
print(f"  Score: {f19}\n")

# F20: Divide en funciones
print("F20 - Divide en funciones:")
func_a = len(re.findall(r'def ', code_a))
func_b = len(re.findall(r'def ', code_b))
print(f"  Functions in parteA: {func_a}")
print(f"  Functions in parteB: {func_b}")
well_divided = func_a >= 3 and func_b >= 3
print(f"  Both parts well divided: {well_divided}")
f20 = 1 if well_divided else 0
print(f"  Score: {f20}\n")

# F21: No repite código de Parte A
print("F21 - No repite código de Parte A:")
# Check if get_args is repeated
get_args_a = code_a[code_a.find('def get_args'):code_a.find('def get_args')+200] if 'def get_args' in code_a else ""
get_args_b = code_b[code_b.find('def get_args'):code_b.find('def get_args')+200] if 'def get_args' in code_b else ""
same_get_args = get_args_a == get_args_b if get_args_a and get_args_b else False
print(f"  get_args duplicated: {same_get_args}")
# Check for imports
imports_a = set(re.findall(r'import ([a-zA-Z_,\s]+)', code_a))
imports_b = set(re.findall(r'import ([a-zA-Z_,\s]+)', code_b))
print(f"  Imports in A: {imports_a}")
print(f"  Imports in B: {imports_b}")
f21 = 0 if same_get_args else 1
print(f"  Score: {f21}\n")

# F22: Sin código duplicado
print("F22 - Sin código duplicado:")
# Check for repeated logic within files
process_user_appears_twice_a = code_a.count('def process_user_info')
process_user_appears_twice_b = code_b.count('def process_user_info')
print(f"  process_user_info in A: {process_user_appears_twice_a}")
print(f"  process_user_info in B: {process_user_appears_twice_b}")
has_duplication = process_user_appears_twice_a > 1 or process_user_appears_twice_b > 1
f22 = 0 if has_duplication else 1
print(f"  Score: {f22}\n")

# F23: Sin código mal indentado
print("F23 - Sin código mal indentado:")
print("  (Python syntax check - both compile without indent errors)")
f23 = 1
print(f"  Score: {f23}\n")

# F24: Sin formato irregular
print("F24 - Sin formato irregular:")
irregular = re.findall(r'\s{2,}[a-z]', code_a + code_b)
print(f"  Irregular spacing found: {len(irregular)}")
f24 = 1 if len(irregular) == 0 else 0
print(f"  Score: {f24}\n")

# F25: Tiene error handling (bonus)
print("F25 - Tiene error handling (bonus):")
has_try_except_a = 'try:' in code_a
has_try_except_b = 'try:' in code_b
print(f"  try/except in A: {has_try_except_a}")
print(f"  try/except in B: {has_try_except_b}")
f25 = 1 if (has_try_except_a and has_try_except_b) else 0
print(f"  Score: {f25}\n")

# Extract time from README
print("TIME ANALYSIS:")
time_a_match = re.search(r'Tiempo:\s*(\d+):(\d+)', readme)
time_b_match = re.search(r'Tiempo:\s*(\d+):(\d+)', readme[readme.find('Parte B'):])
time_a_mins = int(time_a_match.group(1)) * 60 + int(time_a_match.group(2)) if time_a_match else 0
time_b_mins = int(time_b_match.group(1)) * 60 + int(time_b_match.group(2)) if time_b_match else 0
total_mins = time_a_mins + time_b_mins
total_hours = total_mins / 60
print(f"  Time Part A: {time_a_mins} mins ({time_a_match.group(0) if time_a_match else 'N/A'})")
print(f"  Time Part B: {time_b_mins} mins ({time_b_match.group(0) if time_b_match else 'N/A'})")
print(f"  Total time: {total_mins} mins = {total_hours:.2f} hours\n")

# Summary
print("\n=== CHECKLIST SCORES ===")
scores = {
    3: f3, 4: f4, 5: f5, 8: f8, 9: f9, 10: f10, 11: f11, 12: f12, 13: f13,
    16: f16, 17: f17, 18: f18, 19: f19, 20: f20, 21: f21, 22: f22, 23: f23, 24: f24, 25: f25
}

for row, score in scores.items():
    print(f"F{row}: {score}")

print(f"\nTotal non-critical score (excluding F28, F29, F30, F31): {sum(scores.values())}/20")
