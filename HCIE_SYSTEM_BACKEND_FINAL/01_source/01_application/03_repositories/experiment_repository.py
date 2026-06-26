"""
Experiment Repository - Persistent experiment storage
"""

import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExperimentRepository:
    def __init__(self, postgres_store):
        self.db = postgres_store

    def create_experiment(self, tenant_id: str, name: str, groups: List[str]) -> Dict[str, Any]:
        """Create new experiment"""
        query = """
        INSERT INTO experiments (id, tenant_id, name, groups, status, created_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """

        experiment_id = str(uuid.uuid4())
        groups_json = json.dumps(groups)
        status = "created"

        values = (experiment_id, tenant_id, name, groups_json, status, datetime.utcnow())

        result = self.db.execute_query(query, values, fetch_one=True)
        
        if not result:
            raise Exception("Failed to create experiment")
        
        logger.info(f"🧪 Created experiment: {name} ({experiment_id})")
        return result[0]

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID"""
        query = "SELECT * FROM experiments WHERE id = %s"
        result = self.db.execute_query(query, (experiment_id,), fetch_one=True)
        
        if result:
            result_dict = result[0]
            # Parse JSON groups
            if result_dict.get("groups"):
                result_dict["groups"] = json.loads(result_dict["groups"])
            return result_dict
        
        return None

    def get_experiments_by_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all experiments for a tenant"""
        query = "SELECT * FROM experiments WHERE tenant_id = %s ORDER BY created_at DESC"
        results = self.db.execute_query(query, (tenant_id,))
        
        experiments = []
        for row in results:
            exp_dict = dict(row)
            # Parse JSON groups
            if exp_dict.get("groups"):
                exp_dict["groups"] = json.loads(exp_dict["groups"])
            experiments.append(exp_dict)
        
        return experiments

    def update_experiment_status(self, experiment_id: str, status: str):
        """Update experiment status"""
        query = "UPDATE experiments SET status = %s WHERE id = %s"
        self.db.execute_query(query, (status, experiment_id))
        logger.info(f"📊 Updated experiment {experiment_id} status to {status}")

    def get_active_experiments(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get active experiments for a tenant"""
        query = """
        SELECT * FROM experiments 
        WHERE tenant_id = %s AND status IN ('running', 'started')
        ORDER BY created_at DESC
        """
        results = self.db.execute_query(query, (tenant_id,))
        
        experiments = []
        for row in results:
            exp_dict = dict(row)
            if exp_dict.get("groups"):
                exp_dict["groups"] = json.loads(exp_dict["groups"])
            experiments.append(exp_dict)
        
        return experiments
