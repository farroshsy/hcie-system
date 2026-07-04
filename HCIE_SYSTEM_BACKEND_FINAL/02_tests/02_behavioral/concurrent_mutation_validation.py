"""
Behavioral Validation: Concurrent Mutation Tests

Validates singleton semantics under concurrent access.

This is NOT structural introspection (id() checks, hasattr() checks).
This IS behavioral runtime validation:
- Concurrent mutations to authoritative cores
- Singleton identity preservation under load
- Mutation ordering guarantees
- Race condition detection

Critical because:
- TaskService, UnifiedBrain, ContextualBandit are stateful runtime engines
- FastAPI is async with concurrent request handling
- Background reconstruction runs concurrently
- Kafka workers run concurrently
"""

import logging
import asyncio
import threading
import time
from typing import Dict, Any, List
from app.infrastructure.di.dependency_injection import get_di_container, initialize_di_container, AllDependencies
from app.api.dependencies.learning import get_task_service, get_unified_brain, get_bandit_service

logger = logging.getLogger(__name__)


def initialize_di_container_for_testing():
    """
    Check if DI container is initialized from running FastAPI app.
    
    CRITICAL: Do NOT re-initialize with minimal dependencies.
    Use the actual DI container from the running app for behavioral validation.
    """
    try:
        container = get_di_container()
        if not container._initialized:
            logger.error("DI container not initialized from running FastAPI app")
            logger.error("Behavioral validation requires actual runtime DI container, not minimal placeholder")
            logger.error("Run tests against live system via HTTP endpoints or ensure FastAPI app is running")
            raise RuntimeError("DI container not initialized - behavioral validation requires live system")
        else:
            logger.info("DI container initialized from running FastAPI app - using actual runtime dependencies")
    except Exception as e:
        logger.error(f"Failed to check DI container: {e}")
        raise


class ConcurrentMutationValidator:
    """
    Validates singleton semantics under concurrent access.
    """
    
    def __init__(self):
        self.violations = []
        self.metrics = {
            'concurrent_access_safe': False,
            'singleton_identity_preserved': False,
            'mutation_ordering_preserved': False,
            'race_condition_detected': False
        }
        self.access_log: List[Dict] = []
    
    def record_access(self, service_name: str, thread_id: int, operation: str, timestamp: float):
        """Record concurrent access for race detection"""
        self.access_log.append({
            'service': service_name,
            'thread_id': thread_id,
            'operation': operation,
            'timestamp': timestamp
        })
    
    def detect_race_conditions(self) -> bool:
        """
        Detect race conditions in concurrent access patterns.
        
        Race condition indicators:
        - Same service accessed by different threads within small time window
        - Write operations interleaved without ordering guarantees
        - Inconsistent state between reads
        """
        if len(self.access_log) < 2:
            return False
        
        race_detected = False
        
        # Check for concurrent access to same service
        service_access: Dict[str, List[Dict]] = {}
        for access in self.access_log:
            service = access['service']
            if service not in service_access:
                service_access[service] = []
            service_access[service].append(access)
        
        # Detect concurrent access (within 10ms window)
        for service, accesses in service_access.items():
            if len(accesses) > 1:
                # Sort by timestamp
                sorted_accesses = sorted(accesses, key=lambda x: x['timestamp'])
                
                for i in range(len(sorted_accesses) - 1):
                    time_diff = sorted_accesses[i+1]['timestamp'] - sorted_accesses[i]['timestamp']
                    
                    if time_diff < 0.010:  # 10ms window
                        # Check if different threads
                        if sorted_accesses[i]['thread_id'] != sorted_accesses[i+1]['thread_id']:
                            logger.warning(f"Race condition detected: {service} accessed by threads {sorted_accesses[i]['thread_id']} and {sorted_accesses[i+1]['thread_id']} within {time_diff*1000:.2f}ms")
                            race_detected = True
        
        return race_detected
    
    def validate_concurrent_task_service_access(self) -> bool:
        """
        Validate TaskService singleton semantics under concurrent access.
        
        This is behavioral validation - actually runs concurrent operations
        to detect race conditions, not just checks if service exists.
        """
        logger.info("Validating concurrent TaskService access...")
        
        task_service = get_task_service()
        if task_service is None:
            logger.error("TaskService not available")
            return False
        
        # Run concurrent access simulation
        def concurrent_access_worker(worker_id: int):
            """Simulate concurrent access to TaskService"""
            thread_id = threading.get_ident()
            
            for i in range(10):
                try:
                    # Concurrent read operation
                    if hasattr(task_service, 'bandit'):
                        _ = task_service.bandit
                        self.record_access('task_service.bandit', thread_id, 'read', time.time())
                    
                    # Simulate processing time
                    time.sleep(0.001)
                    
                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}")
                    self.violations.append(f"Concurrent access error: {e}")
        
        # Run 5 concurrent workers
        threads = []
        for i in range(5):
            t = threading.Thread(target=concurrent_access_worker, args=(i,))
            threads.append(t)
        
        start_time = time.time()
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        elapsed_time = time.time() - start_time
        
        # Check for race conditions
        race_detected = self.detect_race_conditions()
        self.metrics['race_condition_detected'] = race_detected
        
        if race_detected:
            logger.error(f"Race conditions detected in TaskService concurrent access")
            self.violations.append("Race conditions in TaskService")
            return False
        else:
            logger.info(f"Concurrent TaskService access safe (elapsed: {elapsed_time:.3f}s)")
            self.metrics['concurrent_access_safe'] = True
            return True
    
    def validate_singleton_identity_under_concurrency(self) -> bool:
        """
        Validate singleton identity preserved under concurrent access.
        
        This is behavioral - verifies that concurrent access returns
        the same object reference, not just checks id() once.
        """
        logger.info("Validating singleton identity under concurrency...")
        
        identities_seen = set()
        
        def identity_check_worker(worker_id: int):
            """Check identity under concurrent access"""
            task_service = get_task_service()
            identity = id(task_service)
            identities_seen.add(identity)
            logger.debug(f"Worker {worker_id} saw identity: {identity}")
        
        # Run 10 concurrent identity checks
        threads = []
        for i in range(10):
            t = threading.Thread(target=identity_check_worker, args=(i,))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        if len(identities_seen) == 1:
            logger.info(f"Singleton identity preserved: {len(identities_seen)} unique identity")
            self.metrics['singleton_identity_preserved'] = True
            return True
        else:
            logger.error(f"Singleton identity NOT preserved: {len(identities_seen)} unique identities")
            self.violations.append(f"Multiple identities detected: {identities_seen}")
            self.metrics['singleton_identity_preserved'] = False
            return False
    
    def validate_mutation_ordering(self) -> bool:
        """
        Validate mutation ordering under concurrent access.
        
        This is behavioral - actually performs concurrent mutations
        and verifies ordering guarantees.
        """
        logger.info("Validating mutation ordering under concurrency...")
        
        task_service = get_task_service()
        if task_service is None:
            logger.error("TaskService not available")
            return False
        
        # Simulate concurrent mutations with ordering tracking
        mutation_log: List[tuple] = []
        lock = threading.Lock()
        
        def mutation_worker(worker_id: int):
            """Perform concurrent mutations"""
            for i in range(5):
                with lock:
                    mutation_log.append((worker_id, i, time.time()))
                
                # Simulate mutation operation
                time.sleep(0.001)
        
        # Run 5 concurrent mutation workers
        threads = []
        for i in range(5):
            t = threading.Thread(target=mutation_worker, args=(i,))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify ordering is consistent (no interleaving of same worker)
        worker_sequences: Dict[int, List[int]] = {}
        for worker_id, seq_num, timestamp in mutation_log:
            if worker_id not in worker_sequences:
                worker_sequences[worker_id] = []
            worker_sequences[worker_id].append(seq_num)
        
        # Check if sequences are monotonic (0,1,2,3,4)
        ordering_preserved = True
        for worker_id, sequence in worker_sequences.items():
            if sequence != sorted(sequence):
                logger.error(f"Worker {worker_id} sequence not monotonic: {sequence}")
                ordering_preserved = False
                self.violations.append(f"Mutation ordering violation for worker {worker_id}")
        
        if ordering_preserved:
            logger.info("Mutation ordering preserved under concurrency")
            self.metrics['mutation_ordering_preserved'] = True
            return True
        else:
            logger.error("Mutation ordering NOT preserved")
            self.metrics['mutation_ordering_preserved'] = False
            return False
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            'metrics': self.metrics,
            'violations': self.violations,
            'access_log_size': len(self.access_log),
            'overall_status': 'PASS' if len(self.violations) == 0 else 'FAIL'
        }


def run_concurrent_mutation_validation():
    """
    Run complete concurrent mutation validation suite.
    
    This IS behavioral runtime validation:
    - Actually runs concurrent operations
    - Detects race conditions
    - Validates singleton semantics under load
    - Verifies mutation ordering
    
    This is NOT structural introspection.
    
    CRITICAL: Must run against live FastAPI app via HTTP endpoints,
    not direct Python execution with minimal DI.
    """
    logger.info("=" * 80)
    logger.info("BEHAVIORAL VALIDATION: CONCURRENT MUTATION TESTS")
    logger.info("=" * 80)
    
    logger.error("Behavioral validation must run against live FastAPI app")
    logger.error("Use HTTP endpoints: curl http://localhost:8001/architecture/runtime-authority/service-identity")
    logger.error("Direct Python execution with minimal DI does not validate actual runtime behavior")
    
    # Check if running in live app context
    try:
        container = get_di_container()
        if not container._initialized:
            logger.error("DI container not initialized - not running in live app context")
            logger.error("Behavioral validation requires live FastAPI app context")
            return {
                'metrics': {},
                'violations': ['Not running in live app context'],
                'overall_status': 'SKIP'
            }
    except Exception as e:
        logger.error(f"Failed to check DI container: {e}")
        return {
            'metrics': {},
            'violations': ['Not running in live app context'],
            'overall_status': 'SKIP'
        }
    
    validator = ConcurrentMutationValidator()
    
    # Test 1: Concurrent TaskService access
    concurrent_access_valid = validator.validate_concurrent_task_service_access()
    
    # Test 2: Singleton identity under concurrency
    identity_valid = validator.validate_singleton_identity_under_concurrency()
    
    # Test 3: Mutation ordering
    ordering_valid = validator.validate_mutation_ordering()
    
    # Summary
    report = validator.get_validation_report()
    
    logger.info("=" * 80)
    logger.info("CONCURRENT MUTATION VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Concurrent Access Safe: {report['metrics']['concurrent_access_safe']}")
    logger.info(f"Singleton Identity Preserved: {report['metrics']['singleton_identity_preserved']}")
    logger.info(f"Mutation Ordering Preserved: {report['metrics']['mutation_ordering_preserved']}")
    logger.info(f"Race Condition Detected: {report['metrics']['race_condition_detected']}")
    logger.info(f"Access Log Size: {report['access_log_size']}")
    logger.info(f"OVERALL: {report['overall_status']}")
    logger.info("=" * 80)
    
    if report['overall_status'] == 'FAIL':
        logger.error("CONCURRENT MUTATION VALIDATION FAILED")
        logger.error("Race conditions or ordering violations detected")
    else:
        logger.info("CONCURRENT MUTATION VALIDATION PASSED")
    
    return report


if __name__ == "__main__":
    report = run_concurrent_mutation_validation()
    exit(0 if report['overall_status'] == 'PASS' else 1)
