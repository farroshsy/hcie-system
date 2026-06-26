#!/usr/bin/env python3
"""
Multi-Worker Coordinator
Manages multiple outbox workers with partitioned processing
"""

import os
import sys
import logging
import signal
import time
import threading
import multiprocessing
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
from app.infrastructure.messaging.event_bus import KafkaEventBus
from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
from app.infrastructure.monitoring.event_metrics import event_metrics_collector
from config.env import settings

logger = logging.getLogger(__name__)

class WorkerCoordinator:
    """Coordinates multiple outbox workers with partitioned processing"""
    
    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or settings.get('outbox_worker_count', 2)
        self.workers = []
        self.worker_processes = []
        self.running = False
        self.coordinator_thread = None
        self.health_check_interval = 30
        
        # Worker assignment tracking
        self.worker_assignments = {}  # worker_id -> assigned partitions/topics
        self.partition_assignments = {}  # partition -> assigned worker_id
        
    def start(self):
        """Start the multi-worker coordinator"""
        logger.info(f"🚀 Starting multi-worker coordinator with {self.num_workers} workers")
        
        self.running = True
        
        # Start worker processes
        self._start_worker_processes()
        
        # Start coordinator thread
        self.coordinator_thread = threading.Thread(target=self._coordinator_loop, daemon=True)
        self.coordinator_thread.start()
        
        logger.info("✅ Multi-worker coordinator started")
    
    def stop(self):
        """Stop all workers and coordinator"""
        logger.info("🛑 Stopping multi-worker coordinator...")
        self.running = False
        
        # Stop worker processes
        for worker_process in self.worker_processes:
            try:
                worker_process.terminate()
                worker_process.join(timeout=10)
            except Exception as e:
                logger.error(f"❌ Failed to stop worker process: {e}")
        
        # Stop coordinator thread
        if self.coordinator_thread:
            self.coordinator_thread.join(timeout=10)
        
        logger.info("✅ Multi-worker coordinator stopped")
    
    def _start_worker_processes(self):
        """Start individual worker processes"""
        for worker_id in range(self.num_workers):
            try:
                # Create worker process
                process = multiprocessing.Process(
                    target=self._run_worker_process,
                    args=(worker_id,),
                    name=f"outbox-worker-{worker_id}"
                )
                
                process.start()
                self.worker_processes.append(process)
                
                logger.info(f"✅ Started worker process {worker_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to start worker process {worker_id}: {e}")
    
    def _run_worker_process(self, worker_id: int):
        """Run individual worker process"""
        try:
            # Setup process-specific logging
            process_logger = logging.getLogger(f"outbox-worker-{worker_id}")
            process_logger.info(f"🔄 Worker {worker_id} process starting...")
            
            # Initialize worker dependencies
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            kafka_producer = kafka_factory.create_producer()
            event_bus = KafkaEventBus(kafka_producer)
            
            # Create outbox pattern
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            postgres_store = PostgresInteractionStore(settings)
            outbox_pattern = get_outbox_pattern(postgres_store, event_bus=event_bus)
            
            # Start background processor with worker-specific configuration
            outbox_pattern.start_background_processor(
                interval_seconds=getattr(settings, 'outbox_poll_interval', 5),
                worker_id=f"outbox-worker-{worker_id}"
            )
            
            process_logger.info(f"✅ Worker {worker_id} initialized successfully")
            
            # Worker process main loop
            self._worker_main_loop(worker_id, outbox_pattern, process_logger)
            
        except Exception as e:
            logger.error(f"❌ Worker {worker_id} process crashed: {e}")
    
    def _worker_main_loop(self, worker_id: int, outbox_pattern, logger):
        """Main loop for worker process"""
        health_check_interval = 30
        last_health_check = time.time()
        
        while True:
            try:
                current_time = time.time()
                
                # Periodic health check
                if current_time - last_health_check >= health_check_interval:
                    health = outbox_pattern.get_health_status()
                    
                    if not health['running'] or not health['thread_alive']:
                        logger.warning(f"⚠️ Worker {worker_id} unhealthy - restarting processor")
                        outbox_pattern.stop_background_processor()
                        time.sleep(2)
                        outbox_pattern.start_background_processor(
                            interval_seconds=getattr(settings, 'outbox_poll_interval', 5),
                            worker_id=f"outbox-worker-{worker_id}"
                        )
                    
                    logger.info(f"📊 Worker {worker_id} health - Running: {health['running']}, "
                               f"Processed: {health['processed_count']}, "
                               f"Errors: {health['error_count']}")
                    
                    last_health_check = current_time
                
                # Sleep before next iteration
                time.sleep(5)
                
            except KeyboardInterrupt:
                logger.info(f"🛑 Worker {worker_id} received interrupt - shutting down")
                break
            except Exception as e:
                logger.error(f"❌ Worker {worker_id} loop error: {e}")
                time.sleep(5)
        
        # Cleanup
        try:
            outbox_pattern.stop_background_processor()
            logger.info(f"✅ Worker {worker_id} stopped")
        except Exception as e:
            logger.error(f"❌ Worker {worker_id} cleanup error: {e}")
    
    def _coordinator_loop(self):
        """Coordinator main loop for monitoring and rebalancing"""
        while self.running:
            try:
                # Monitor worker health
                self._monitor_worker_health()
                
                # Check for rebalancing needs
                self._check_rebalancing()
                
                # Collect aggregate metrics
                self._collect_aggregate_metrics()
                
                # Sleep until next iteration
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"❌ Coordinator loop error: {e}")
                time.sleep(self.health_check_interval)
    
    def _monitor_worker_health(self):
        """Monitor health of all worker processes"""
        dead_workers = []
        
        for i, worker_process in enumerate(self.worker_processes):
            if not worker_process.is_alive():
                dead_workers.append(i)
                logger.warning(f"⚠️ Worker process {i} died")
        
        # Restart dead workers
        for worker_id in dead_workers:
            logger.info(f"🔄 Restarting dead worker {worker_id}")
            try:
                # Remove dead process
                del self.worker_processes[worker_id]
                
                # Start new process
                process = multiprocessing.Process(
                    target=self._run_worker_process,
                    args=(worker_id,),
                    name=f"outbox-worker-{worker_id}"
                )
                process.start()
                self.worker_processes.insert(worker_id, process)
                
                logger.info(f"✅ Restarted worker process {worker_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to restart worker {worker_id}: {e}")
    
    def _check_rebalancing(self):
        """Check if rebalancing is needed"""
        # TODO: Implement partition-based rebalancing logic
        # This would monitor Kafka partitions and redistribute work
        pass
    
    def _collect_aggregate_metrics(self):
        """Collect metrics from all workers"""
        try:
            # Get outbox metrics (aggregated across all workers)
            outbox_metrics = event_metrics_collector.get_outbox_metrics()
            
            # Log aggregate metrics
            logger.info(f"📊 Aggregate metrics - Total events: {outbox_metrics.total_events}, "
                       f"Pending: {outbox_metrics.pending_events}, "
                       f"Throughput: {outbox_metrics.throughput_events_per_second:.2f}/sec")
            
        except Exception as e:
            logger.error(f"❌ Failed to collect aggregate metrics: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status"""
        alive_workers = sum(1 for w in self.worker_processes if w.is_alive())
        
        return {
            "running": self.running,
            "total_workers": self.num_workers,
            "alive_workers": alive_workers,
            "dead_workers": self.num_workers - alive_workers,
            "worker_assignments": self.worker_assignments,
            "partition_assignments": self.partition_assignments,
            "timestamp": time.time()
        }

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {signum} - shutting down coordinator...")
    if coordinator:
        coordinator.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=getattr(settings, 'log_level', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start coordinator
    coordinator = WorkerCoordinator()
    
    try:
        coordinator.start()
        
        # Keep main thread alive
        while coordinator.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt - shutting down...")
        coordinator.stop()
    except Exception as e:
        logger.error(f"❌ Coordinator crashed: {e}")
        coordinator.stop()
        sys.exit(1)
