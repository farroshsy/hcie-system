#!/usr/bin/env python3
"""
HCIE Research Worker Working - Manual Avro Decoding
Uses message_serializer directly for Avro decoding
"""

import sys
import redis
import json
import numpy as np
from scipy import stats
from datetime import datetime
from confluent_kafka import Consumer
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer
from confluent_kafka.avro import CachedSchemaRegistryClient

# Phase 8: Live Tournament Scoreboard
tournament_data = {
    "hcie": {"rewards": [], "n": 0},
    "dag": {"rewards": [], "n": 0},
    "random": {"rewards": [], "n": 0}
}

def record_tournament_event(policy, reward):
    """Record tournament event and run live significance testing"""
    if policy not in tournament_data: return
    
    # Accumulate raw data for significance testing
    tournament_data[policy]["rewards"].append(reward)
    tournament_data[policy]["n"] += 1
    
    # Every 10 events per policy, run a quick "Live Significance" check
    n_hcie = tournament_data["hcie"]["n"]
    n_rand = tournament_data["random"]["n"]
    
    if n_hcie >= 30 and n_rand >= 30:
        t_stat, p_val = stats.ttest_ind(
            tournament_data["hcie"]["rewards"], 
            tournament_data["random"]["rewards"], 
            equal_var=False
        )
        print(f"{'='*60}")
        print(f"{'='*60}")
        print("TOURNAMENT STATS: HCIE vs Random")
        print(f"HCIE Sample: {n_hcie} | Random Sample: {n_rand}")
        print(f"HCIE Mean: {np.mean(tournament_data['hcie']['rewards']):.3f}")
        print(f"Random Mean: {np.mean(tournament_data['random']['rewards']):.3f}")
        print(f"P-Value: {p_val:.4f} | {'SIGNIFICANT' if p_val < 0.05 else 'NOT SIGNIFICANT'}")
        print(f"{'='*60}")
        print(f"{'='*60}")

# Add OpenTelemetry metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("Prometheus client not available - metrics disabled")

# Metrics for Grafana Alerting
if METRICS_AVAILABLE:
    interaction_counter = Counter('hcie_interaction_reward_count', 'Total number of interactions', ['policy_mode', 'concept_id'])
    reward_histogram = Histogram('hcie_interaction_reward', 'Reward values', ['policy_mode', 'concept_id'])
    reward_sum = Gauge('hcie_interaction_reward_sum', 'Sum of rewards', ['policy_mode'])
    avg_reward = Gauge('hcie_avg_reward', 'Average reward across all interactions')
    
    # Start metrics server
    try:
        start_http_server(8888, addr='0.0.0.0')
        print("Prometheus metrics server started on port 8888")
    except Exception as e:
        print(f"Failed to start metrics server: {e}")

def main():
    """Main research worker function"""
    
    print("=== HCIE RESEARCH WORKING DECODER STARTING ===")
    print("Purpose: Decode Avro CDC events into readable research metrics")
    print("Topic: hcie.public.interactions")
    print("=" * 50)
    
    # Set up Redis connection for live dashboard
    try:
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        redis_client.ping()
        print("Redis connection established")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return 1
    
    # Set up Avro components
    schema_registry_url = 'http://schema-registry:8081'
    schema_registry_client = CachedSchemaRegistryClient(schema_registry_url)
    avro_serializer = MessageSerializer(schema_registry_client)
    
    # Configuration pointing to INTERNAL Docker services
    consumer_config = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'research-redis-v1',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }

    # Create regular Consumer
    try:
        consumer = Consumer(consumer_config)
        consumer.subscribe(['hcie.public.interactions'])
        print("Consumer created and subscribed successfully")
    except Exception as e:
        print(f"Failed to create Consumer: {e}")
        return 1
    
    print("\n" + "=" * 50)
    print("RESEARCH WORKING DECODER READY - Listening for interactions...")
    print("Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            # Decode key (string) and value (Avro)
            try:
                key = msg.key().decode('utf-8') if msg.key() else None
                
                # Decode Avro value manually
                try:
                    data = avro_serializer.decode_message(msg.value(), is_key=False)
                    
                    if 'after' in data:
                        res = data['after']
                        print(f"{'='*50}")
                        print(f"User: {res['user_id']} | Reward: {res['reward']} | Correct: {res['correct']}")
                        print(f"Policy: {res['policy_mode']} | Task: {res['task_id']}")
                        print(f"Concept: {res['concept_id']} | Response Time: {res['response_time']}s")
                        print(f"{'='*50}")
                        
                        # Persist to Redis for live dashboard
                        try:
                            user_id = res['user_id']
                            
                            # Store latest interaction data
                            redis_key = f"user:{user_id}:latest_interaction"
                            interaction_data = {
                                'user_id': user_id,
                                'reward': res['reward'],
                                'correct': res['correct'],
                                'policy_mode': res['policy_mode'],
                                'task_id': res['task_id'],
                                'concept_id': res['concept_id'],
                                'response_time': res['response_time'],
                                'timestamp': res.get('timestamp', datetime.now().isoformat())
                            }
                            redis_client.set(redis_key, json.dumps(interaction_data))
                            
                            # Store individual metrics for quick access
                            redis_client.set(f"user:{user_id}:last_reward", res['reward'])
                            redis_client.set(f"user:{user_id}:last_correct", int(res['correct']))
                            redis_client.set(f"user:{user_id}:last_policy", res['policy_mode'])
                            redis_client.set(f"user:{user_id}:last_concept", res['concept_id'])
                            redis_client.set(f"user:{user_id}:last_response_time", res['response_time'])
                            
                            # Update global metrics
                            redis_client.lpush("global:recent_interactions", json.dumps(interaction_data))
                            redis_client.ltrim("global:recent_interactions", 0, 99)  # Keep last 100
                            
                            # Update policy performance tracking
                            policy_key = f"policy:{res['policy_mode']}:total_reward"
                            redis_client.incrbyfloat(policy_key, res['reward'])
                            
                            print(f"Redis: Stored live metrics for user {user_id}")
                            
                            # Phase 8: Record tournament event
                            policy_mode = res['policy_mode']
                            reward = res['reward']
                            record_tournament_event(policy_mode, reward)
                            
                            # Update Prometheus metrics for Grafana Alerting
                            if METRICS_AVAILABLE:
                                try:
                                    concept_id = res['concept_id']
                                    
                                    # Update counters and histograms
                                    interaction_counter.labels(policy_mode=policy_mode, concept_id=concept_id).inc()
                                    reward_histogram.labels(policy_mode=policy_mode, concept_id=concept_id).observe(reward)
                                    
                                    # Update sum gauge
                                    reward_sum.labels(policy_mode=policy_mode).inc(reward)
                                    
                                    print(f"Prometheus: Updated metrics for {policy_mode}")
                                    
                                except Exception as metrics_error:
                                    print(f"Metrics error: {metrics_error}")
                            
                        except Exception as redis_error:
                            print(f"Redis error: {redis_error}")
                    
                except Exception as decode_error:
                    print(f"Decode error: {decode_error}")
                    print(f"Message key: {key}")
                    print(f"Value length: {len(msg.value())} bytes")
                    continue
                
                # Manual commit for research accuracy
                consumer.commit(asynchronous=False)
                
            except Exception as e:
                print(f"Error processing message: {e}")
                continue

    except KeyboardInterrupt:
        print("\nShutting down research working decoder...")
        consumer.close()
        print("Consumer closed successfully")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
