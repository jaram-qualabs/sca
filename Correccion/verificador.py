# Correr en la carpeta con todos los *.json
# Ingresar el resultado de la parte B, por ej: ['./u18.json', './u9.json', './u0.json', './u4.json']
# Si esa solucion esta ok, dice "solucion cubre", sino "no cubre"

import glob, os, json, sys
from collections import defaultdict

PATH = '.'

modules = defaultdict(list)
user_to_modules = {}

def read_files(path):
  for filename in glob.glob(os.path.join(path, '*.json')):
    with open(filename, 'r') as f:
      user = os.path.basename(filename)
      r = json.load(f)
      content = r["provider"]["content_module"]
      auth = r["provider"]["auth_module"]
      user_to_modules[user] = [content, auth]
      
      modules[content].append(user)
      modules[auth].append(user)


def verify(users):
  for user in users:
    c, a = user_to_modules[user.removeprefix("./")]
    if c in modules:
      del modules[c]
    if a in modules:
      del modules[a]

if __name__ == "__main__":
  read_files(PATH)
  if len(modules) == 0:
    print("No encontre archivos")
    sys.exit(1)
  users = eval(input("Ingrese resultado parte B: "))
  verify(users)
  if len(modules) == 0:
    print("Solucion cubre!")
  else:
    print("La solucion NO cubre")
