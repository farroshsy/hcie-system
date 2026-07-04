"""
V3 API Client

HTTP client for calling V3 runtime APIs from worker processes.
Provides a simple interface for workers to integrate with V3 endpoints.
"""

import logging
import httpx
from typing import Dict, Any, Optional
from config.env import settings

logger = logging.getLogger(__name__)


def resolve_v3_base_url(settings_obj=settings) -> str:
    """
    Resolve V3 API base URL with Docker-aware defaults.
    
    Args:
        settings_obj: Settings object (defaults to global settings)
        
    Returns:
        Docker-safe base URL (http://api:8000 in Docker, http://localhost:8000 locally)
    """
    configured = getattr(settings_obj, "v3_api_base_url", None)
    if configured:
        return configured
    docker_env = getattr(settings_obj, "docker_env", False)
    if docker_env or getattr(settings_obj, "DOCKER_ENV", False):
        return "http://api:8000"
    return "http://localhost:8000"


class V3APIClient:
    """
    HTTP client for V3 runtime APIs.
    
    Provides methods to call V3 endpoints from worker processes.
    Designed for integration with event-driven consumers.
    """
    
    def __init__(self, base_url: str = None):
        """
        Initialize V3 API client.
        
        Args:
            base_url: Base URL for V3 API (default: Docker-aware)
        """
        self.base_url = base_url or resolve_v3_base_url(settings)
        self.client = httpx.Client(timeout=30.0)
        logger.info(f"V3 API Client initialized with base URL: {self.base_url}")
    
    def call_mutation_api(
        self,
        user_id: str,
        mutation_type: str,
        mutation_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call V3 Mutation API for canonical mutations.
        
        Args:
            user_id: User ID
            mutation_type: Type of mutation
            mutation_data: Mutation data
            
        Returns:
            Response from V3 mutation API or None on failure
        """
        try:
            url = f"{self.base_url}/v3/runtime/mutation"
            payload = {
                "user_id": user_id,
                "mutation_type": mutation_type,
                "mutation_data": mutation_data
            }
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"V3 mutation API called successfully: {mutation_type} for user {user_id}")
            return result
            
        except httpx.HTTPError as e:
            logger.warning(f"V3 mutation API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling V3 mutation API: {e}")
            return None
    
    def call_trajectory_api(
        self,
        user_id: str,
        trajectory_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call V3 Trajectory API for trajectory recording.
        
        Args:
            user_id: User ID
            trajectory_data: Trajectory data
            
        Returns:
            Response from V3 trajectory API or None on failure
        """
        try:
            url = f"{self.base_url}/v3/runtime/trajectory"
            payload = {
                "user_id": user_id,
                "trajectory_data": trajectory_data
            }
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"V3 trajectory API called successfully for user {user_id}")
            return result
            
        except httpx.HTTPError as e:
            logger.warning(f"V3 trajectory API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling V3 trajectory API: {e}")
            return None
    
    def call_research_transfer_api(
        self,
        telemetry_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call V3 Research Transfer API for transfer telemetry.
        
        Args:
            telemetry_data: Transfer telemetry data
            
        Returns:
            Response from V3 research API or None on failure
        """
        try:
            url = f"{self.base_url}/v3/research/transfer"
            payload = {
                "telemetry_data": telemetry_data
            }
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info("V3 research transfer API called successfully")
            return result
            
        except httpx.HTTPError as e:
            logger.warning(f"V3 research transfer API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling V3 research transfer API: {e}")
            return None
    
    def call_research_policy_api(
        self,
        telemetry_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call V3 Research Policy API for policy telemetry.
        
        Args:
            telemetry_data: Policy telemetry data
            
        Returns:
            Response from V3 research API or None on failure
        """
        try:
            url = f"{self.base_url}/v3/research/policy"
            payload = {
                "telemetry_data": telemetry_data
            }
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info("V3 research policy API called successfully")
            return result
            
        except httpx.HTTPError as e:
            logger.warning(f"V3 research policy API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling V3 research policy API: {e}")
            return None
    
    def call_event_api(
        self,
        event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call V3 Event API for event propagation visibility.
        
        Args:
            event_data: Event data
            
        Returns:
            Response from V3 event API or None on failure
        """
        try:
            url = f"{self.base_url}/v3/runtime/event"
            payload = {
                "event_data": event_data
            }
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info("V3 event API called successfully")
            return result
            
        except httpx.HTTPError as e:
            logger.warning(f"V3 event API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling V3 event API: {e}")
            return None
    
    def _governance_state_url(self, user_id: str) -> str:
        """Build governance state URL matching V3 router path."""
        return f"{self.base_url}/v3/runtime/governance/state?user_id={user_id}"

    def get_governance_state(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get governance state from V3 API.
        
        Args:
            user_id: User ID
            
        Returns:
            Governance state or None on failure
        """
        try:
            url = self._governance_state_url(user_id)
            response = self.client.get(url)
            response.raise_for_status()

            result = response.json()
            logger.info(f"V3 governance state retrieved for user {user_id}")
            return result

        except httpx.HTTPError as e:
            logger.warning(f"V3 governance state retrieval failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving V3 governance state: {e}")
            return None
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
        logger.info("V3 API Client closed")


def get_v3_client() -> V3APIClient:
    """
    Get V3 API client instance with Docker-aware defaults.
    
    Returns:
        V3APIClient instance
    """
    return V3APIClient(base_url=resolve_v3_base_url(settings))
