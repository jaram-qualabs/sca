"""Helpers HTTP directos para Asana.

El conector MCP de Asana no expone `add_attachment`/`upload_attachment`. Este
paquete contiene wrappers minimalistas sobre el REST API de Asana para las
operaciones que el conector MCP no cubre. Usa Personal Access Token (PAT)
seteado como env var `ASANA_PAT`. No reemplaza al conector — convive con él.

Hoy solo cubre attachments. Si en el futuro hace falta otra operación que
el MCP tampoco expone, sumá un módulo acá.
"""
