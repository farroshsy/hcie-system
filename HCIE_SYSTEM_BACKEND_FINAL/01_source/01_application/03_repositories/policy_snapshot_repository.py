"""
Policy Snapshot Repository - Database Persistence for Immutable Policy Snapshots

C2.1.5: This module provides database persistence for policy snapshots.
Snapshots must be durably stored to ensure replay validity across system restarts.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PolicySnapshotRepository:
    """
    Repository for persisting and retrieving immutable policy snapshots.
    
    This ensures snapshots are durably stored in PostgreSQL for:
    - Replay validity across system restarts
    - Longitudinal educational analysis
    - Policy comparison studies
    - Forensic reconstruction
    """
    
    def __init__(self, postgres_store):
        """
        Initialize repository with PostgreSQL store.
        
        Args:
            postgres_store: PostgresInteractionStore instance for database access
        """
        self.postgres_store = postgres_store
    
    def save_snapshot(self, snapshot_dict: Dict[str, Any]) -> bool:
        """
        Save a policy snapshot to the database.
        
        Args:
            snapshot_dict: Policy snapshot data as dictionary
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            query = """
                INSERT INTO policy_snapshots (
                    snapshot_id, policy_version, created_at, experiment_id,
                    pacing_strategy, remediation_strategy, difficulty_strategy, ux_transformer,
                    adaptation_parameters, thresholds, status, schema_version, snapshot_hash
                ) VALUES (
                    %(snapshot_id)s, %(policy_version)s, %(created_at)s, %(experiment_id)s,
                    %(pacing_strategy)s, %(remediation_strategy)s, %(difficulty_strategy)s, %(ux_transformer)s,
                    %(adaptation_parameters)s, %(thresholds)s, %(status)s, %(schema_version)s, %(snapshot_hash)s
                )
                ON CONFLICT (snapshot_id) DO NOTHING
            """
            
            # Import json for serialization
            import json
            
            params = {
                "snapshot_id": snapshot_dict["snapshot_id"],
                "policy_version": snapshot_dict["policy_version"],
                "created_at": snapshot_dict["created_at"],
                "experiment_id": snapshot_dict.get("experiment_id"),
                "pacing_strategy": json.dumps(snapshot_dict["pacing_strategy"]),
                "remediation_strategy": json.dumps(snapshot_dict["remediation_strategy"]),
                "difficulty_strategy": json.dumps(snapshot_dict["difficulty_strategy"]),
                "ux_transformer": json.dumps(snapshot_dict["ux_transformer"]),
                "adaptation_parameters": json.dumps(snapshot_dict["adaptation_parameters"]),
                "thresholds": json.dumps(snapshot_dict["thresholds"]),
                "status": snapshot_dict["status"],
                "schema_version": snapshot_dict["schema_version"],
                "snapshot_hash": self._compute_snapshot_hash(snapshot_dict)
            }
            
            self.postgres_store.execute_query(query, params)
            logger.info(f"✅ Saved policy snapshot {snapshot_dict['snapshot_id']} to database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save policy snapshot: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a policy snapshot from the database.
        
        Args:
            snapshot_id: Snapshot identifier
        
        Returns:
            Snapshot data as dictionary, or None if not found
        """
        try:
            query = """
                SELECT 
                    snapshot_id, policy_version, created_at, experiment_id,
                    pacing_strategy, remediation_strategy, difficulty_strategy, ux_transformer,
                    adaptation_parameters, thresholds, status, schema_version, snapshot_hash
                FROM policy_snapshots
                WHERE snapshot_id = %s
            """
            
            result = self.postgres_store.execute_query(query, (snapshot_id,))
            
            if result and len(result) > 0:
                row = result[0]
                
                # Import json for deserialization
                import json
                
                snapshot_dict = {
                    "snapshot_id": row[0],
                    "policy_version": row[1],
                    "created_at": row[2],
                    "experiment_id": row[3],
                    "pacing_strategy": json.loads(row[4]),
                    "remediation_strategy": json.loads(row[5]),
                    "difficulty_strategy": json.loads(row[6]),
                    "ux_transformer": json.loads(row[7]),
                    "adaptation_parameters": json.loads(row[8]),
                    "thresholds": json.loads(row[9]),
                    "status": row[10],
                    "schema_version": row[11],
                    "snapshot_hash": row[12]
                }
                
                logger.debug(f"✅ Retrieved policy snapshot {snapshot_id} from database")
                return snapshot_dict
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve policy snapshot {snapshot_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_snapshots_by_policy_version(self, policy_version: str) -> List[Dict[str, Any]]:
        """
        Retrieve all snapshots for a specific policy version.
        
        Args:
            policy_version: Policy version identifier
        
        Returns:
            List of snapshot dictionaries
        """
        try:
            query = """
                SELECT 
                    snapshot_id, policy_version, created_at, experiment_id,
                    pacing_strategy, remediation_strategy, difficulty_strategy, ux_transformer,
                    adaptation_parameters, thresholds, status, schema_version, snapshot_hash
                FROM policy_snapshots
                WHERE policy_version = %s
                ORDER BY created_at DESC
            """
            
            result = self.postgres_store.execute_query(query, (policy_version,))
            
            if result:
                import json
                snapshots = []
                for row in result:
                    snapshot_dict = {
                        "snapshot_id": row[0],
                        "policy_version": row[1],
                        "created_at": row[2],
                        "experiment_id": row[3],
                        "pacing_strategy": json.loads(row[4]),
                        "remediation_strategy": json.loads(row[5]),
                        "difficulty_strategy": json.loads(row[6]),
                        "ux_transformer": json.loads(row[7]),
                        "adaptation_parameters": json.loads(row[8]),
                        "thresholds": json.loads(row[9]),
                        "status": row[10],
                        "schema_version": row[11],
                        "snapshot_hash": row[12]
                    }
                    snapshots.append(snapshot_dict)
                
                logger.debug(f"✅ Retrieved {len(snapshots)} snapshots for policy {policy_version}")
                return snapshots
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve snapshots for policy {policy_version}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_snapshots_by_experiment(self, experiment_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all snapshots for a specific experiment.
        
        Args:
            experiment_id: Experiment identifier
        
        Returns:
            List of snapshot dictionaries
        """
        try:
            query = """
                SELECT 
                    snapshot_id, policy_version, created_at, experiment_id,
                    pacing_strategy, remediation_strategy, difficulty_strategy, ux_transformer,
                    adaptation_parameters, thresholds, status, schema_version, snapshot_hash
                FROM policy_snapshots
                WHERE experiment_id = %s
                ORDER BY policy_version
            """
            
            result = self.postgres_store.execute_query(query, (experiment_id,))
            
            if result:
                import json
                snapshots = []
                for row in result:
                    snapshot_dict = {
                        "snapshot_id": row[0],
                        "policy_version": row[1],
                        "created_at": row[2],
                        "experiment_id": row[3],
                        "pacing_strategy": json.loads(row[4]),
                        "remediation_strategy": json.loads(row[5]),
                        "difficulty_strategy": json.loads(row[6]),
                        "ux_transformer": json.loads(row[7]),
                        "adaptation_parameters": json.loads(row[8]),
                        "thresholds": json.loads(row[9]),
                        "status": row[10],
                        "schema_version": row[11],
                        "snapshot_hash": row[12]
                    }
                    snapshots.append(snapshot_dict)
                
                logger.debug(f"✅ Retrieved {len(snapshots)} snapshots for experiment {experiment_id}")
                return snapshots
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve snapshots for experiment {experiment_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _compute_snapshot_hash(self, snapshot_dict: Dict[str, Any]) -> str:
        """
        Compute hash of snapshot content for integrity validation.
        
        Args:
            snapshot_dict: Snapshot data as dictionary
        
        Returns:
            SHA256 hash string
        """
        import hashlib
        import json
        
        # Create deterministic string representation
        content = json.dumps(snapshot_dict, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
