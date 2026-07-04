#!/usr/bin/env python3
"""
Test the complete learning loop with REAL mastery updates
"""

from app.services.service_factory import ServiceFactory
from app.models.requests import TaskSubmission
from datetime import datetime

def test_real_learning_loop():
    """Test the complete learning loop with REAL mastery updates"""
    
    sf = ServiceFactory()
    task_service = sf.get_task_service()
    
    user_id = 'real_learning_test'
    concept = 'k2_algorithms'
    
    print('🎯 REAL LEARNING LOOP TEST')
    print('=' * 40)
    
    # Step 1: Get initial mastery
    initial_candidates = task_service._get_candidate_tasks(user_id, concept_filter=[concept])
    initial_task = initial_candidates[0] if initial_candidates else None
    print(f'Initial task: {initial_task["task_id"] if initial_task else "None"}')
    
    # Step 2: Simulate task submission
    if initial_task:
        submission = TaskSubmission(
            user_id=user_id,
            task_id=initial_task['task_id'],
            node_id=concept,
            answer='correct_answer',  # Simulate correct answer
            response_time=20.0,
            representation='text',
            learner_mode='lyapunov'
        )
        
        print(f'\n📝 Submitting task: {submission.task_id}')
        print(f'   Answer: {submission.answer}')
        print(f'   Response time: {submission.response_time}s')
        
        # Process submission (this should now update mastery via UnifiedLearningBrain)
        result = task_service.process_submission(submission)
        print(f'\n✅ Submission processed!')
        print(f'   Success: {result.get("success")}')
        print(f'   Mastery after: {result.get("mastery_after", "N/A")}')
    
    # Step 3: Check if mastery actually updated
    final_candidates = task_service._get_candidate_tasks(user_id, concept_filter=[concept])
    mastery_context = task_service._get_mastery_context(user_id, final_candidates)
    
    print(f'\n🔍 FINAL MASTERY CHECK:')
    print(f'   Mastery context: {mastery_context}')
    print(f'   Concept mastery: {mastery_context.get(concept, "N/A")}')
    
    # Step 4: Test with another submission to see cumulative effect
    if initial_task:
        submission2 = TaskSubmission(
            user_id=user_id,
            task_id=initial_task['task_id'],
            node_id=concept,
            answer='wrong_answer',  # Simulate wrong answer
            response_time=45.0,
            representation='text',
            learner_mode='lyapunov'
        )
        
        print(f'\n📝 Submitting WRONG answer to test decrease...')
        result2 = task_service.process_submission(submission2)
        
        # Check mastery again
        final_mastery_context = task_service._get_mastery_context(user_id, final_candidates)
        final_mastery = final_mastery_context.get(concept, 'N/A')
        
        print(f'\n🎉 CUMULATIVE LEARNING RESULT:')
        print(f'   Final mastery: {final_mastery}')
        print(f'   Mastery changed: {"YES" if final_mastery != 0.3 else "NO"}')
        
        if final_mastery != 0.3:
            print('✅ REAL MASTERY UPDATES WORKING!')
        else:
            print('❌ Mastery still not updating')

if __name__ == "__main__":
    test_real_learning_loop()
