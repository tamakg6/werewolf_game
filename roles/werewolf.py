from .base import Role

class Werewolf(Role):
    def __init__(self):
        super().__init__("人狼")

    def get_team_for_seer(self) -> str:
        return "人狼陣営"

    def can_act_at_night(self) -> bool:
        return True
