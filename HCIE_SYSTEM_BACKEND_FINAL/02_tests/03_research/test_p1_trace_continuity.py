"""
P1 - Trace Continuity Validation

Validates trace_id, span_id, parent_span_id across full event chain:
API → Outbox → Kafka → Consumer → Derived Events

This ensures distributed tracing continuity for:
- Replay lineage reconstruction
- Distributed debugging
- Causal dependency tracking
- Performance analysis across async boundaries
"""

import subprocess
import time
import requests
import json
from typing import Dict, Any, Optional

def submit_task_attempt():
    """Submit a task attempt via API to generate trace"""
    response = requests.post(
        'http://localhost:8001/api/learning/frontend/answer',
        json={
            'user_id': 'test_p1_trace',
            'concept': 'k2_computing_systems_devices',
            'correct': True,
            'response_time': 5.0
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get('processing_id')
    else:
        raise Exception(f"API request failed: {response.status_code}")

def capture_outbox_event(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Capture TaskAttemptSubmitted event from outbox_event_envelopes table.
    
    Returns trace context fields from outbox event.
    """
    try:
        cmd = [
            "docker", "exec", "docker-postgres-1",
            "psql", "-U", "hcie_user", "-d", "hcie",
            "-c",
            f"SELECT id, event_id, event_type, topic, envelope, correlation_id, causation_id, source_service, created_at FROM outbox_event_envelopes WHERE event_id = '{event_id}' ORDER BY created_at DESC LIMIT 1;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:
            data_line = lines[2].split('|')
            envelope_str = data_line[4].strip()
            
            # Parse envelope JSON
            envelope = json.loads(envelope_str)
            
            return {
                "id": data_line[0].strip(),
                "event_id": data_line[1].strip(),
                "event_type": data_line[2].strip(),
                "topic": data_line[3].strip(),
                "correlation_id": data_line[5].strip(),
                "causation_id": data_line[6].strip(),
                "source_service": data_line[7].strip(),
                "envelope": envelope
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Failed to capture outbox event: {e}")
        return None

def capture_derived_event(original_event_id: str) -> Optional[Dict[str, Any]]:
    """
    Capture LearningProcessed event from outbox_event_envelopes table.
    
    Returns trace context fields from derived event.
    """
    try:
        derived_event_id = f"{original_event_id}_processed"
        cmd = [
            "docker", "exec", "docker-postgres-1",
            "psql", "-U", "hcie_user", "-d", "hcie",
            "-c",
            f"SELECT id, event_id, event_type, topic, envelope, correlation_id, causation_id, source_service, created_at FROM outbox_event_envelopes WHERE event_id = '{derived_event_id}' ORDER BY created_at DESC LIMIT 1;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:
            data_line = lines[2].split('|')
            envelope_str = data_line[4].strip()
            
            # Parse envelope JSON
            envelope = json.loads(envelope_str)
            
            return {
                "id": data_line[0].strip(),
                "event_id": data_line[1].strip(),
                "event_type": data_line[2].strip(),
                "topic": data_line[3].strip(),
                "correlation_id": data_line[5].strip(),
                "causation_id": data_line[6].strip(),
                "source_service": data_line[7].strip(),
                "envelope": envelope
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Failed to capture derived event: {e}")
        return None

def extract_trace_context(envelope: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract trace context from event envelope.
    
    Returns trace_id, span_id, parent_span_id if present.
    """
    trace_context = {
        "trace_id": None,
        "span_id": None,
        "parent_span_id": None
    }
    
    metadata = envelope.get('metadata', {})
    payload = envelope.get('payload', {})
    
    # Check metadata for trace context
    if 'trace_id' in metadata:
        trace_context['trace_id'] = metadata['trace_id']
    if 'span_id' in metadata:
        trace_context['span_id'] = metadata['span_id']
    if 'parent_span_id' in metadata:
        trace_context['parent_span_id'] = metadata['parent_span_id']
    
    # Check payload for trace context (B3.6 injection)
    if 'trace_id' in payload:
        trace_context['trace_id'] = payload['trace_id']
    
    return trace_context

def validate_trace_continuity(outbox_event: Dict[str, Any], derived_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate trace continuity across event chain.
    
    Checks:
    - trace_id is present and consistent across events
    - span_id is present and unique per event
    - parent_span_id establishes correct causal chain
    - correlation_id/ causation_id establish event lineage
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "trace_chain": {}
    }
    
    # Extract trace contexts
    outbox_trace = extract_trace_context(outbox_event['envelope'])
    derived_trace = extract_trace_context(derived_event['envelope'])
    
    result['trace_chain']['outbox_event'] = outbox_trace
    result['trace_chain']['derived_event'] = derived_trace
    
    # Validate trace_id presence
    if not outbox_trace['trace_id']:
        result['errors'].append("Missing trace_id in outbox event")
        result['valid'] = False
    
    if not derived_trace['trace_id']:
        result['errors'].append("Missing trace_id in derived event")
        result['valid'] = False
    
    # Validate trace_id continuity
    if outbox_trace['trace_id'] and derived_trace['trace_id']:
        if outbox_trace['trace_id'] != derived_trace['trace_id']:
            result['errors'].append(f"Trace ID mismatch: outbox={outbox_trace['trace_id']}, derived={derived_trace['trace_id']}")
            result['valid'] = False
        else:
            print(f"✅ Trace ID continuity: {outbox_trace['trace_id']}")
    
    # Validate span_id presence
    if not outbox_trace['span_id']:
        result['warnings'].append("Missing span_id in outbox event")
    
    if not derived_trace['span_id']:
        result['warnings'].append("Missing span_id in derived event")
    
    # Validate span_id uniqueness
    if outbox_trace['span_id'] and derived_trace['span_id']:
        if outbox_trace['span_id'] == derived_trace['span_id']:
            result['errors'].append(f"Span ID collision: both events have same span_id={outbox_trace['span_id']}")
            result['valid'] = False
        else:
            print(f"✅ Span ID uniqueness: outbox={outbox_trace['span_id']}, derived={derived_trace['span_id']}")
    
    # Validate parent_span_id causal chain
    if derived_trace['parent_span_id']:
        if derived_trace['parent_span_id'] == outbox_trace['span_id']:
            print(f"✅ Parent span ID correct: derived parent={derived_trace['parent_span_id']} matches outbox span={outbox_trace['span_id']}")
        else:
            result['warnings'].append(f"Parent span ID mismatch: derived parent={derived_trace['parent_span_id']}, outbox span={outbox_trace['span_id']}")
    
    # Validate causation_id lineage
    if derived_event['causation_id']:
        if derived_event['causation_id'] == outbox_event['event_id']:
            print(f"✅ Causation ID correct: derived causation={derived_event['causation_id']} matches outbox event_id={outbox_event['event_id']}")
        else:
            result['errors'].append(f"Causation ID mismatch: derived causation={derived_event['causation_id']}, outbox event_id={outbox_event['event_id']}")
            result['valid'] = False
    else:
        result['warnings'].append("Missing causation_id in derived event")
    
    # Validate correlation_id continuity
    if outbox_event['correlation_id'] and derived_event['correlation_id']:
        if outbox_event['correlation_id'] == derived_event['correlation_id']:
            print(f"✅ Correlation ID continuity: {outbox_event['correlation_id']}")
        else:
            result['warnings'].append(f"Correlation ID mismatch: outbox={outbox_event['correlation_id']}, derived={derived_event['correlation_id']}")
    
    return result

def test_trace_continuity():
    """
    Main test function for P1 Trace Continuity Validation.
    """
    print("=" * 80)
    print("P1 - Trace Continuity Validation")
    print("=" * 80)
    
    try:
        # Step 1: Submit task attempt
        print("\n📝 Step 1: Submitting task attempt...")
        event_id = submit_task_attempt()
        print(f"✅ Event submitted: {event_id}")
        
        # Step 2: Wait for async processing
        print("\n⏳ Step 2: Waiting for async processing...")
        time.sleep(10)
        
        # Step 3: Capture outbox event
        print("\n📦 Step 3: Capturing outbox event...")
        outbox_event = capture_outbox_event(event_id)
        
        if not outbox_event:
            print("❌ Failed to capture outbox event")
            return
        
        print(f"✅ Outbox event captured: {outbox_event['event_id']}")
        print(f"   Event type: {outbox_event['event_type']}")
        print(f"   Topic: {outbox_event['topic']}")
        
        # Step 4: Capture derived event
        print("\n📊 Step 4: Capturing derived event...")
        derived_event = capture_derived_event(event_id)
        
        if not derived_event:
            print("❌ Failed to capture derived event")
            return
        
        print(f"✅ Derived event captured: {derived_event['event_id']}")
        print(f"   Event type: {derived_event['event_type']}")
        print(f"   Topic: {derived_event['topic']}")
        
        # Step 5: Validate trace continuity
        print("\n🔍 Step 5: Validating trace continuity...")
        result = validate_trace_continuity(outbox_event, derived_event)
        
        # Step 6: Report results
        print("\n" + "=" * 80)
        print("TRACE CONTINUITY VALIDATION RESULTS")
        print("=" * 80)
        
        print(f"\nStatus: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
        
        if result['errors']:
            print(f"\n❌ Errors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"   - {error}")
        
        if result['warnings']:
            print(f"\n⚠️  Warnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"   - {warning}")
        
        print("\n📊 Trace Chain:")
        print(f"   Outbox Event: {result['trace_chain']['outbox_event']}")
        print(f"   Derived Event: {result['trace_chain']['derived_event']}")
        
        print("\n" + "=" * 80)
        
        if result['valid']:
            print("✅ P1 VALIDATION PASSED: Trace continuity established across event chain")
        else:
            print("❌ P1 VALIDATION FAILED: Trace continuity broken")
        
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return {"valid": False, "errors": [str(e)], "warnings": [], "trace_chain": {}}

if __name__ == "__main__":
    test_trace_continuity()
