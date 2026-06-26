#!/bin/bash
# SRE-grade Prometheus rules validation
# Prevents monitoring outages from bad PromQL

set -e

RULES_FILE="/etc/prometheus/kafka-lag-rules.yml"
PROMTOOL="promtool"

echo "🔍 SRE RULE VALIDATION STARTED"

# 1. Syntax validation
echo "📝 Checking syntax..."
$PROMTOOL check rules $RULES_FILE
if [ $? -ne 0 ]; then
    echo "❌ SYNTAX ERROR - BLOCKING DEPLOY"
    exit 1
fi

# 2. Forbidden patterns check
echo "🚫 Checking for forbidden patterns..."

FORBIDDEN_PATTERNS=(
    "rate(vectorized_kafka_group_offset"
    "deriv("
    "group_left("
    "group_right("
    "on(topic,partition) group_left"
    "predict_linear("
)

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if grep -q "$pattern" $RULES_FILE; then
        echo "❌ FORBIDDEN PATTERN DETECTED: $pattern"
        echo "🚫 This pattern causes Prometheus crashes"
        exit 1
    fi
done

# 3. Required metrics check
echo "✅ Checking for required safe metrics..."

REQUIRED_METRICS=(
    "hcie_kafka_consumer_lag_total"
    "hcie_kafka_messages_consumed_5m"
    "hcie_kafka_messages_produced_5m"
    "hcie_kafka_lag_growth"
    "hcie_kafka_consumer_dead"
)

for metric in "${REQUIRED_METRICS[@]}"; do
    if ! grep -q "$metric" $RULES_FILE; then
        echo "❌ MISSING REQUIRED METRIC: $metric"
        exit 1
    fi
done

# 4. Safe pattern validation
echo "🛡️  Checking safe patterns..."

SAFE_PATTERNS=(
    "increase("
    "clamp_min("
    "sum("
    "max by("
)

safe_count=0
for pattern in "${SAFE_PATTERNS[@]}"; do
    if grep -q "$pattern" $RULES_FILE; then
        safe_count=$((safe_count + 1))
    fi
done

if [ $safe_count -lt 3 ]; then
    echo "❌ NOT ENOUGH SAFE PATTERNS - potential instability"
    exit 1
fi

echo "✅ ALL VALIDATIONS PASSED"
echo "🚀 Rules are production-safe"
exit 0
