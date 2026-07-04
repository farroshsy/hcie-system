"""Seed video / audio / diagram learning materials for the core K-12 concepts.

Revision ID: 033_seed_multimodal_materials
Revises: 032_add_tier2_5_v2_jt_signals
Create Date: 2026-06-03 00:00:00.000000

Completes migration 031's "follow-up migrations will add video, audio, and
interactive materials" TODO for the eight core K-12 concepts (EN).

HONESTY: these rows carry REAL text-form study content (a concept-specific body
plus, for video/audio, a narration transcript) and the correct modality +
archetype tags — but ``media_url`` is NULL and ``metadata.media_status`` =
``pending_production``: the actual video/audio/diagram files are NOT produced
here. This populates the content-library structure (so the modality dimension is
no longer reading-only) without fabricating media. It is content scaffolding, not
evidence, and materials are not yet selected by archetype (material.py serves them
structurally) — wiring archetype→material selection is separate future work.
"""

from alembic import op
import sqlalchemy as sa
import json


revision = "033_seed_multimodal_materials"
down_revision = "032_add_tier2_5_v2_jt_signals"
branch_labels = None
depends_on = None


CONCEPT_NAME = {
    "k2_algorithms": "Algorithms (K-2)",
    "k2_control": "Control Structures (K-2)",
    "k5_algorithms": "Algorithms (K-5)",
    "k5_control": "Control Structures (K-5)",
    "k8_algorithms": "Algorithms (K-8)",
    "k8_control": "Control Structures (K-8)",
    "k12_algorithms": "Algorithms (K-12)",
    "k12_control": "Control Structures (K-12)",
}

# One real, concept-specific blurb per concept (drives all three modalities).
BLURB = {
    "k2_algorithms": "an algorithm is an exact, ordered list of steps that solves the same problem the same way every time",
    "k2_control": "control structures decide the order steps run: do them in sequence, repeat them, or choose between them",
    "k5_algorithms": "the same problem can have several correct algorithms, so we trace each by hand and pick the simpler one",
    "k5_control": "loops repeat work without rewriting it, and conditionals (if / else) let a program react to different inputs",
    "k8_algorithms": "searching and sorting organise data so the next answer is faster to find, and method choice changes the speed",
    "k8_control": "nested loops and combined conditions express richer rules, but every extra layer adds cost worth watching",
    "k12_algorithms": "algorithmic efficiency (Big-O) measures how work grows with input size, and recursion solves a problem with smaller copies of itself",
    "k12_control": "advanced control flow — early exits, guards, and state machines — keeps complex logic readable and provably correct",
}

# (modality, est_min, difficulty, archetype_tags, title_fmt, body_fmt, transcript_fmt)
# {name} = concept display name, {blurb} = concept blurb (lower-cased clause).
MODALITIES = [
    (
        "video", 4, 0.4, ["vark_visual", "motiv_explorer"],
        "Watch: {name} — animated walkthrough",
        "A short animated walkthrough of {name}. The big idea: {blurb}. "
        "Watch how each step changes the result, pause before the next one, and predict it yourself.\n\n"
        "_(Video production pending — the narration transcript below carries the full explanation.)_",
        "{blurb_cap}. Let's trace it together, one step at a time, and see exactly why the order matters before we move on.",
    ),
    (
        "audio", 3, 0.35, ["vark_auditory", "motiv_social"],
        "Listen: {name} — narrated explainer",
        "A ~3-minute narrated explainer for {name} you can follow with your eyes closed. The big idea: {blurb}.\n\n"
        "_(Audio production pending — the narration transcript below is the full script.)_",
        "{blurb_cap}. Picture each step as I describe it — you don't need to see a screen to follow the idea; just hold the order in your head.",
    ),
    (
        "diagram", 2, 0.4, ["vark_visual", "vark_kinesthetic", "motiv_logical"],
        "Diagram: {name} — labelled flow",
        "A labelled flow diagram of {name}. The big idea: {blurb}. "
        "Each box is one step; arrows show the order, and a branch shows a choice.\n\n"
        "```\n[ start ] -> [ step ] -> < choice? > --yes--> [ do A ]\n                                  |\n                                  no--> [ do B ]\n```\n\n"
        "_(Rendered diagram pending — the text flow above is the labelled alternative.)_",
        None,
    ),
]


def upgrade():
    bind = op.get_bind()
    for concept_id, name in CONCEPT_NAME.items():
        blurb = BLURB[concept_id]
        blurb_cap = blurb[0].upper() + blurb[1:]
        for modality, est_min, difficulty, tags, title_fmt, body_fmt, trans_fmt in MODALITIES:
            mid = f"{concept_id}_{modality}_en_v1"
            exists = bind.execute(
                sa.text("SELECT 1 FROM learning_materials WHERE id = :id"), {"id": mid}
            ).first()
            if exists:
                continue
            body = body_fmt.format(name=name, blurb=blurb)
            transcript = trans_fmt.format(blurb_cap=blurb_cap) if trans_fmt else None
            metadata = json.dumps({
                "media_status": "pending_production",
                "text_form": True,
                "seeded_by": "033_seed_multimodal_materials",
            })
            bind.execute(
                sa.text(
                    """
                    INSERT INTO learning_materials (
                        id, concept_id, language, modality, archetype_tags,
                        title, body, media_url, transcript, estimated_minutes,
                        difficulty, prerequisites_assumed, metadata
                    ) VALUES (
                        :id, :concept_id, 'en', :modality, CAST(:tags AS jsonb),
                        :title, :body, NULL, :transcript, :est_min,
                        :difficulty, '[]'::jsonb, CAST(:metadata AS jsonb)
                    )
                    """
                ),
                {
                    "id": mid,
                    "concept_id": concept_id,
                    "modality": modality,
                    "tags": json.dumps(tags),
                    "title": title_fmt.format(name=name),
                    "body": body,
                    "transcript": transcript,
                    "est_min": est_min,
                    "difficulty": difficulty,
                    "metadata": metadata,
                },
            )


def downgrade():
    bind = op.get_bind()
    for concept_id in CONCEPT_NAME:
        for modality in ("video", "audio", "diagram"):
            bind.execute(
                sa.text("DELETE FROM learning_materials WHERE id = :id"),
                {"id": f"{concept_id}_{modality}_en_v1"},
            )
