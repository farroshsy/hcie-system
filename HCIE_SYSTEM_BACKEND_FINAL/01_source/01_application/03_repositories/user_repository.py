"""
User Repository - PostgreSQL user data access
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """PostgreSQL repository for user management"""
    
    # Allowed fields for dynamic updates (whitelist for security)
    ALLOWED_UPDATE_FIELDS = {"name", "learning_rate", "forgetting_rate"}
    
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store

    def create_user(self, email: str, password_hash: str, name: str, role: str = 'student',
                    policy_mode: str = 'hcie', learning_rate: float = 0.01, 
                    forgetting_rate: float = 0.001, experiment_id: Optional[str] = None,
                    experiment_group: Optional[str] = None, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user in PostgreSQL"""
        query = """
            INSERT INTO users (
                id, email, password_hash, name, role,
                policy_mode, learning_rate, forgetting_rate,
                experiment_id, experiment_group, tenant_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        values = (
            str(uuid.uuid4()), email, password_hash, name, role,
            policy_mode, learning_rate, forgetting_rate,
            experiment_id, experiment_group, tenant_id
        )

        try:
            result = self.postgres_store.execute_write(query, values, fetch_one=True)
        except Exception as e:
            if "unique" in str(e).lower() and "email" in str(e).lower():
                raise ValueError("User with this email already exists")
            logger.error(f"❌ Failed to create user in repository: {e}")
            raise ValueError("Failed to create user")
        
        if not result:
            raise Exception("Failed to create user")
        
        logger.info(f"👤 User created in DB: {email}")
        return result

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.postgres_store.execute_read(query, (email,), fetch_one=True)
        return result

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        import re
        _UUID_RE = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        if not _UUID_RE.match(user_id or ""):
            # Non-UUID strings (synthetic IDs, research-validation, etc.) will never
            # be in the users table; skip the DB round-trip to avoid a Postgres
            # "invalid input syntax for type uuid" error.
            return None
        query = "SELECT * FROM users WHERE id = %s"
        result = self.postgres_store.execute_read(query, (user_id,), fetch_one=True)
        return result

    def update_last_active(self, user_id: str):
        """Update user's last active timestamp"""
        query = """
        UPDATE users SET last_active = %s WHERE id = %s
        """
        self.postgres_store.execute_write(query, (datetime.utcnow(), user_id))
        logger.info(f"🔄 Updated last_active for user: {user_id}")

    def update_experiment_assignment(self, user_id: str, experiment_id: str, experiment_group: str):
        """Assign user to experiment"""
        query = """
        UPDATE users 
        SET experiment_id = %s, experiment_group = %s 
        WHERE id = %s
        """
        self.postgres_store.execute_write(query, (experiment_id, experiment_group, user_id))
        logger.info(f"🧪 Assigned user {user_id} to experiment {experiment_group}")

    def get_users_by_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all users for a tenant"""
        query = "SELECT * FROM users WHERE tenant_id = %s"
        results = self.postgres_store.execute_read(query, (tenant_id,))
        return results if results else []

    def update_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update user profile fields"""
        if not updates:
            return
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if field in self.ALLOWED_UPDATE_FIELDS:
                set_clauses.append(f"{field} = %s")
                values.append(value)
        
        if not set_clauses:
            return
            
        set_clause = ", ".join(set_clauses)
        query = f"UPDATE users SET {set_clause} WHERE id = %s"
        values.append(user_id)
        
        # Check if user already exists
        existing = self.get_by_email(updates.get('email'))
        if existing:
            raise ValueError("User already exists")
        
        self.postgres_store.execute_write(query, values)
        logger.info(f"✏️ Updated profile for user: {user_id}")

    def get_all_users(self) -> List[str]:
        """Get all user IDs from the system"""
        query = "SELECT DISTINCT user_id FROM user_state WHERE user_id IS NOT NULL"
        
        try:
            result = self.postgres_store.execute_read(query)
            return [row[0] for row in result] if result else []
        except Exception as e:
            logger.error(f"❌ Failed to get all users: {e}")
            return []
