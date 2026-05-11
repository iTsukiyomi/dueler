from .move_init import MoveInit
from .move_use import MoveUse
from .move_attack import MoveAttack
from .move_power import MovePower
from .move_type import MoveType
from .move_checks import MoveChecks, MoveHelpers

class Move(
    MoveInit,
    MoveUse,
    MoveAttack,
    MovePower,
    MoveType,
    MoveChecks,
    MoveHelpers,
):
    pass