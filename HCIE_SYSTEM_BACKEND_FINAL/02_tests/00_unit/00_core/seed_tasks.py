#!/usr/bin/env python3
"""
Seed real tasks in database to enable end-to-end learning validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import asyncpg
from datetime import datetime

async def seed_tasks():
    """Seed real tasks for each CT concept"""
    
    # Database connection
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="hcie_db"
    )
    
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
    
    # Create tasks table if not exists
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(255) PRIMARY KEY,
            concept_id VARCHAR(255) NOT NULL,
            question_text TEXT NOT NULL,
            correct_answer VARCHAR(255) NOT NULL,
            difficulty FLOAT DEFAULT 0.5,
            task_type VARCHAR(100) DEFAULT 'multiple_choice',
            choices JSON,
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
            
            choices = [
                {"id": "A", "text": "42"},
                {"id": "B", "text": "67"}, 
                {"id": "C", "text": "85"},
                {"id": "D", "text": "23"}
            ]
            
            explanation = f"Good job! You mastered {concept.replace('ct_', '').replace('_', ' ').title()}."
            hint = f"Think about the key principles of {concept.replace('ct_', '').replace('_', ' ').title()}."
            
            await conn.execute("""
                INSERT INTO tasks (id, concept_id, question_text, correct_answer, difficulty, task_type, choices, explanation, hint)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO NOTHING
            """, task_id, concept, question_text, correct_answer, 0.5 + (j * 0.1), 'multiple_choice', choices, explanation, hint)
            
            print(f"  Seeded task: {task_id}")
    
    # Verify tasks were inserted
    result = await conn.fetchval("SELECT COUNT(*) FROM tasks")
    print(f"\nTotal tasks in database: {result}")
    
    await conn.close()
    print("Task seeding completed!")

if __name__ == "__main__":
    asyncio.run(seed_tasks())
