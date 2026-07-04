#!/bin/bash

# Debug script for PostgreSQL pipeline issue
# This will help us identify why PostgreSQL writes are failing

echo "=== HCIE Pipeline Debug Script ==="

# 1. Check PostgreSQL table structure
echo "1. Checking PostgreSQL table structure..."
docker exec docker-postgres-1 psql -U hcie_user -d hcie -c "\d interactions"

# 2. Check current PostgreSQL count
echo "2. Current PostgreSQL interaction count..."
docker exec docker-postgres-1 psql -U hcie_user -d hcie -c "SELECT COUNT(*) FROM interactions;"

# 3. Check Kafka topics
echo "3. Checking Kafka topics..."
docker exec docker-kafka-1 rpk topic list

# 4. Check Kafka topic messages
echo "4. Checking Kafka topic messages..."
docker exec docker-kafka-1 rpk topic consume hcie.submissions --num 5 --offset earliest || echo "No messages in hcie.submissions"

docker exec docker-kafka-1 rpk topic consume hcie.mastery --num 5 --offset earliest || echo "No messages in hcie.mastery"

# 5. Check API logs for errors
echo "5. Checking API logs for PostgreSQL errors..."
docker logs docker-api-1 --tail 50 | grep -i "postgres\|interaction\|error" || echo "No PostgreSQL errors found"

# 6. Check if analytics worker is running
echo "6. Checking analytics worker status..."
docker logs docker-api-1 --tail 20 | grep -i "analytics\|worker" || echo "No analytics worker logs found"

# 7. Test direct PostgreSQL insert
echo "7. Testing direct PostgreSQL insert..."
docker exec docker-postgres-1 psql -U hcie_user -d hcie -c "
INSERT INTO interactions (
    user_id, concept_id, representation, correct, reward, 
    response_time, difficulty, task_id, policy_mode, timestamp
) VALUES (
    'debug_test', 'debug_concept', 'debug_repr', true, 1.0, 10.0, 0.5, 'debug_task', 'debug_policy', NOW()
);
SELECT COUNT(*) FROM interactions;
"

# 8. Test API submission
echo "8. Testing API submission..."
curl -X GET "http://localhost:8001/api/v1/tasks/debug_pipeline_test" || echo "API not responding"

# 9. Check if interaction was saved
echo "9. Checking if interaction was saved..."
sleep 3
docker exec docker-postgres-1 psql -U hcie_user -d hcie -c "SELECT COUNT(*) FROM interactions;"
docker exec docker-postgres-1 psql -U hcie_user -d hcie -c "SELECT user_id, concept_id, correct, reward, timestamp FROM interactions WHERE user_id = 'debug_pipeline_test' ORDER BY timestamp DESC LIMIT 5;"

echo "=== Debug Complete ==="
echo "If you see the debug_test interaction in PostgreSQL but not pipeline_test interactions, the issue is in the Kafka worker."
echo "If you don't see any interactions, there's a PostgreSQL connection issue."
