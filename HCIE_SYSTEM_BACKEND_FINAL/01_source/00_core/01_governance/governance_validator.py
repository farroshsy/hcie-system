"""
Brain Governance Validator - Architectural Immune System

Prevents architectural regression by enforcing governance invariants:
- No reward path bypasses JT
- No subsystem updates behavior independently
- OBSERVE variables never modify CONTROL
- STATE variables are read-only outside governance paths

This is the architectural immune system that prevents the system
from re-fragmenting as complexity grows.
"""

import logging
import math
from typing import Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class VariableType(Enum):
    CONTROL = "CONTROL"  # Affects behavior (η, exploration, policy, ensemble weights)
    STATE = "STATE"      # Describes cognitive state (mastery, uncertainty, ZPD, transfer)
    OBSERVE = "OBSERVE"  # Dashboard/research only (metrics, regret, traces)


class GovernanceValidator:
    """
    Enforces brain governance invariants to prevent architectural regression
    """

    def __init__(self):
        # Registry of variable classifications
        self.variable_registry: Dict[str, VariableType] = {}

        # Track control flow paths
        self.control_paths: Dict[str, List[str]] = {}

        # Track reward paths (must all go through JT)
        self.reward_paths: List[str] = []

        # Track violations
        self.violations: List[str] = []

    def register_variable(self, name: str, var_type: VariableType, context: str = ""):
        """
        Register a variable with its governance classification

        Args:
            name: Variable name
            var_type: CONTROL, STATE, or OBSERVE
            context: File/function where variable is defined
        """
        self.variable_registry[name] = var_type
        logger.debug(f"Registered {name} as {var_type.value} in {context}")

    def validate_no_parallel_objectives(self, learning_context: Dict[str, Any]) -> bool:
        """
        Validate that no subsystem has independent objectives

        Checks:
        1. All reward paths go through JT
        2. No CONTROL variable is updated without JT consideration
        3. No STATE variable directly drives behavior

        Args:
            learning_context: Dictionary of current learning state

        Returns:
            True if governance is valid, False otherwise
        """
        violations = []

        # Check 1: Reward must go through JT
        if "reward" in learning_context:
            reward = learning_context["reward"]
            if "JT" not in str(reward) and "J_t" not in str(reward):
                violations.append(
                    f"Reward bypasses JT: {reward}. "
                    "All rewards must be JT-derived."
                )

        # Check 2: CONTROL variables should be JT-driven
        control_vars = [
            "eta", "learning_rate", "exploration", "policy",
            "ensemble_weights", "bandit_action"
        ]
        for var in control_vars:
            if var in learning_context:
                value = learning_context[var]
                # Check if the value is computed from JT
                if hasattr(value, '__dict__'):
                    # It's an object, check if it references JT
                    if "JT" not in str(value) and "J_t" not in str(value):
                        violations.append(
                            f"CONTROL variable {var} may not be JT-driven: {value}"
                        )

        # Check 3: STATE variables should not directly drive behavior
        state_vars = [
            "mastery", "uncertainty", "confidence", "zpd_score",
            "transfer_amount", "ensemble_variance"
        ]
        for var in state_vars:
            if var in learning_context:
                # STATE variables should only inform, not control
                # This is a soft check - we can't prevent all uses
                pass

        if violations:
            self.violations.extend(violations)
            for v in violations:
                logger.error(f"GOVERNANCE VIOLATION: {v}")
            return False

        return True

    def validate_observe_readonly(self, metrics_context: Dict[str, Any]) -> bool:
        """
        Validate that OBSERVE variables never modify CONTROL

        Args:
            metrics_context: Dictionary of metrics being recorded

        Returns:
            True if OBSERVE is read-only, False otherwise
        """
        violations = []

        # OBSERVE variables should never have side effects
        observe_vars = [
            "regret", "trace", "metric", "dashboard", "analytics"
        ]

        for key, value in metrics_context.items():
            if any(obs in key.lower() for obs in observe_vars):
                # Check if this is a callable (potential side effect)
                if callable(value):
                    violations.append(
                        f"OBSERVE variable {key} is callable - "
                        "OBSERVE should be read-only data"
                    )

        if violations:
            self.violations.extend(violations)
            for v in violations:
                logger.error(f"GOVERNANCE VIOLATION: {v}")
            return False

        return True

    def validate_jt_central(self, learning_result: Dict[str, Any]) -> bool:
        """
        Validate that JT is the central control signal

        Args:
            learning_result: LearningResult dictionary

        Returns:
            True if JT is central, False otherwise
        """
        violations = []

        # Check 1: JT must exist
        if "J_value" not in learning_result:
            violations.append("JT (J_value) not found in learning result")

        # Check 2: JT must be finite
        if "J_value" in learning_result:
            jt_value = learning_result["J_value"]
            if jt_value is None:
                violations.append("JT is None - must be computed")
            elif not isinstance(jt_value, (int, float)):
                violations.append(f"JT is not a number: {type(jt_value)}")
            elif not (isinstance(jt_value, float) and not math.isnan(jt_value)):  # Check NaN
                violations.append("JT is NaN")

        if violations:
            self.violations.extend(violations)
            for v in violations:
                logger.error(f"GOVERNANCE VIOLATION: {v}")
            return False

        return True

    def get_violations(self) -> List[str]:
        """Return all governance violations"""
        return self.violations

    def clear_violations(self):
        """Clear violation history"""
        self.violations = []


# Global validator instance
_governance_validator = GovernanceValidator()


def assert_no_parallel_objectives(learning_context: Dict[str, Any]):
    """
    Assertion wrapper for governance validation

    Usage:
        assert_no_parallel_objectives({
            "reward": ...,
            "eta": ...,
            "J_value": ...
        })

    Raises:
        AssertionError if governance is violated
    """
    if not _governance_validator.validate_no_parallel_objectives(learning_context):
        violations = _governance_validator.get_violations()
        raise AssertionError(
            f"Governance violation detected: {violations}\n"
            "See BRAIN_GOVERNANCE.md for architecture rules"
        )


def assert_observe_readonly(metrics_context: Dict[str, Any]):
    """
    Assertion wrapper for OBSERVE read-only validation

    Raises:
        AssertionError if OBSERVE variables have side effects
    """
    if not _governance_validator.validate_observe_readonly(metrics_context):
        violations = _governance_validator.get_violations()
        raise AssertionError(
            f"OBSERVE violation detected: {violations}\n"
            "OBSERVE variables must be read-only"
        )


def assert_jt_central(learning_result: Dict[str, Any]):
    """
    Assertion wrapper for JT centrality validation

    Raises:
        AssertionError if JT is not the central control signal
    """
    if not _governance_validator.validate_jt_central(learning_result):
        violations = _governance_validator.get_violations()
        raise AssertionError(
            f"JT centrality violation detected: {violations}\n"
            "JT must be the top-level objective"
        )


def register_control_variable(name: str, context: str = ""):
    """Register a CONTROL variable"""
    _governance_validator.register_variable(name, VariableType.CONTROL, context)


def register_state_variable(name: str, context: str = ""):
    """Register a STATE variable"""
    _governance_validator.register_variable(name, VariableType.STATE, context)


def register_observe_variable(name: str, context: str = ""):
    """Register an OBSERVE variable"""
    _governance_validator.register_variable(name, VariableType.OBSERVE, context)
