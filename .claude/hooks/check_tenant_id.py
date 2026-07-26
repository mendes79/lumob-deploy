#!/usr/bin/env python3
# .claude/hooks/check_tenant_id.py
import json, sys, re

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")

if not file_path.endswith(".py"):
    sys.exit(0)

with open(file_path, encoding="utf-8") as f:
    content = f.read()

tem_sql = re.search(r"\b(SELECT|UPDATE|DELETE)\b", content, re.IGNORECASE)
tem_filtro_tenant = "tenant_id" in content

if tem_sql and not tem_filtro_tenant:
    print(
        f"O arquivo {file_path} tem uma query SQL sem 'tenant_id' visível no texto. "
        "Confirme se o filtro de tenant está sendo aplicado antes de prosseguir.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)