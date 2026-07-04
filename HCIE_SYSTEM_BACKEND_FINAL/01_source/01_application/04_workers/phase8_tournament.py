#!/usr/bin/env python3
"""
THIS IS OLD 
Phase 8: Live Tournament Engine
Real-time randomized policy evaluation with statistical significance testing
"""

import sys
import time
import redis
import json
import logging
import numpy as np
from scipy import stats
from datetime import datetime
from confluent_kafka import Consumer
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer
from confluent_kafka.avro import CachedSchemaRegistryClient

logger = logging.getLogger(__name__)

# Phase 8.2: Live Tournament Scoreboard with Multi-Metric Analysis
tournament_data = {
    "hcie": {"rewards": [], "gains": [], "n": 0},
    "dag": {"rewards": [], "gains": [], "n": 0},
    "random": {"rewards": [], "gains": [], "n": 0}
}

def record_tournament_event(policy, reward, learning_gain=0.0):
    """Record tournament event and run live significance testing"""
    if policy not in tournament_data: return
    
    # Accumulate raw data for significance testing
    tournament_data[policy]["rewards"].append(reward)
    tournament_data[policy]["gains"].append(learning_gain)
    tournament_data[policy]["n"] += 1
    
    # Run pairwise tests when samples are sufficient
    if all(tournament_data[p]["n"] >= 30 for p in ["hcie", "dag", "random"]):
        logger.info(f"\n{'='*60}")
        logger.info(f"{'='*60}")
        logger.info("PHASE 8.2: ZPD TOURNAMENT SIGNIFICANCE")
        logger.info(f"{'='*60}")

        pairs = [("hcie", "random"), ("hcie", "dag"), ("dag", "random")]
        for p1, p2 in pairs:
            _, p_val = stats.ttest_ind(
                tournament_data[p1]["rewards"],
                tournament_data[p2]["rewards"],
                equal_var=False
            )
            status = "SIGNIFICANT" if p_val < 0.05 else "NOT SIG"
            logger.info(f"   REWARD {p1.upper()} vs {p2.upper()}: p={p_val:.4f} | {status}")

        # Learning Gain Analysis
        logger.info(f"\n{'='*60}")
        logger.info("LEARNING GAIN ANALYSIS:")
        logger.info(f"{'='*60}")

        for p1, p2 in pairs:
            # Filter out None values from gains
            gains1 = [g for g in tournament_data[p1]["gains"] if g is not None]
            gains2 = [g for g in tournament_data[p2]["gains"] if g is not None]

            if len(gains1) > 0 and len(gains2) > 0:
                _, p_val = stats.ttest_ind(gains1, gains2, equal_var=False)
                status = "SIGNIFICANT" if p_val < 0.05 else "NOT SIG"
                logger.info(f"   GAIN   {p1.upper()} vs {p2.upper()}: p={p_val:.4f} | {status}")
            else:
                logger.info(f"   GAIN   {p1.upper()} vs {p2.upper()}: INSUFFICIENT DATA")

        logger.info(f"{'='*60}")
        logger.info(f"{'='*60}")

        # Show means for both metrics
        logger.info("CURRENT MEANS:")
        for policy in ["hcie", "dag", "random"]:
            if tournament_data[policy]["rewards"]:
                reward_mean = np.mean(tournament_data[policy]["rewards"])
                gains = [g for g in tournament_data[policy]["gains"] if g is not None]
                gain_mean = np.mean(gains) if gains else 0.0
                n = tournament_data[policy]["n"]
                logger.info(f"   {policy.upper()}: Reward={reward_mean:.3f}, Gain={gain_mean:.4f} (n={n})")
        logger.info(f"{'='*60}")
        logger.info(f"{'='*60}")

def main():
    """Main Phase 8 tournament function"""
    
    logger.info("=== PHASE 8: LIVE TOURNAMENT STARTING ===")
    logger.info("Purpose: Real-time randomized policy evaluation")
    logger.info("Topic: hcie.public.interactions")
    logger.info("=" * 60)

    # Set up Redis connection for live dashboard
    try:
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return 1
    
    # Set up Avro components
    schema_registry_url = 'http://schema-registry:8081'
    schema_registry_client = CachedSchemaRegistryClient(schema_registry_url)
    avro_serializer = MessageSerializer(schema_registry_client)
    
    # Configuration pointing to INTERNAL Docker services
    consumer_config = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'research-tournament-v8-final',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }

    # Create Consumer
    try:
        consumer = Consumer(consumer_config)
        consumer.subscribe(['hcie.public.interactions'])
        logger.info("Consumer created and subscribed successfully")
    except Exception as e:
        logger.error(f"Failed to create Consumer: {e}")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 8 TOURNAMENT READY - Listening for interactions...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60 + "\n")
    
    interaction_count = 0
    start_time = datetime.now()
    last_heartbeat = time.time()
    
    try:
        while True:
            # Poll for messages (1 second timeout)
            msg = consumer.poll(1.0)
            
            # HEARTBEAT: Show life every 30 seconds if nothing is happening
            if time.time() - last_heartbeat > 30:
                logger.debug(f"[{datetime.now().strftime('%H:%M:%S')}] HEARTBEAT: Worker Alive. "
                      f"Total Processed: {interaction_count} | "
                      f"Samples: HCIE({tournament_data['hcie']['n']}) "
                      f"RAND({tournament_data['random']['n']})")
                last_heartbeat = time.time()

            if msg is None:
                continue

            # Reset heartbeat timer when data is received
            last_heartbeat = time.time()

            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue
            
            # Handle the message
            try:
                interaction_count += 1
                
                # Decode key (string) and value (Avro)
                key = msg.key().decode('utf-8') if msg.key() else None
                
                # Decode Avro value manually
                try:
                    data = avro_serializer.decode_message(msg.value(), is_key=False)
                    
                    if 'after' in data:
                        res = data['after']

                        logger.debug(f"{'='*60}")
                        logger.debug(f"INTERACTION #{interaction_count} - {datetime.now().strftime('%H:%M:%S')}")
                        logger.debug(f"{'='*60}")
                        logger.debug(f"Key: {key}")
                        logger.debug(f"User: {res['user_id']} | Reward: {res['reward']} | Correct: {res['correct']}")
                        logger.debug(f"Policy: {res['policy_mode']} | Task: {res['task_id']}")
                        logger.debug(f"Concept: {res['concept_id']} | Response Time: {res['response_time']}s")
                        logger.debug(f"{'='*60}")
                        
                        # Phase 8.2: Record tournament event with learning gain
                        policy_mode = res['policy_mode']
                        reward = res['reward']
                        learning_gain = res.get('learning_gain', 0.0)
                        record_tournament_event(policy_mode, reward, learning_gain)
                        
                        # Store in Redis for live dashboard
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
                            
                            # Update global metrics
                            redis_client.lpush("global:recent_interactions", json.dumps(interaction_data))
                            redis_client.ltrim("global:recent_interactions", 0, 99)
                            
                            logger.debug(f"Redis: Stored tournament data for {policy_mode}")

                        except Exception as redis_error:
                            logger.error(f"Redis error: {redis_error}")

                except Exception as decode_error:
                    logger.error(f"Decode error: {decode_error}")
                    continue

                # Manual commit for research accuracy
                consumer.commit(asynchronous=False)

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        logger.info("\n\nShutting down Phase 8 tournament...")
        logger.info(f"Total interactions processed: {interaction_count}")
        logger.info(f"Running time: {datetime.now() - start_time}")

        # Final tournament summary
        logger.info(f"\n{'='*60}")
        logger.info("FINAL PHASE 8.2 TOURNAMENT RESULTS")
        logger.info(f"{'='*60}")
        for policy, data in tournament_data.items():
            if data['rewards']:
                gains = [g for g in data['gains'] if g is not None]
                logger.info(f"{policy.upper()}:")
                logger.info(f"  Sample Size: {len(data['rewards'])}")
                logger.info(f"  Mean Reward: {np.mean(data['rewards']):.3f}")
                logger.info(f"  Mean Gain: {np.mean(gains):.4f}" if gains else "  Mean Gain: N/A")
                logger.info(f"  Reward Std Dev: {np.std(data['rewards']):.3f}")
                logger.info(f"  Gain Std Dev: {np.std(gains):.4f}" if gains else "  Gain Std Dev: N/A")
                logger.info("")

    finally:
        # Close consumer gracefully
        try:
            consumer.close()
            logger.info("Consumer closed successfully")
        except:
            pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
