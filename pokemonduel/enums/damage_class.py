from enum import IntEnum


class DamageClass(IntEnum):
    """Helper enum for damage classes to make them more readable."""
    STATUS = 1
    PHYSICAL = 2
    SPECIAL = 3