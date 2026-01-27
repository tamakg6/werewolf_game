from .base import Role

class Madman(Role):
    def __init__(self):
        super().__init__("狂人")
    
    # 狂人は夜行動なし、占いは「村人陣営（白）」判定
