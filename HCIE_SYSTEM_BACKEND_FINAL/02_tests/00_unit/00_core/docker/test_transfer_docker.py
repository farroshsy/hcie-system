from core.learning.transfer_learning_engine import TransferLearningEngine

print('=== TRANSFER ENGINE DOCKER TEST ===')

# Initialize transfer engine
te = TransferLearningEngine()
print(f'Transfer engine initialized')
print(f'DAG size: {len(te.dependencies)}')

# Show some dependencies
print(f'Sample concepts: {list(te.dependencies.keys())[:5]}')

# Test transfer calculation
test_concept = 'ct_pattern_recognition'
if test_concept in te.dependencies:
    deps = te.dependencies[test_concept]
    print(f'{test_concept} has {len(deps)} dependencies:')
    for dep in deps:
        print(f'  → {dep.target_concept} (weight={dep.transfer_weight})')
        
        # Calculate transfer amount
        transfer_amount = te.calculate_transfer_amount(
            source_concept=test_concept,
            target_concept=dep.target_concept,
            mastery_change=0.05,
            confidence=0.8,
            learning_gain=0.05
        )
        
        applies = transfer_amount >= te.min_transfer_threshold
        print(f'    Transfer amount: {transfer_amount:.6f} {"✅" if applies else "❌"}')
        
        # Test process_mastery_update
        transfers, events = te.process_mastery_update(
            user_id='test_user',
            concept=test_concept,
            mastery_before=0.3,
            mastery_after=0.35,
            confidence=0.8,
            learning_gain=0.05
        )
        
        print(f'    Process result: {len(transfers)} transfers, {len(events)} events')
        if transfers:
            for key, amount in transfers.items():
                print(f'      {key}: +{amount:.6f}')
else:
    print(f'{test_concept} not found in DAG')

print('✅ TRANSFER ENGINE TEST COMPLETE')
