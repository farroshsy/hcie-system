"""
NumPy-to-Python Type Converter with Type Preservation

This module provides utilities to convert NumPy types to native Python types
for JSON serialization while preserving type information.

Part of Stage A: Phase 1A - Prospective Transfer Governance Implementation
"""

import numpy as np
from typing import Any, Dict, Optional
import json


def convert_numpy_to_python(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types.
    
    Handles:
    - numpy scalar types (int64, float64, etc.) -> Python int/float
    - numpy arrays -> Python lists
    - numpy ndarrays -> nested Python lists
    - numpy bool_ -> Python bool
    - numpy string_ -> Python str
    - numpy datetime64 -> ISO format string
    - nested dicts/lists with NumPy types
    
    Args:
        obj: Any object potentially containing NumPy types
        
    Returns:
        Object with all NumPy types converted to native Python types
    """
    if isinstance(obj, np.ndarray):
        # Convert numpy array to list, recursively converting elements
        return obj.tolist()
    
    elif isinstance(obj, np.integer):
        return int(obj)
    
    elif isinstance(obj, np.floating):
        return float(obj)
    
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    elif isinstance(obj, np.str_):
        return str(obj)
    
    elif isinstance(obj, np.datetime64):
        return obj.astype(str)
    
    elif isinstance(obj, dict):
        # Recursively convert dict values
        return {key: convert_numpy_to_python(value) for key, value in obj.items()}
    
    elif isinstance(obj, (list, tuple)):
        # Recursively convert list/tuple elements
        return [convert_numpy_to_python(item) for item in obj]
    
    elif isinstance(obj, np.generic):
        # Catch-all for any other numpy scalar types
        return obj.item()
    
    else:
        # Return as-is for native Python types
        return obj


def convert_dict_numpy_to_python(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert all NumPy types in a dictionary to native Python types.
    
    Args:
        data: Dictionary potentially containing NumPy types
        
    Returns:
        Dictionary with all NumPy types converted
    """
    return convert_numpy_to_python(data)


def safe_json_serialize(obj: Any, indent: Optional[int] = None) -> str:
    """
    Safely serialize an object to JSON, handling NumPy types.
    
    Args:
        obj: Object to serialize
        indent: Optional indentation for pretty printing
        
    Returns:
        JSON string with all NumPy types converted
    """
    converted = convert_numpy_to_python(obj)
    return json.dumps(converted, indent=indent)


def assert_no_numpy_leakage(obj: Any, path: str = "root") -> None:
    """
    Hard failure guard to assert no NumPy types remain in object.
    
    Raises AssertionError if any NumPy types are found.
    
    Args:
        obj: Object to check
        path: Current path in nested structure (for error reporting)
        
    Raises:
        AssertionError: If any NumPy types are detected
    """
    if isinstance(obj, np.ndarray):
        raise AssertionError(f"NumPy ndarray detected at {path}")
    
    elif isinstance(obj, np.generic):
        raise AssertionError(f"NumPy scalar {type(obj)} detected at {path}")
    
    elif isinstance(obj, dict):
        for key, value in obj.items():
            assert_no_numpy_leakage(value, f"{path}[{key!r}]")
    
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            assert_no_numpy_leakage(item, f"{path}[{idx}]")


class NumpyJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles NumPy types.
    
    Usage:
        json.dumps(data, cls=NumpyJSONEncoder)
    """
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        elif isinstance(obj, np.integer):
            return int(obj)
        
        elif isinstance(obj, np.floating):
            return float(obj)
        
        elif isinstance(obj, np.bool_):
            return bool(obj)
        
        elif isinstance(obj, np.str_):
            return str(obj)
        
        elif isinstance(obj, np.datetime64):
            return obj.astype(str)
        
        elif isinstance(obj, np.generic):
            return obj.item()
        
        return super().default(obj)


def serialize_for_storage(data: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
    """
    Convert dictionary to storage-ready format with optional validation.
    
    This is the main entry point for serialization before database storage.
    
    Args:
        data: Dictionary containing potentially NumPy types
        validate: If True, runs assert_no_numpy_leakage after conversion
        
    Returns:
        Dictionary with all NumPy types converted to Python native types
        
    Raises:
        AssertionError: If validation fails and NumPy types remain
    """
    converted = convert_numpy_to_python(data)
    
    if validate:
        assert_no_numpy_leakage(converted)
    
    return converted
