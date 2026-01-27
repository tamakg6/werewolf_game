class Role:
    def __init__(self, name: str):
        self.role_name = name

    def get_team_for_seer(self) -> str:
        """占い師に見える陣営（黒白判定）"""
        return "村人陣営"

    def get_species_for_medium(self) -> str:
        """霊媒師に見える結果"""
        return self.role_name

    def can_act_at_night(self) -> bool:
        """夜に行動があるか"""
        return False

    def __str__(self):
        return self.role_name
