"""Seed task-backed K-12 catalog entries for cohort smoke runs.

Revision ID: 015_seed_cohort_k12_task_catalog
Revises: 014_bandit_persistence
Create Date: 2026-05-21 00:00:00.000000

Slice 4 cohorts call the canonical /v3/learner/recommend endpoint, which
requires task-backed K-12 concept IDs. This migration keeps that catalog
contract in Alembic instead of relying on runtime fallback data.
"""

from alembic import op


revision = "015_seed_cohort_k12_task_catalog"
down_revision = "014_bandit_persistence"


TASKS = [
    (
        "k2_control_text_v1",
        "Follow a Repeat Pattern",
        "Identify repetition in a simple routine",
        "k2_control",
        0.25,
        1,
        "text",
        '{"question": "Which routine repeats the same step?"}' ,
        '{"explanation": "A repeated step is the beginning of loop reasoning."}',
    ),
    (
        "k5_control_text_v1",
        "Trace a Loop",
        "Trace repeated instructions in a short program",
        "k5_control",
        0.45,
        2,
        "text",
        '{"question": "How many times does the repeated instruction run?"}',
        '{"explanation": "Count each iteration of the loop body."}',
    ),
    (
        "k8_control_code_v1",
        "Choose Loop Conditions",
        "Select an appropriate loop condition",
        "k8_control",
        0.65,
        3,
        "code",
        '{"task": "Pick a condition that stops after five iterations."}',
        '{"explanation": "The loop condition controls when repetition stops."}',
    ),
    (
        "k12_control_code_v1",
        "Reason About Nested Control",
        "Analyze nested control flow",
        "k12_control",
        0.8,
        4,
        "code",
        '{"task": "Explain how nested loops change total work."}',
        '{"explanation": "Nested loops multiply the number of executed steps."}',
    ),
    (
        "k8_algorithms_text_v1",
        "Compare Algorithm Strategies",
        "Compare two algorithms for the same goal",
        "k8_algorithms",
        0.6,
        3,
        "text",
        '{"question": "Which algorithm uses fewer steps and why?"}',
        '{"explanation": "Algorithm quality can be compared by the work required."}',
    ),
    (
        "k12_algorithms_code_v1",
        "Analyze Algorithm Efficiency",
        "Reason about algorithm efficiency",
        "k12_algorithms",
        0.8,
        4,
        "code",
        '{"task": "Describe the growth in work as input size increases."}',
        '{"explanation": "Efficiency describes how work grows with input size."}',
    ),
]


def upgrade():
    for task_id, title, description, concept_id, difficulty, cognitive_level, task_type, content, solution in TASKS:
        op.execute(
            f"""
            INSERT INTO tasks (
                id, title, description, concept_id, concept_type, difficulty,
                cognitive_level, task_type, content, solution, hints, metadata,
                created_at, updated_at
            )
            VALUES (
                '{task_id}', '{title}', '{description}', '{concept_id}', 'k12',
                {difficulty}, {cognitive_level}, '{task_type}',
                '{content}'::jsonb, '{solution}'::jsonb, '[]'::jsonb,
                '{{"seeded_for": "slice4_cohorts"}}'::jsonb, NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
            """
        )


def downgrade():
    ids = ", ".join(f"'{task[0]}'" for task in TASKS)
    op.execute(f"DELETE FROM tasks WHERE id IN ({ids})")
