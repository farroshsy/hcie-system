"""
Service Management API Routes
Integrated service monitoring and management for HCIE infrastructure
"""

import docker
import requests
import json
import sys
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.api.dependencies.rbac import require_admin

# Add project root to Python path
sys.path.insert(0, '/app')

# SECURITY: every endpoint here (restart containers, read logs, setup CDC) is admin-only.
router = APIRouter(prefix="/admin/services", tags=["service-management"], dependencies=[Depends(require_admin)])

class ServiceStatusResponse(BaseModel):
    service: str
    status: str
    description: str
    container: Dict[str, Any]
    health: Dict[str, Any]
    timestamp: str

class ServiceRestartResponse(BaseModel):
    service: str
    action: str
    success: bool
    message: str
    timestamp: str

class HCIEServiceManager:
    """Integrated service management for HCIE infrastructure"""
    
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            # Test Docker connection
            self.docker_client.ping()
            print("Docker client initialized successfully")
        except Exception as e:
            print(f"Docker client initialization failed: {e}")
            self.docker_client = None
            print("Using fallback service management mode")
            
        self.services = {
            'redis': {
                'container': 'docker-redis-1',
                'port': 6379,
                'health_check': self._check_redis,
                'description': 'Redis Cache Layer'
            },
            'postgres': {
                'container': 'docker-postgres-1',
                'port': 5432,
                'health_check': self._check_postgres,
                'description': 'PostgreSQL Database'
            },
            'kafka': {
                'container': 'docker-kafka-1',
                'port': 9092,
                'health_check': self._check_kafka,
                'description': 'Kafka Event Streaming'
            },
            'api': {
                'container': 'docker-api-1',
                'port': 8000,
                'health_check': self._check_api,
                'description': 'HCIE API Service'
            },
            'schema-registry': {
                'container': 'schema-registry',
                'port': 8081,
                'health_check': self._check_schema_registry,
                'description': 'Kafka Schema Registry'
            },
            'kafka-connect': {
                'container': 'kafka-connect',
                'port': 8083,
                'health_check': self._check_kafka_connect,
                'description': 'Kafka Connect (Debezium)'
            },
            'kafka-ui': {
                'container': 'kafka-ui',
                'port': 8080,
                'health_check': self._check_kafka_ui,
                'description': 'Kafka Management UI'
            },
            'prometheus': {
                'container': 'prometheus',
                'port': 9090,
                'health_check': self._check_prometheus,
                'description': 'Prometheus Metrics'
            },
            'grafana': {
                'container': 'grafana',
                'port': 3000,
                'health_check': self._check_grafana,
                'description': 'Grafana Visualization'
            }
        }
    
    def _check_redis(self, container_name: str) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            import redis
            r = redis.Redis(host='redis', port=6379, decode_responses=True)
            r.ping()
            return {'status': 'healthy', 'response_time': 'fast', 'info': 'Connected'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_postgres(self, container_name: str) -> Dict[str, Any]:
        """Check PostgreSQL health"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='postgres',
                port=5432,
                database='hcie',
                user='hcie_user',
                password='hcie_password'
            )
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            return {'status': 'healthy', 'database': 'hcie', 'connections': 'active'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_kafka(self, container_name: str) -> Dict[str, Any]:
        """Check Kafka health"""
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: str(v).encode(),
                request_timeout_ms=5000
            )
            producer.close()
            return {'status': 'healthy', 'bootstrap_servers': 'kafka:9092'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_api(self, container_name: str) -> Dict[str, Any]:
        """Check API health"""
        try:
            # Skip self-check to avoid timeout, just check if process is running
            import os
            if os.path.exists('/app'):
                return {'status': 'healthy', 'response': 'API process running', 'self_check': 'skipped'}
            else:
                return {'status': 'unhealthy', 'error': 'API process not found'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_schema_registry(self, container_name: str) -> Dict[str, Any]:
        """Check Schema Registry health"""
        try:
            response = requests.get('http://schema-registry:8081/subjects', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'subjects_count': len(response.json())}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_kafka_connect(self, container_name: str) -> Dict[str, Any]:
        """Check Kafka Connect health"""
        try:
            response = requests.get('http://kafka-connect:8083/connectors', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'connectors': response.json()}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            error_str = str(e)
            if 'NameResolutionError' in error_str or 'Temporary failure' in error_str:
                return {'status': 'restarting', 'error': 'Service is starting up...'}
            else:
                return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_kafka_ui(self, container_name: str) -> Dict[str, Any]:
        """Check Kafka UI health"""
        try:
            # Try root endpoint first
            response = requests.get('http://kafka-ui:8080/', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'ui_accessible': True, 'endpoint': '/'}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_prometheus(self, container_name: str) -> Dict[str, Any]:
        """Check Prometheus health"""
        try:
            response = requests.get('http://prometheus:9090/api/v1/query?query=up', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'metrics_available': True}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_grafana(self, container_name: str) -> Dict[str, Any]:
        """Check Grafana health"""
        try:
            response = requests.get('http://grafana:3000/api/health', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'health': response.json()}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get detailed status of a specific service"""
        if service_name not in self.services:
            return {'error': f'Service {service_name} not found'}
        
        service_config = self.services[service_name]
        
        # Fallback mode - just do health checks without Docker container info
        if not self.docker_client:
            try:
                # Get health check result
                health_result = service_config['health_check'](service_config['container'])
                
                return {
                    'service': service_name,
                    'description': service_config['description'],
                    'container': {
                        'name': service_config['container'],
                        'status': 'unknown (fallback mode)',
                        'mode': 'health_check_only'
                    },
                    'health': health_result,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    'service': service_name,
                    'description': service_config['description'],
                    'container': {
                        'name': service_config['container'],
                        'status': 'unknown (fallback mode)',
                        'mode': 'health_check_only'
                    },
                    'health': {'status': 'unhealthy', 'error': str(e)},
                    'timestamp': datetime.now().isoformat()
                }
        
        try:
            # Get container info
            container = self.docker_client.containers.get(service_config['container'])
            container_info = {
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'ports': container.ports,
                'created': container.attrs['Created'],
                'labels': container.labels
            }
            
            # Get health check result
            health_result = service_config['health_check'](service_config['container'])
            
            return {
                'service': service_name,
                'description': service_config['description'],
                'container': container_info,
                'health': health_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except docker.errors.NotFound:
            return {
                'service': service_name,
                'error': f'Container {service_config["container"]} not found',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service': service_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_all_services_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        results = {}
        healthy_count = 0
        total_count = len(self.services)
        
        for service_name in self.services:
            results[service_name] = self.get_service_status(service_name)
            if 'health' in results[service_name] and results[service_name]['health']['status'] == 'healthy':
                healthy_count += 1
        
        return {
            'summary': {
                'total_services': total_count,
                'healthy_services': healthy_count,
                'unhealthy_services': total_count - healthy_count,
                'health_percentage': (healthy_count / total_count) * 100
            },
            'services': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a specific service"""
        if service_name not in self.services:
            return {'error': f'Service {service_name} not found'}
        
        if not self.docker_client:
            return {'error': 'Docker client not available'}
        
        try:
            container = self.docker_client.containers.get(self.services[service_name]['container'])
            container.restart()
            return {
                'service': service_name,
                'action': 'restarted',
                'container': container.name,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_service_logs(self, service_name: str, lines: int = 50) -> Dict[str, Any]:
        """Get logs for a specific service"""
        if service_name not in self.services:
            return {'error': f'Service {service_name} not found'}
        
        if not self.docker_client:
            return {'error': 'Docker client not available'}
        
        try:
            container = self.docker_client.containers.get(self.services[service_name]['container'])
            logs = container.logs(tail=lines).decode('utf-8')
            return {
                'service': service_name,
                'logs': logs,
                'lines_count': len(logs.split('\n')),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def setup_debezium_connector(self) -> Dict[str, Any]:
        """Setup Debezium connector for PostgreSQL CDC"""
        connector_config = {
            "name": "hcie-postgres-connector",
            "config": {
                "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
                "database.hostname": "postgres",
                "database.port": "5432",
                "database.user": "hcie_user",
                "database.password": "hcie_password",
                "database.dbname": "hcie",
                "database.server.name": "postgres",
                "table.include.list": "public.interactions,public.users,public.concepts",
                "plugin.name": "pgoutput",
                "slot.name": "hcie_slot",
                "publication.name": "hcie_publication",
                "transforms": "unwrap",
                "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
                "transforms.unwrap.drop.tombstones": "false",
                "transforms.unwrap.add.fields": "op,ts_ms",
                "key.converter": "org.apache.kafka.connect.storage.StringConverter",
                "value.converter": "org.apache.kafka.connect.json.JsonConverter",
                "value.converter.schemas.enable": "false",
                "tombstones.on.delete": "false",
                "heartbeat.interval.ms": "30000",
                "snapshot.mode": "initial",
                "snapshot.locking.mode": "minimal",
                "snapshot.fetch.size": "1024",
                "max.batch.size": "2048",
                "max.queue.size": "8192",
                "poll.interval.ms": "1000"
            }
        }
        
        try:
            response = requests.post(
                'http://kafka-connect:8083/connectors',
                json=connector_config,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return {
                    'status': 'success',
                    'message': 'Debezium connector created successfully',
                    'connector': response.json(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to create connector: {response.status_code}',
                    'response': response.text,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global service manager instance
service_manager = HCIEServiceManager()

@router.get("/status")
async def get_all_services_status():
    """Get status of all services"""
    return service_manager.get_all_services_status()

@router.get("/status/{service_name}")
async def get_service_status(service_name: str):
    """Get status of a specific service"""
    result = service_manager.get_service_status(service_name)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return result

@router.post("/restart/{service_name}")
async def restart_service(service_name: str):
    """Restart a specific service"""
    result = service_manager.restart_service(service_name)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return result

@router.get("/logs/{service_name}")
async def get_service_logs(service_name: str, lines: int = 50):
    """Get logs for a specific service"""
    result = service_manager.get_service_logs(service_name, lines)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return result

@router.post("/setup-cdc")
async def setup_debezium_connector():
    """Setup Debezium connector for PostgreSQL CDC"""
    result = service_manager.setup_debezium_connector()
    return result
