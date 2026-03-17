"""Tenant CRUD manager backed by JSON files."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from server.config import TENANTS_DIR

TENANTS_INDEX = TENANTS_DIR / "tenants.json"


def _load_tenants() -> list[dict]:
    TENANTS_DIR.mkdir(parents=True, exist_ok=True)
    if not TENANTS_INDEX.exists():
        return []
    return json.loads(TENANTS_INDEX.read_text(encoding="utf-8"))


def _save_tenants(tenants: list[dict]) -> None:
    TENANTS_DIR.mkdir(parents=True, exist_ok=True)
    TENANTS_INDEX.write_text(
        json.dumps(tenants, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def list_tenants() -> list[dict]:
    return _load_tenants()


def get_tenant(tenant_id: str) -> dict | None:
    return next((t for t in _load_tenants() if t["id"] == tenant_id), None)


def create_tenant(name: str, description: str = "") -> dict:
    tenants = _load_tenants()
    tenant = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tenants.append(tenant)
    _save_tenants(tenants)
    # Create tenant data directory
    (TENANTS_DIR / tenant["id"]).mkdir(parents=True, exist_ok=True)
    return tenant


def delete_tenant(tenant_id: str) -> bool:
    tenants = _load_tenants()
    filtered = [t for t in tenants if t["id"] != tenant_id]
    if len(filtered) == len(tenants):
        return False
    _save_tenants(filtered)
    return True


def ensure_default_tenant() -> dict:
    """Ensure a 'default' tenant exists, create if not."""
    tenants = _load_tenants()
    default = next((t for t in tenants if t["id"] == "default"), None)
    if default:
        return default
    tenant = {
        "id": "default",
        "name": "기본 테넌트",
        "description": "기본 규정 문서 컬렉션",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tenants.append(tenant)
    _save_tenants(tenants)
    (TENANTS_DIR / "default").mkdir(parents=True, exist_ok=True)
    return tenant
