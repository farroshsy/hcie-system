-- material_engagement — additive observability table for the Modality
-- Effectiveness Lab. Captures WHICH study-material modality a learner opened
-- for a concept, so a reviewer can study "reading vs interactive vs audio →
-- learning speed / mastery" per concept and per grade-band.
--
-- ADDITIVE ONLY. This table is never read by the MAB / bandit and never feeds
-- the sealed evaluation. It mirrors the existing "material ordering is
-- observational UX only — never feeds the MAB" invariant (see material.py).
--
-- Apply on the Mac stack:
--   docker exec -i hcie-final-postgres psql -U hcie_user -d hcie < material_engagement_table.sql

CREATE TABLE IF NOT EXISTS material_engagement (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  concept_id TEXT NOT NULL,
  modality TEXT NOT NULL,
  grade_band TEXT,
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ms_spent INTEGER
);

CREATE INDEX IF NOT EXISTS idx_meng_user ON material_engagement(user_id);
CREATE INDEX IF NOT EXISTS idx_meng_concept_modality ON material_engagement(concept_id, modality);
