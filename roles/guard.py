from .base import Role

class Guard(Role):
    def __init__(self):
        super().__init__("騎士")

    def can_act_at_night(self) -> bool:
        return True
