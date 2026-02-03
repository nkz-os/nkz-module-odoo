"""
Nekazari Odoo ERP Module - API Routers

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from app.routers import tenant, sync, webhook, health

__all__ = ["tenant", "sync", "webhook", "health"]
