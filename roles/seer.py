from .base import Role

class Seer(Role):
    def __init__(self):
        super().__init__("占い師")

    def can_act_at_night(self) -> bool:
        return True
    
