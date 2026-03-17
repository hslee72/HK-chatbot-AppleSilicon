"""Tenant management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.tenants.manager import (
    list_tenants,
    get_tenant,
    create_tenant,
    delete_tenant,
    ensure_default_tenant,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


class CreateTenantRequest(BaseModel):
    name: str
    description: str = ""


@router.get("")
async def get_tenants():
    ensure_default_tenant()
    return list_tenants()


@router.post("")
async def post_tenant(req: CreateTenantRequest):
    return create_tenant(req.name, req.description)


@router.get("/{tenant_id}")
async def get_tenant_by_id(tenant_id: str):
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.delete("/{tenant_id}")
async def delete_tenant_by_id(tenant_id: str):
    if tenant_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default tenant")
    if not delete_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"ok": True}
