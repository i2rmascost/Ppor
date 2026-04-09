# --- THE AXIOM: YAML Schema Validator ---
# พิกัด: tests/test_yaml_schema.py

import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

# โครงสร้างกฎหมายมหาภพ (Axiom Strict Schema)
OVERRIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "global_config": {
            "type": "object",
            "properties": {
                "default_timeout": {"type": "integer"},
                "blacklist_values": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            }
        },
        "overrides": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_-]+$": {
                    "type": "object",
                    "properties": {
                        "name_th": {"type": "string"},
                        "engine": {"type": "string", "enum": ["httpx", "playwright"]},
                        "css": {"type": "string"},
                        "xpath": {"type": "string"},
                        "regex_fallback": {"type": "string"},
                        "wait_for": {"type": "integer"}
                    },
                    # ต้องมีอย่างน้อย 1 วิธีในการมุดข้อมูล
                    "anyOf": [
                        {"required": ["css"]},
                        {"required": ["xpath"]},
                        {"required": ["regex_fallback"]}
                    ]
                }
            },
            "additionalProperties": False
        }
    },
    "required": ["overrides"]
}

def test_selector_overrides_schema():
    target_path = Path("data/selector_overrides.yaml")
    
    # 1. ตรวจสอบการมีอยู่ของไฟล์
    assert target_path.exists(), f"Critical: {target_path} is missing."
    
    # 2. ตรวจสอบ YAML Syntax
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        pytest.fail(f"YAML Syntax Error: {exc}")
        
    # 3. ตรวจสอบ Schema Validation
    try:
        validate(instance=data, schema=OVERRIDE_SCHEMA)
    except ValidationError as e:
        pytest.fail(f"Schema Violation in {e.json_path}: {e.message}")

def test_blacklist_integrity():
    with open("data/selector_overrides.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    blacklist = data.get("global_config", {}).get("blacklist_values", [])
    # กฎ: ต้องมีเลขป้องกันการหลอกลวงพื้นฐาน
    assert 60000.0 in blacklist, "Security Warning: 60000.0 missing from blacklist"
    assert 0.0 in blacklist, "Security Warning: 0.0 missing from blacklist"