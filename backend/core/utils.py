"""Safe SQL literals and atomic JSON artifacts."""
import json
import os
from datetime import date, datetime
from pathlib import Path

def sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"

def sql_identifier(value):
    return '"' + str(value).replace('"', '""') + '"'

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
