"""API response translation utilities.

Relocated from the legacy ``app.api.utils`` namespace in the Phase 14e audit
slice. The two translators below are the canonical response shapers for the
``09_ux`` dashboard and learning endpoints; they perform domain-to-DTO
projection and version-bump compatibility for the legacy V2 contract.

Canonical IDEAL home: ``01_source/01_application/10_utils/api_responses/``
(per ``IDEAL_STRUCTURE.md`` line 370 — utilities live under ``10_utils/``).
"""

from .response_translator import ResponseTranslator
from .response_translator_v2 import ResponseTranslatorV2

__all__ = ["ResponseTranslator", "ResponseTranslatorV2"]
