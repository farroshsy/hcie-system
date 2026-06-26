#!/usr/bin/env python3
"""
Seed real tasks in database using existing connection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.postgres_store.interaction_store import get_postgres_interaction_store

def seed_tasks():
    """Seed real tasks for each CT concept"""
    
    # Get database connection
    store = get_postgres_interaction_store()
    
    # Define CT concepts and sample tasks
    ct_concepts = [
        "ct_problem_identification",
        "ct_decomposition", 
        "ct_algorithm_design",
        "ct_algorithm_tracing",
        "ct_pattern_recognition",
        "ct_abstraction",
        "ct_debugging",
        "ct_system_thinking",
        "ct_optimization"
    ]
    
    print("Seeding real tasks for CT concepts...")
    
    try:
        # Create tasks table if not exists
        store.execute_query("""
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR(255) PRIMARY KEY,
                concept_id VARCHAR(255) NOT NULL,
                question_text TEXT NOT NULL,
                correct_answer VARCHAR(255) NOT NULL,
                difficulty FLOAT DEFAULT 0.5,
                task_type VARCHAR(100) DEFAULT 'multiple_choice',
                choices TEXT,
                explanation TEXT,
                hint TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Seed tasks for each concept
        for i, concept in enumerate(ct_concepts):
            for j in range(5):  # 5 tasks per concept
                task_id = f"{concept}_task_{j+1}"
                
                # Create sample multiple choice task
                question_text = f"Practice {concept.replace('ct_', '').replace('_', ' ').title()} concept - Problem {j+1}"
                correct_answer = "85"
                
                choices = '{"A": "42", "B": "67", "C": "85", "D": "23"}'
                
                explanation = f"Good job! You mastered {concept.replace('ct_', '').replace('_', ' ').title()}."
                hint = f"Think about the key principles of {concept.replace('ct_', '').replace('_', ' ').title()}."
                
                # Insert task
                store.execute_query("""
                    INSERT INTO tasks (id, concept_id, question_text, correct_answer, difficulty, task_type, choices, explanation, hint)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, task_id, concept, question_text, correct_answer, 0.5 + (j * 0.1), 'multiple_choice', choices, explanation, hint)
                
                print(f"  Seeded task: {task_id}")
        
        # Verify tasks were inserted
        result = store.execute_query("SELECT COUNT(*) FROM tasks")
        print(f"\nTotal tasks in database: {result[0][0]}")
        
        print("Task seeding completed!")
        return True
        
    except Exception as e:
        print(f"Error seeding tasks: {e}")
        return False

if __name__ == "__main__":
    success = seed_tasks()
    exit(0 if success else 1)
