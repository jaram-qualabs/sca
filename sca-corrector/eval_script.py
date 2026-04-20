#!/usr/bin/env python3
import os
import sys
import json
import shutil
from pathlib import Path

# Setup paths
sys.path.insert(0, '/Users/javieraramberri/Projects/SCA')

# Change to candidate directory
os.chdir('/Users/javieraramberri/Projects/SCA/sca-corrector/candidato/pruebatecnica')

# Step 1: Run Parte A
print("=== EJECUTANDO PARTE A ===")
os.system('python3 parteA.py')

# Step 2: Read Parte A output
print("\n=== VALIDANDO PARTE A ===")
try:
    with open('users_by_provider.json', 'r') as f:
        output_a = json.load(f)
    print(f"Parte A output (raw): {json.dumps(output_a, indent=2)[:500]}...")

    # Validate with SCA validator
    from sca.validators.part_a import validate
    output_string = json.dumps(output_a)
    result = validate(output_string)
    print(f"Parte A validation result:")
    print(result.summary())
    parte_a_ok = result.is_valid
    print(f"Parte A correcta: {parte_a_ok}")
except Exception as e:
    print(f"Error running/validating Parte A: {e}")
    import traceback
    traceback.print_exc()
    parte_a_ok = False

# Step 3: Run Parte B
print("\n=== EJECUTANDO PARTE B ===")
try:
    output = os.popen('python3 parteB.py').read()
    print(f"Parte B output: {output}")

    # Validate with SCA validator
    from sca.validators.part_b import validate_from_string
    DATA_DIR = '/Users/javieraramberri/Projects/SCA/datos prueba tecnica'
    result = validate_from_string(output, DATA_DIR)
    print(f"\nParte B validation result:")
    print(result.summary())
    parte_b_ok = result.is_valid
    parte_b_output = output.strip()
    print(f"Parte B correcta: {parte_b_ok}")
except Exception as e:
    print(f"Error running/validating Parte B: {e}")
    import traceback
    traceback.print_exc()
    parte_b_ok = False
    parte_b_output = None

print(f"\n=== RESUMEN INICIAL ===")
print(f"Parte A OK: {parte_a_ok}")
print(f"Parte B OK: {parte_b_ok}")
