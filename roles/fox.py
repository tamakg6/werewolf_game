from .base import Role

class Fox(Role):
    def __init__(self):
        super().__init__("妖狐")

    def get_species_for_medium(self) -> str:
        return "妖狐"
    
    # 妖狐は夜行動なし、占いは「村人陣営（白）」だが呪殺されるロジックはGame側で処理
