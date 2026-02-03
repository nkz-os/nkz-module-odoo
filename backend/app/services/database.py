"""
Nekazari Odoo ERP Module - Database Service

Handles database operations for tenant and sync data.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from typing import Optional, Any
from datetime import datetime
import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

# Connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10
        )
    return _pool


async def init_db():
    """Initialize database tables for the Odoo module.
    
    This function is idempotent and handles race conditions from multiple
    pods starting simultaneously.
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        try:
            # Create tables for tenant Odoo info
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS odoo_tenant_info (
                    tenant_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    database VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'pending',
                    energy_modules_enabled BOOLEAN DEFAULT FALSE,
                    installed_modules JSONB DEFAULT '[]'::jsonb,
                    admin_email VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    error TEXT
                )
            """)

            # Create tables for entity mappings
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS odoo_entity_mappings (
                    id SERIAL PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    ngsi_id VARCHAR(512) NOT NULL,
                    ngsi_type VARCHAR(255) NOT NULL,
                    odoo_id INTEGER NOT NULL,
                    odoo_model VARCHAR(255) NOT NULL,
                    odoo_name VARCHAR(512),
                    last_sync TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(tenant_id, ngsi_id)
                )
            """)

            # Create table for sync status
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS odoo_sync_status (
                    tenant_id VARCHAR(255) PRIMARY KEY,
                    status VARCHAR(50) DEFAULT 'never_synced',
                    last_sync TIMESTAMP WITH TIME ZONE,
                    entities_synced INTEGER DEFAULT 0,
                    errors JSONB DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_odoo_mappings_tenant
                ON odoo_entity_mappings(tenant_id)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_odoo_mappings_ngsi_id
                ON odoo_entity_mappings(ngsi_id)
            """)

            logger.info("Database tables initialized")

        except asyncpg.exceptions.UniqueViolationError:
            # Race condition: another pod already created the tables
            logger.info("Database tables already exist (created by another instance)")
        except asyncpg.exceptions.DuplicateTableError:
            # Tables already exist
            logger.info("Database tables already exist")


# Tenant Info Operations

async def get_tenant_odoo_info(tenant_id: str) -> Optional[dict]:
    """Get Odoo info for a tenant."""
    import json
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM odoo_tenant_info WHERE tenant_id = $1",
            tenant_id
        )

        if row:
            data = dict(row)
            # Parse JSON fields
            if isinstance(data.get("installed_modules"), str):
                try:
                    data["installed_modules"] = json.loads(data["installed_modules"])
                except json.JSONDecodeError:
                    data["installed_modules"] = []
            return data
        return None


async def save_tenant_odoo_info(tenant_id: str, info: Optional[dict]):
    """Save or delete Odoo info for a tenant."""
    import json
    pool = await get_pool()

    async with pool.acquire() as conn:
        if info is None:
            # Delete
            await conn.execute(
                "DELETE FROM odoo_tenant_info WHERE tenant_id = $1",
                tenant_id
            )
        else:
            # Upsert
            await conn.execute("""
                INSERT INTO odoo_tenant_info (tenant_id, name, database, status,
                    energy_modules_enabled, installed_modules, admin_email, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, NOW())
                ON CONFLICT (tenant_id) DO UPDATE SET
                    name = COALESCE(EXCLUDED.name, odoo_tenant_info.name),
                    database = COALESCE(EXCLUDED.database, odoo_tenant_info.database),
                    status = COALESCE(EXCLUDED.status, odoo_tenant_info.status),
                    energy_modules_enabled = COALESCE(EXCLUDED.energy_modules_enabled, odoo_tenant_info.energy_modules_enabled),
                    installed_modules = COALESCE(EXCLUDED.installed_modules, odoo_tenant_info.installed_modules),
                    admin_email = COALESCE(EXCLUDED.admin_email, odoo_tenant_info.admin_email),
                    updated_at = NOW()
            """,
                tenant_id,
                info.get("name"),
                info.get("database"),
                info.get("status"),
                info.get("energy_modules_enabled", False),
                json.dumps(info.get("installed_modules", [])),  # Use json.dumps for valid JSON
                info.get("admin_email"),
                info.get("created_at")
            )


# Entity Mapping Operations

async def get_entity_mappings(
    tenant_id: str,
    ngsi_type: Optional[str] = None
) -> list[dict]:
    """Get entity mappings for a tenant."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        if ngsi_type:
            rows = await conn.fetch(
                """SELECT * FROM odoo_entity_mappings
                   WHERE tenant_id = $1 AND ngsi_type = $2""",
                tenant_id, ngsi_type
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM odoo_entity_mappings WHERE tenant_id = $1",
                tenant_id
            )

        return [dict(row) for row in rows]


async def get_entity_mapping_by_ngsi_id(
    tenant_id: str,
    ngsi_id: str
) -> Optional[dict]:
    """Get entity mapping by NGSI-LD ID."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM odoo_entity_mappings
               WHERE tenant_id = $1 AND ngsi_id = $2""",
            tenant_id, ngsi_id
        )

        if row:
            return dict(row)
        return None


async def create_entity_mapping(tenant_id: str, mapping: dict):
    """Create or update entity mapping."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO odoo_entity_mappings
                (tenant_id, ngsi_id, ngsi_type, odoo_id, odoo_model, odoo_name, last_sync)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (tenant_id, ngsi_id) DO UPDATE SET
                odoo_id = EXCLUDED.odoo_id,
                odoo_model = EXCLUDED.odoo_model,
                odoo_name = EXCLUDED.odoo_name,
                last_sync = EXCLUDED.last_sync
        """,
            tenant_id,
            mapping["ngsi_id"],
            mapping["ngsi_type"],
            mapping["odoo_id"],
            mapping["odoo_model"],
            mapping.get("odoo_name"),
            mapping.get("last_sync")
        )


# Sync Status Operations

async def get_sync_status(tenant_id: str) -> Optional[dict]:
    """Get sync status for a tenant."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM odoo_sync_status WHERE tenant_id = $1",
            tenant_id
        )

        if row:
            return dict(row)
        return None


async def update_sync_status(tenant_id: str, status: dict):
    """Update sync status for a tenant."""
    import json
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO odoo_sync_status
                (tenant_id, status, last_sync, entities_synced, errors, updated_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
            ON CONFLICT (tenant_id) DO UPDATE SET
                status = EXCLUDED.status,
                last_sync = EXCLUDED.last_sync,
                entities_synced = EXCLUDED.entities_synced,
                errors = EXCLUDED.errors,
                updated_at = NOW()
        """,
            tenant_id,
            status.get("status"),
            status.get("last_sync"),
            status.get("entities_synced", 0),
            json.dumps(status.get("errors", []))  # Use json.dumps for valid JSON
        )
