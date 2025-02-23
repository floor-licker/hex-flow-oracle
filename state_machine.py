from typing import Dict, Set, Callable
from dataclasses import dataclass
from enum import Enum, auto

class ContractState(Enum):
    INITIALIZING = auto()
    VALIDATING = auto()
    ACTIVE = auto()
    ERROR = auto()
    SHUTDOWN = auto()

@dataclass
class StateTransition:
    from_state: Set[ContractState]
    to_state: ContractState
    guards: list[Callable]
    actions: list[Callable]

class StateMachine:
    def __init__(self):
        self._state = ContractState.INITIALIZING
        self._transitions: Dict[ContractState, StateTransition] = {}

    async def transition(self, to_state: ContractState):
        transition = self._transitions.get(to_state)
        if not transition or self._state not in transition.from_state:
            raise ValueError(f"Invalid transition from {self._state} to {to_state}")

        for guard in transition.guards:
            if not await guard():
                raise ValueError(f"Guard failed for transition to {to_state}")

        for action in transition.actions:
            await action()

        self._state = to_state 