"""
Kafka Observability and Monitoring
Provides real-time Kafka cluster health and consumer metrics
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class KafkaPartitionMetrics:
    """Metrics for a specific partition"""
    topic: str
    partition: int
    current_offset: int
    latest_offset: int
    lag: int
    consumer_group: str
    timestamp: datetime
    is_leader: bool = False
    under_replicated: bool = False

@dataclass
class KafkaClusterMetrics:
    """Kafka cluster health metrics"""
    broker_count: int
    topic_count: int
    total_partitions: int
    healthy_brokers: int
    under_replicated_partitions: int
    timestamp: datetime
    broker_details: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ConsumerGroupMetrics:
    """Consumer group performance metrics"""
    group_id: str
    state: str  # stable, rebalancing, dead
    members: int
    active_members: int
    partition_assignments: List[KafkaPartitionMetrics]
    rebalance_count: int
    last_rebalance: Optional[datetime]
    timestamp: datetime

class KafkaObservability:
    """Kafka observability and monitoring"""
    
    def __init__(self, kafka_consumer=None):
        self.kafka_consumer = kafka_consumer
        self.metrics_history = []
        self.last_collection = None
        
    def collect_partition_lag(self, consumer_group: str, topics: List[str]) -> List[KafkaPartitionMetrics]:
        """Collect partition lag metrics for consumer group"""
        try:
            metrics = []
            
            for topic in topics:
                # Get partition information
                partitions = self._get_topic_partitions(topic)
                
                for partition in partitions:
                    # Get consumer offset
                    current_offset = self._get_consumer_offset(consumer_group, topic, partition)
                    
                    # Get latest offset
                    latest_offset = self._get_latest_offset(topic, partition)
                    
                    # Calculate lag
                    lag = latest_offset - current_offset
                    
                    metrics.append(KafkaPartitionMetrics(
                        topic=topic,
                        partition=partition,
                        current_offset=current_offset,
                        latest_offset=latest_offset,
                        lag=lag,
                        consumer_group=consumer_group,
                        timestamp=datetime.utcnow()
                    ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to collect partition lag: {e}")
            return []
    
    def collect_cluster_health(self) -> KafkaClusterMetrics:
        """Collect Kafka cluster health metrics"""
        try:
            # Get broker information
            brokers = self._get_broker_metadata()
            healthy_brokers = sum(1 for broker in brokers if broker.get('healthy', False))
            under_replicated = self._get_under_replicated_partitions()
            
            return KafkaClusterMetrics(
                broker_count=len(brokers),
                topic_count=len(self._get_all_topics()),
                total_partitions=sum(len(self._get_topic_partitions(topic)) for topic in self._get_all_topics()),
                healthy_brokers=healthy_brokers,
                under_replicated_partitions=under_replicated,
                timestamp=datetime.utcnow(),
                broker_details=brokers
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to collect cluster health: {e}")
            return KafkaClusterMetrics(
                broker_count=0,
                topic_count=0,
                total_partitions=0,
                healthy_brokers=0,
                under_replicated_partitions=0,
                timestamp=datetime.utcnow()
            )
    
    def collect_consumer_group_metrics(self, group_id: str) -> ConsumerGroupMetrics:
        """Collect consumer group performance metrics"""
        try:
            # Get consumer group state
            group_state = self._get_consumer_group_state(group_id)
            
            # Get partition assignments
            assignments = self._get_consumer_group_assignments(group_id)
            
            return ConsumerGroupMetrics(
                group_id=group_id,
                state=group_state.get('state', 'unknown'),
                members=len(group_state.get('members', [])),
                active_members=len([m for m in group_state.get('members', []) if m.get('active', False)]),
                partition_assignments=assignments,
                rebalance_count=group_state.get('rebalance_count', 0),
                last_rebalance=group_state.get('last_rebalance'),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to collect consumer group metrics: {e}")
            return ConsumerGroupMetrics(
                group_id=group_id,
                state='error',
                members=0,
                active_members=0,
                partition_assignments=[],
                rebalance_count=0,
                last_rebalance=None,
                timestamp=datetime.utcnow()
            )
    
    def get_rebalance_metrics(self, group_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get rebalance metrics for consumer group"""
        try:
            # This would typically come from Kafka metrics or monitoring system
            # For now, simulate with recent rebalance detection
            
            current_state = self._get_consumer_group_state(group_id)
            
            return {
                "group_id": group_id,
                "current_state": current_state.get('state', 'unknown'),
                "rebalance_count": current_state.get('rebalance_count', 0),
                "last_rebalance": current_state.get('last_rebalance'),
                "rebalance_frequency": self._calculate_rebalance_frequency(group_id, hours),
                "avg_rebalance_duration": self._get_avg_rebalance_duration(group_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get rebalance metrics: {e}")
            return {"error": str(e)}
    
    def get_offset_commit_metrics(self, group_id: str) -> Dict[str, Any]:
        """Get offset commit metrics for consumer group"""
        try:
            # Get offset commit information
            commits = self._get_offset_commits(group_id)
            
            return {
                "group_id": group_id,
                "total_commits": len(commits),
                "recent_commits": commits[-10:],  # Last 10 commits
                "commit_frequency": self._calculate_commit_frequency(commits),
                "lagging_partitions": self._get_lagging_partitions(group_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get offset commit metrics: {e}")
            return {"error": str(e)}
    
    # Helper methods (would connect to actual Kafka admin APIs)
    def _get_topic_partitions(self, topic: str) -> List[int]:
        """Get partition list for topic"""
        # TODO: Implement actual Kafka admin API call
        return [0, 1, 2]  # Mock implementation
    
    def _get_consumer_offset(self, group_id: str, topic: str, partition: int) -> int:
        """Get current consumer offset"""
        # TODO: Implement actual Kafka admin API call
        return 0  # Mock implementation
    
    def _get_latest_offset(self, topic: str, partition: int) -> int:
        """Get latest offset for partition"""
        # TODO: Implement actual Kafka admin API call
        return 1000  # Mock implementation
    
    def _get_broker_metadata(self) -> List[Dict[str, Any]]:
        """Get broker metadata"""
        # TODO: Implement actual Kafka admin API call
        return [
            {"id": 1, "host": "localhost", "port": 9092, "healthy": True},
            {"id": 2, "host": "localhost", "port": 9093, "healthy": True}
        ]
    
    def _get_all_topics(self) -> List[str]:
        """Get all topics"""
        # TODO: Implement actual Kafka admin API call
        return ["hcie.auth", "hcie.tasks", "hcie.analytics"]
    
    def _get_under_replicated_partitions(self) -> int:
        """Get count of under-replicated partitions"""
        # TODO: Implement actual Kafka admin API call
        return 0  # Mock implementation
    
    def _get_consumer_group_state(self, group_id: str) -> Dict[str, Any]:
        """Get consumer group state"""
        # TODO: Implement actual Kafka admin API call
        return {
            "state": "stable",
            "members": [{"id": "consumer-1", "active": True}],
            "rebalance_count": 0,
            "last_rebalance": datetime.utcnow() - timedelta(hours=1)
        }
    
    def _get_consumer_group_assignments(self, group_id: str) -> List[KafkaPartitionMetrics]:
        """Get partition assignments for consumer group"""
        # TODO: Implement actual Kafka admin API call
        return []
    
    def _calculate_rebalance_frequency(self, group_id: str, hours: int) -> float:
        """Calculate rebalance frequency per hour"""
        # TODO: Implement based on historical data
        return 0.1  # Mock implementation
    
    def _get_avg_rebalance_duration(self, group_id: str) -> float:
        """Get average rebalance duration in seconds"""
        # TODO: Implement based on historical data
        return 5.0  # Mock implementation
    
    def _get_offset_commits(self, group_id: str) -> List[Dict[str, Any]]:
        """Get recent offset commits"""
        # TODO: Implement actual Kafka admin API call
        return [
            {"timestamp": datetime.utcnow() - timedelta(minutes=i), "offset": i * 10}
            for i in range(10)
        ]
    
    def _calculate_commit_frequency(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate commit frequency per minute"""
        if len(commits) < 2:
            return 0.0
        
        time_span = (commits[-1]["timestamp"] - commits[0]["timestamp"]).total_seconds() / 60
        return len(commits) / time_span if time_span > 0 else 0.0
    
    def _get_lagging_partitions(self, group_id: str) -> List[Dict[str, Any]]:
        """Get partitions with significant lag"""
        # TODO: Implement based on partition lag metrics
        return []

# Global observability instance
_kafka_observability = None

def get_kafka_observability(kafka_consumer=None) -> KafkaObservability:
    """Get or create Kafka observability instance"""
    global _kafka_observability
    
    if _kafka_observability is None:
        _kafka_observability = KafkaObservability(kafka_consumer)
    
    return _kafka_observability
