"""
Static Topology Validation - Phase E1.3

Architectural linting to enforce ownership boundaries:
- Frontend modules forbidden from importing UnifiedBrain
- Projection layer forbidden from cognition mutation repos
- Analytics forbidden from cognition persistence
- WebSocket layer forbidden from cognition services

Prevents topology erosion over time.
"""

import ast
import sys
from typing import List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TopologyViolation:
    """Represents a topology violation"""
    def __init__(self, file_path: str, line: int, violation_type: str, details: str):
        self.file_path = file_path
        self.line = line
        self.violation_type = violation_type
        self.details = details
    
    def __str__(self):
        return f"❌ {self.file_path}:{self.line} - {self.violation_type}: {self.details}"


class TopologyLinter:
    """
    Static analysis tool to enforce architectural ownership boundaries.
    
    Validates import patterns across the codebase to prevent topology erosion.
    """
    
    # Forbidden import patterns by module type
    FORBIDDEN_IMPORTS = {
        # Frontend modules should not import UnifiedBrain directly
        'frontend': {
            'forbidden': ['core.learning.unified_brain', 'core.learning.brain'],
            'allowed': ['app.repositories.learning_state_repository', 'core.session.projection_service'],
            'reason': 'Frontend must read from projection store, not UnifiedBrain directly'
        },
        # Projection layer should not mutate cognition directly
        'projection': {
            'forbidden': ['app.repositories.learning_state_repository'],
            'allowed': ['core.session.projection_service'],
            'reason': 'Projection layer must be read-only derived topology'
        },
        # Analytics should not write to cognition persistence
        'analytics': {
            'forbidden': ['app.repositories.learning_state_repository.save_state', 'app.repositories.learning_state_repository.batch_save_states'],
            'allowed': ['app.repositories.learning_state_repository.get_state', 'app.repositories.learning_state_repository.get_user_concepts'],
            'reason': 'Analytics must be read-only, not mutate canonical cognition'
        },
        # WebSocket layer should not access cognition services
        'websocket': {
            'forbidden': ['core.learning.unified_brain', 'core.learning.brain'],
            'allowed': ['app.repositories.learning_state_repository'],
            'reason': 'WebSocket must read from projection store, not cognition services'
        }
    }
    
    # Module path patterns for classification
    MODULE_PATTERNS = {
        'frontend': [
            'app/api/ux',
            'app/api/websocket',
            'app/api/frontend'
        ],
        'projection': [
            'core/session/projection',
            'app/workers/projection_consumer'
        ],
        'analytics': [
            'app/workers/analytics',
            'app/workers/metrics'
        ],
        'websocket': [
            'app/api/websocket'
        ]
    }
    
    def __init__(self, root_dir: str):
        """
        Initialize topology linter.
        
        Args:
            root_dir: Root directory of the codebase
        """
        self.root_dir = Path(root_dir)
        self.violations: List[TopologyViolation] = []
    
    def classify_module(self, file_path: Path) -> str:
        """
        Classify a module based on its path.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Module type (frontend, projection, analytics, websocket, or 'other')
        """
        path_str = str(file_path)
        
        for module_type, patterns in self.MODULE_PATTERNS.items():
            for pattern in patterns:
                if pattern in path_str:
                    return module_type
        
        return 'other'
    
    def check_imports(self, file_path: Path) -> List[TopologyViolation]:
        """
        Check imports in a Python file for topology violations.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of topology violations
        """
        violations = []
        module_type = self.classify_module(file_path)
        
        if module_type == 'other':
            return violations
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._check_import_alias(file_path, alias.name, node.lineno, module_type, violations)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._check_import_alias(file_path, node.module, node.lineno, module_type, violations)
                        
                        # Also check individual names imported
                        for alias in node.names:
                            full_import = f"{node.module}.{alias.name}"
                            self._check_import_alias(file_path, full_import, node.lineno, module_type, violations)
        
        except Exception as e:
            logger.warning(f"⚠️  Failed to parse {file_path}: {e}")
        
        return violations
    
    def _check_import_alias(self, file_path: Path, import_name: str, line: int, module_type: str, violations: List[TopologyViolation]):
        """
        Check if an import violates topology rules.
        
        Args:
            file_path: Path to the file
            import_name: Import statement
            line: Line number
            module_type: Type of module being checked
            violations: List to add violations to
        """
        if module_type not in self.FORBIDDEN_IMPORTS:
            return
        
        rules = self.FORBIDDEN_IMPORTS[module_type]
        
        for forbidden in rules['forbidden']:
            if import_name.startswith(forbidden):
                violations.append(TopologyViolation(
                    file_path=str(file_path),
                    line=line,
                    violation_type=f"{module_type.upper()}_FORBIDDEN_IMPORT",
                    details=f"Importing '{import_name}' violates ownership boundary. {rules['reason']}"
                ))
    
    def lint_directory(self, directory: str = None) -> List[TopologyViolation]:
        """
        Lint all Python files in a directory.
        
        Args:
            directory: Directory to lint (defaults to root_dir)
            
        Returns:
            List of all topology violations found
        """
        if directory is None:
            directory = self.root_dir
        else:
            directory = Path(directory)
        
        violations = []
        
        for py_file in directory.rglob('*.py'):
            file_violations = self.check_imports(py_file)
            violations.extend(file_violations)
        
        self.violations = violations
        return violations
    
    def report_violations(self) -> str:
        """
        Generate a report of all violations.
        
        Returns:
            Formatted violation report
        """
        if not self.violations:
            return "✅ No topology violations found"
        
        report = []
        report.append(f"❌ Found {len(self.violations)} topology violations:\n")
        
        for violation in self.violations:
            report.append(str(violation))
        
        return "\n".join(report)


def run_topology_lint(root_dir: str = None) -> Tuple[int, List[TopologyViolation]]:
    """
    Run topology linter on the codebase.
    
    Args:
        root_dir: Root directory of the codebase (defaults to current directory)
        
    Returns:
        Tuple of (exit_code, violations_list)
    """
    if root_dir is None:
        root_dir = Path(__file__).parent.parent.parent
    
    linter = TopologyLinter(root_dir)
    violations = linter.lint_directory()
    
    print("=" * 80)
    print("TOPOLOGY LINT RESULTS")
    print("=" * 80)
    print(linter.report_violations())
    print("=" * 80)
    
    exit_code = 0 if not violations else 1
    return exit_code, violations


if __name__ == "__main__":
    exit_code, _ = run_topology_lint()
    sys.exit(exit_code)
