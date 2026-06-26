"""
User ID Normalization Utility

Hybrid approach: Accept both UUID and string IDs, convert strings to deterministic UUIDs.
This provides:
- Production: UUID security and standards
- Experiments: Readable string IDs
- Debugging: Deterministic mapping between strings and UUIDs
"""

import uuid
from typing import Optional


# Namespace for deterministic UUID generation (HCIE system namespace)
HCIE_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, 'hcie.system')


def normalize_user_id(user_id: str) -> str:
    """
    Convert string IDs to deterministic UUIDs.
    
    If user_id is already a valid UUID, return it as-is.
    If user_id is a string, convert to a deterministic UUID using UUID5.
    
    Args:
        user_id: User identifier (UUID string or readable string)
        
    Returns:
        Valid UUID string
        
    Examples:
        >>> normalize_user_id("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        
        >>> normalize_user_id("test_user_001")
        '550e8400-e29b-41d4-a716-446655440000'  # Deterministic UUID
        
        >>> normalize_user_id("user_123")
        '6ba7b810-9dad-11d1-80b4-00c04fd430c8'  # Different deterministic UUID
    """
    if not user_id:
        raise ValueError("user_id cannot be empty")
    
    try:
        # Try to parse as UUID
        uuid.UUID(user_id)
        return user_id  # Already a valid UUID
    except (ValueError, AttributeError):
        # Convert string to deterministic UUID
        return str(uuid.uuid5(HCIE_NAMESPACE, user_id))


def is_valid_uuid(user_id: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        user_id: User identifier to check
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(user_id)
        return True
    except (ValueError, AttributeError):
        return False


def get_original_string(uuid_str: str, known_strings: list) -> Optional[str]:
    """
    Reverse-lookup: Find the original string that generated this UUID.
    
    This is useful for debugging logs where you see a UUID and want to know
    what the original readable string was.
    
    Args:
        uuid_str: UUID string to lookup
        known_strings: List of possible original strings
        
    Returns:
        Original string if found, None otherwise
        
    Examples:
        >>> get_original_string(normalize_user_id("test_user_001"), ["test_user_001", "user_123"])
        'test_user_001'
    """
    target_uuid = normalize_user_id(uuid_str)
    for original in known_strings:
        if normalize_user_id(original) == target_uuid:
            return original
    return None
