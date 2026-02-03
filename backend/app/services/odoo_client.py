"""
Nekazari Odoo ERP Module - Odoo Client

Handles communication with Odoo via XML-RPC and JSON-RPC APIs.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
import xmlrpc.client
from typing import Optional, Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OdooClient:
    """Client for Odoo XML-RPC and JSON-RPC APIs."""

    def __init__(self, database: Optional[str] = None):
        """
        Initialize Odoo client.

        Args:
            database: Specific database to connect to. If None, uses master password for DB management.
        """
        self.url = settings.odoo_url
        self.database = database
        self.master_password = settings.ODOO_MASTER_PASSWORD

        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        self.db = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/db")

        # Cached UID for authenticated operations
        self._uid: Optional[int] = None
        self._password: Optional[str] = None

    def authenticate(self, username: str, password: str) -> int:
        """
        Authenticate with Odoo and return user ID.

        Args:
            username: Odoo username (usually email)
            password: Odoo password

        Returns:
            User ID (uid)
        """
        if not self.database:
            raise ValueError("Database must be set for authentication")

        uid = self.common.authenticate(
            self.database,
            username,
            password,
            {}
        )

        if not uid:
            raise ValueError("Authentication failed")

        self._uid = uid
        self._password = password
        return uid

    def execute(
        self,
        model: str,
        method: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a method on an Odoo model.

        Args:
            model: Odoo model name (e.g., 'res.partner')
            method: Method to call (e.g., 'search', 'read', 'create')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Method result
        """
        if not self._uid or not self._password:
            raise ValueError("Must authenticate first")

        return self.models.execute_kw(
            self.database,
            self._uid,
            self._password,
            model,
            method,
            args,
            kwargs
        )

    # Database Management

    async def duplicate_database(self, source_db: str, target_db: str):
        """
        Duplicate a database (used for tenant provisioning).

        Args:
            source_db: Source database name (template)
            target_db: Target database name (new tenant)
        """
        logger.info(f"Duplicating database: {source_db} -> {target_db}")

        try:
            self.db.duplicate_database(
                self.master_password,
                source_db,
                target_db
            )
            logger.info(f"Database duplicated successfully: {target_db}")

        except Exception as e:
            logger.error(f"Failed to duplicate database: {e}")
            raise

    async def delete_database(self, db_name: str):
        """
        Delete a database.

        Args:
            db_name: Database name to delete
        """
        logger.warning(f"Deleting database: {db_name}")

        try:
            self.db.drop(self.master_password, db_name)
            logger.info(f"Database deleted: {db_name}")

        except Exception as e:
            logger.error(f"Failed to delete database: {e}")
            raise

    async def list_databases(self) -> list[str]:
        """List all databases."""
        return self.db.list()

    async def database_exists(self, db_name: str) -> bool:
        """Check if a database exists."""
        databases = await self.list_databases()
        return db_name in databases

    # Module Management

    async def install_modules(self, db_name: str, modules: list[str]):
        """
        Install modules in a database.

        Args:
            db_name: Database name
            modules: List of module technical names to install
        """
        logger.info(f"Installing modules in {db_name}: {modules}")

        # Connect to the database as admin
        client = OdooClient(database=db_name)
        client.authenticate("admin", "admin")  # Default admin credentials

        # Find module IDs
        module_ids = client.execute(
            "ir.module.module",
            "search",
            [["name", "in", modules], ["state", "!=", "installed"]]
        )

        if module_ids:
            # Install modules
            client.execute(
                "ir.module.module",
                "button_immediate_install",
                module_ids
            )
            logger.info(f"Modules installed: {modules}")
        else:
            logger.info("All modules already installed or not found")

    async def get_installed_modules(self, db_name: str) -> list[str]:
        """Get list of installed modules in a database."""
        client = OdooClient(database=db_name)
        client.authenticate("admin", "admin")

        module_ids = client.execute(
            "ir.module.module",
            "search_read",
            [["state", "=", "installed"]],
            {"fields": ["name"]}
        )

        return [m["name"] for m in module_ids]

    # User Management

    async def create_user(
        self,
        db_name: str,
        email: str,
        name: str,
        is_admin: bool = False
    ) -> int:
        """
        Create a new user in Odoo.

        Args:
            db_name: Database name
            email: User email (also used as login)
            name: User display name
            is_admin: Whether to grant admin rights

        Returns:
            Created user ID
        """
        logger.info(f"Creating user in {db_name}: {email}")

        client = OdooClient(database=db_name)
        client.authenticate("admin", "admin")

        # Create user
        user_data = {
            "name": name,
            "login": email,
            "email": email,
            "notification_type": "inbox"
        }

        user_id = client.execute("res.users", "create", user_data)

        if is_admin:
            # Add to admin group
            admin_group_id = client.execute(
                "res.groups",
                "search",
                [["category_id.name", "=", "Administration"],
                 ["name", "=", "Settings"]]
            )

            if admin_group_id:
                client.execute(
                    "res.users",
                    "write",
                    [user_id],
                    {"groups_id": [(4, admin_group_id[0])]}
                )

        logger.info(f"User created: {email} (ID: {user_id})")
        return user_id

    # Record Operations

    async def create_record(
        self,
        db_name: str,
        model: str,
        values: dict
    ) -> int:
        """Create a record in Odoo."""
        client = OdooClient(database=db_name)
        client.authenticate("admin", "admin")

        record_id = client.execute(model, "create", values)
        logger.debug(f"Created {model} record: {record_id}")
        return record_id

    async def update_record(
        self,
        db_name: str,
        model: str,
        record_id: int,
        values: dict
    ):
        """Update a record in Odoo."""
        client = OdooClient(database=db_name)
        client.authenticate("admin", "admin")

        client.execute(model, "write", [record_id], values)
        logger.debug(f"Updated {model} record: {record_id}")

    async def read_record(
        self,
        db_name: str,
        model: str,
        record_id: int,
        fields: Optional[list[str]] = None
    ) -> dict:
        """Read a record from Odoo."""
        client = OdooClient(database=db_name)
        client.authenticate("admin", "admin")

        result = client.execute(
            model,
            "read",
            [record_id],
            {"fields": fields} if fields else {}
        )

        return result[0] if result else {}

    async def search_records(
        self,
        db_name: str,
        model: str,
        domain: list,
        fields: Optional[list[str]] = None,
        limit: Optional[int] = None
    ) -> list[dict]:
        """Search records in Odoo."""
        client = OdooClient(database=db_name)
        client.authenticate("admin", "admin")

        kwargs = {}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit

        return client.execute(model, "search_read", domain, kwargs)
