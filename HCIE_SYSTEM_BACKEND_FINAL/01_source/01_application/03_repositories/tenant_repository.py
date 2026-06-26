"""
Tenant Repository - Multi-tenant support
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TenantRepository:
    def __init__(self, postgres_store):
        self.db = postgres_store

    def create_tenant(self, name: str) -> Dict[str, Any]:
        """Create new tenant"""
        query = """
        INSERT INTO tenants (id, name, created_at)
        VALUES (%s, %s, %s)
        RETURNING *
        """

        tenant_id = str(uuid.uuid4())
        values = (tenant_id, name, datetime.utcnow())

        result = self.db.execute_query(query, values, fetch_one=True)
        
        if not result:
            raise Exception("Failed to create tenant")
        
        logger.info(f"🏢 Created tenant: {name} ({tenant_id})")
        return result[0]

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        query = "SELECT * FROM tenants WHERE id = %s"
        result = self.db.execute_query(query, (tenant_id,), fetch_one=True)
        return result[0] if result else None

    def get_all_tenants(self) -> List[Dict[str, Any]]:
        """Get all tenants"""
        query = "SELECT * FROM tenants ORDER BY created_at DESC"
        results = self.db.execute_query(query)
        return [dict(row) for row in results]

    def get_tenant_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant for a specific user"""
        query = """
        SELECT t.* FROM tenants t
        JOIN users u ON u.tenant_id = t.id
        WHERE u.id = %s
        """
        result = self.db.execute_query(query, (user_id,), fetch_one=True)
        return result[0] if result else None
