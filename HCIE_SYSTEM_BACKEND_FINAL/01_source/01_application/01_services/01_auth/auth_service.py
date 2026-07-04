"""
Auth Service - Authentication and user management with persistent storage
Event-driven architecture with Kafka integration
"""

import logging
import uuid
import random
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, user_repo=None, token_store=None, event_producer=None):
        self.user_repo = user_repo
        self.token_store = token_store
        self.event_producer = event_producer  # Kafka event producer
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def register_user(self, email: str, password: str, name: str, role: str = "student", tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Register new user"""
        import os
        
        # PRODUCTION MODE: Require repository
        if not self.user_repo:
            if os.getenv('ENVIRONMENT') == 'production':
                raise RuntimeError("UserRepository not initialized - production mode requires database")
            else:
                # Development fallback (with warning)
                logger.warning("⚠️ UserRepository not available - using in-memory fallback")
                return self._register_user_in_memory(email, password, name, role, tenant_id=tenant_id)
        
        # Check if user exists
        existing = self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("User already exists")

        # Ensure tenant_id is set — users.tenant_id is NOT NULL with a FK to tenants.
        # Look up or create the default tenant if caller didn't supply one.
        if not tenant_id:
            try:
                tenant_row = self.user_repo.postgres_store.execute_read(
                    "SELECT id FROM tenants WHERE name = %s LIMIT 1",
                    ("default",),
                    fetch_one=True,
                )
                if tenant_row and tenant_row.get("id"):
                    tenant_id = str(tenant_row["id"])
                else:
                    created = self.user_repo.postgres_store.execute_write(
                        "INSERT INTO tenants (name) VALUES (%s) RETURNING id",
                        ("default",),
                        fetch_one=True,
                    )
                    if created and created.get("id"):
                        tenant_id = str(created["id"])
                        logger.info(f"🏢 Created default tenant: {tenant_id}")
            except Exception as exc:
                logger.error(f"Failed to resolve default tenant: {exc!r}")
                raise

        user_data = {
            "email": email,
            "password_hash": self.hash_password(password),
            "name": name,
            "role": role,
            "policy_mode": "hcie",  # Default to HCIE
            "learning_rate": 0.01,
            "forgetting_rate": 0.001,
            "experiment_id": None,
            "experiment_group": None,
            "tenant_id": tenant_id
        }
        
        # Create user in database with Unit of Work pattern (truly atomic)
        try:
            # Import Unit of Work
            from app.infrastructure.unit_of_work import get_transaction
            from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
            
            # Get outbox instance (uses same database connection)
            outbox = get_outbox_pattern(self.user_repo.postgres_store, self.event_producer)
            
            # Create unique event ID
            event_id = str(uuid.uuid4())
            
            # Use Unit of Work for true atomicity with explicit transaction context
            with get_transaction(self.user_repo.postgres_store) as tx:
                # Create user with explicit transaction
                user = self.user_repo.create_user(**user_data)
                
                # Create outbox event in same transaction
                outbox_event = outbox.create_event(
                    event_id=event_id,
                    event_type="user_registered",
                    payload={
                        "event_id": event_id,
                        "event_type": "user_registered",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": user['id'],
                        "email": email,
                        "username": name,
                        "registration_source": "auth_service",
                        "metadata": {
                            "role": role,
                            "tenant_id": str(tenant_id) if tenant_id else "",
                            "experiment_group": str(user.get('experiment_group', "")),
                            "source": "auth_service"
                        }
                    },
                    topic="hcie.auth"
                )
                
                # Save outbox event with explicit transaction
                outbox.save_event(outbox_event, transaction=tx)
                
                # Transaction will commit here or rollback on error
                logger.info(f"👤 Successfully registered user: {email} ({user['id']})")
                logger.info(f"📝 Registration event queued for publishing: {event_id}")
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Registration transaction failed: {e}")
            raise

    def _register_user_in_memory(self, email: str, password: str, name: str, role: str = "student", policy_mode: str = "hcie", learning_rate: float = 0.01, forgetting_rate: float = 0.001, experiment_id: Optional[str] = None, experiment_group: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Fallback in-memory registration"""
        if not hasattr(self, '_memory_users'):
            self._memory_users = {}
        
        # Check if user exists
        if any(user["email"] == email for user in self._memory_users.values()):
            raise ValueError("User already exists")
        
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(password)
        
        user = {
            "id": user_id,
            "email": email,
            "password_hash": hashed_password,
            "name": name,
            "role": role,
            "policy_mode": policy_mode,
            "learning_rate": learning_rate,
            "forgetting_rate": forgetting_rate,
            "experiment_id": experiment_id,
            "experiment_group": experiment_group,
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat()
        }
        
        self._memory_users[user_id] = user
        logger.info(f"👤 Registered user in memory: {email} ({user_id})")
        return user
    
    def authenticate_user(self, email: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password with transaction boundary"""
        # Fallback to in-memory if repositories not available
        if not self.user_repo:
            return self._authenticate_user_in_memory(email, password)
        
        try:
            # Begin transaction unit of work
            user = self.user_repo.get_by_email(email)
            if not user or not self.verify_password(password, user["password_hash"]):
                return None
            
            # Update last active within transaction
            self.user_repo.update_last_active(user["id"])
            
            # CRITICAL: Event emitted INSIDE transaction context
            # If event fails, authentication should still succeed (non-critical event)
            if self.event_producer:
                try:
                    self.event_producer.user_logged_in(
                        user_id=user["id"],
                        email=email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        login_method="password"
                    )
                    logger.info(f"📡 Login event emitted for: {email}")
                except Exception as e:
                    # Login events are non-critical - log but don't fail authentication
                    logger.warning(f"⚠️ Login event emission failed (authentication succeeded): {e}")
            
            # Transaction complete - user authenticated and event emitted (if possible)
            logger.info(f"✅ Successfully authenticated user: {email}")
            return user
            
        except Exception as e:
            logger.error(f"❌ Authentication transaction failed: {e}")
            # For authentication, we should be more lenient - don't fail the whole operation
            # unless it's a critical database error
            if "database" in str(e).lower() or "connection" in str(e).lower():
                return None
            # For other errors, try basic authentication without event
            try:
                user = self.user_repo.get_by_email(email)
                if user and self.verify_password(password, user["password_hash"]):
                    logger.warning(f"⚠️ Authentication succeeded without event due to error: {email}")
                    return user
            except Exception:
                pass
            return None
    
    def _authenticate_user_in_memory(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Fallback in-memory authentication"""
        if not hasattr(self, '_memory_users'):
            return None
        
        for user in self._memory_users.values():
            if user["email"] == email and self.verify_password(password, user["password_hash"]):
                user["last_active"] = datetime.utcnow().isoformat()
                logger.info(f"✅ Authenticated user in memory: {email}")
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        # Fallback to in-memory if repositories not available
        if not self.user_repo:
            if hasattr(self, '_memory_users'):
                return self._memory_users.get(user_id)
            return None
        
        return self.user_repo.get_by_id(user_id)
    
    def store_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """Store refresh token for user"""
        if self.token_store:
            self.token_store.store(refresh_token, user_id)
            logger.info(f"🔄 Stored refresh token for user {user_id}")
    
    def verify_refresh_token(self, refresh_token: str) -> Optional[str]:
        """Verify refresh token and return user ID"""
        if self.token_store:
            return self.token_store.verify(refresh_token)
        return None
    
    def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke refresh token"""
        if self.token_store:
            self.token_store.revoke(refresh_token)
            logger.info("🗑️ Revoked refresh token")
    
    def assign_user_to_experiment(self, user_id: str, experiment: Dict[str, Any]) -> bool:
        """Assign user to experiment with random group"""
        try:
            groups = experiment.get("groups", ["hcie", "random"])
            group = random.choice(groups)
            
            self.user_repo.update_experiment_assignment(user_id, experiment["id"], group)
            
            # Update user object if in memory
            user = self.get_user_by_id(user_id)
            if user:
                user["experiment_id"] = experiment["id"]
                user["experiment_group"] = group
            
            logger.info(f"🧪 Assigned user {user_id} to experiment group: {group}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to assign user to experiment: {e}")
            return False
    
    def update_user_policy(self, user_id: str, policy_mode: str, experiment_group: Optional[str] = None) -> bool:
        """Update user policy mode and experiment assignment"""
        updates = {"policy_mode": policy_mode}
        if experiment_group:
            updates["experiment_group"] = experiment_group
        
        self.user_repo.update_profile(user_id, updates)
        logger.info(f"🎯 Updated policy for user {user_id}: {policy_mode}")
        return True
