"""Seed additional task variants per K-12 concept for baseline divergence.

Revision ID: 017_seed_cohort_task_diversity
Revises: 016_learning_state_text_user_ids
Create Date: 2026-05-22 00:00:00.000000

Slice 4 baseline comparison requires that the ``bandit`` / ``random`` /
``static`` selectors can diverge on the same concept. The original catalog
(015) seeded mostly one task per concept which collapsed all selectors to
the same row. This migration adds easy / mid / hard variants per concept
so the selectors are semantically distinguishable in experiment trajectories.
"""

from alembic import op


revision = "017_seed_cohort_task_diversity"
down_revision = "016_learning_state_text_user_ids"


# Each row: (id, title, description, concept_id, difficulty,
#            cognitive_level, task_type, content_json, solution_json)
TASKS = [
    # k2_algorithms — easy / mid / hard
    (
        "k2_algorithms_text_easy_v1",
        "Spot a Step-by-Step Plan",
        "Identify the simplest sequence of steps",
        "k2_algorithms",
        0.15,
        1,
        "text",
        '{"question": "Which list shows the simplest correct order?"}',
        '{"explanation": "Algorithms break problems into ordered steps."}',
    ),
    (
        "k2_algorithms_mid_v1",
        "Order Three Steps",
        "Order three steps to complete a small task",
        "k2_algorithms",
        0.35,
        2,
        "text",
        '{"question": "Place these three steps in the right order."}',
        '{"explanation": "Step ordering is the foundation of algorithmic thinking."}',
    ),
    # k5_algorithms — supply easy / mid / hard
    (
        "k5_algorithms_text_easy_v1",
        "Pick a Reusable Step",
        "Identify a step that can be reused inside a routine",
        "k5_algorithms",
        0.30,
        2,
        "text",
        '{"question": "Which step appears more than once and can be reused?"}',
        '{"explanation": "Reuse is the early seed of abstraction."}',
    ),
    (
        "k5_algorithms_text_hard_v1",
        "Sequence Without Repeats",
        "Build a sequence that avoids unnecessary repetition",
        "k5_algorithms",
        0.55,
        3,
        "text",
        '{"question": "Reorder the steps to avoid doing the same thing twice."}',
        '{"explanation": "Eliminating repeats reduces algorithm work."}',
    ),
    # k8_algorithms — supply easy / hard alongside existing mid (0.6)
    (
        "k8_algorithms_text_easy_v1",
        "Name an Algorithm Goal",
        "Identify the goal of a small algorithm",
        "k8_algorithms",
        0.45,
        2,
        "text",
        '{"question": "What is the goal of this short algorithm?"}',
        '{"explanation": "An algorithm always has an explicit goal."}',
    ),
    (
        "k8_algorithms_code_hard_v1",
        "Count Algorithm Steps",
        "Count the work performed by a short loop",
        "k8_algorithms",
        0.70,
        3,
        "code",
        '{"task": "How many additions are performed by this loop?"}',
        '{"explanation": "Work counts let us compare algorithms quantitatively."}',
    ),
    # k12_algorithms — supply easy / mid alongside existing hard (0.8)
    (
        "k12_algorithms_text_mid_v1",
        "Spot a Worst Case",
        "Identify which input is the worst case for a short algorithm",
        "k12_algorithms",
        0.60,
        3,
        "text",
        '{"question": "Which input makes this algorithm work hardest?"}',
        '{"explanation": "Worst-case reasoning grounds Big-O intuition."}',
    ),
    (
        "k12_algorithms_text_easy_v1",
        "Compare Two Algorithm Outputs",
        "Compare outputs of two short algorithms on the same input",
        "k12_algorithms",
        0.50,
        3,
        "text",
        '{"question": "Which algorithm returns the larger value on this input?"}',
        '{"explanation": "Comparing outputs is the first lens before comparing efficiency."}',
    ),
    # k2_control — supply mid and hard alongside existing easy (0.25)
    (
        "k2_control_text_mid_v1",
        "Predict the Next Repeat",
        "Predict the next step in a repeated pattern",
        "k2_control",
        0.40,
        2,
        "text",
        '{"question": "What step comes next in this repeating pattern?"}',
        '{"explanation": "Predicting the next step exercises control-flow intuition."}',
    ),
    # k5_control — supply easy and hard alongside existing mid (0.45)
    (
        "k5_control_text_easy_v1",
        "Recognise the Loop Body",
        "Identify which lines belong to the loop body",
        "k5_control",
        0.30,
        2,
        "text",
        '{"question": "Which lines run on every loop iteration?"}',
        '{"explanation": "Knowing the loop body is the prerequisite for tracing."}',
    ),
    # k8_control — supply easy alongside existing mid (0.65)
    (
        "k8_control_text_easy_v1",
        "Pick a Stop Condition",
        "Pick a simple condition that stops the loop after the first true value",
        "k8_control",
        0.50,
        2,
        "text",
        '{"question": "Which condition stops as soon as the value is true?"}',
        '{"explanation": "Loop control hinges on the stop condition."}',
    ),
    # k12_control — supply mid alongside existing hard (0.8)
    (
        "k12_control_text_mid_v1",
        "Map Nested Calls",
        "Map the call chain inside a nested control block",
        "k12_control",
        0.65,
        3,
        "text",
        '{"question": "Which call runs second in this nested block?"}',
        '{"explanation": "Mapping nested calls is the precursor to reasoning about complexity."}',
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
                '{{"seeded_for": "slice4_baseline_divergence"}}'::jsonb,
                NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
            """
        )


def downgrade():
    ids = ", ".join(f"'{task[0]}'" for task in TASKS)
    op.execute(f"DELETE FROM tasks WHERE id IN ({ids})")
