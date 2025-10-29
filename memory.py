from typing import Dict, List

class SessionMemory:
    def __init__(self):
        self.state: Dict[str, str] = {}
        self.turns: List[str] = []

    def remember(self, key: str, value: str):
        self.state[key] = value

    def fact(self, key: str, default: str = "") -> str:
        return self.state.get(key, default)

    def add_turn(self, role: str, content: str):
        self.turns.append(f"{role.upper()}: {content}")

    def resumen(self, max_chars: int = 600) -> str:
        txt = " | ".join(self.turns)
        return txt[-max_chars:] if len(txt) > max_chars else txt
