from .base import Role

class Fanatic(Role):
    def __init__(self):
        super().__init__("狂信者")

    def get_divination_result(self) -> str:
        """占い結果は「村人陣営」（白）"""
        return "村人"

    def get_medium_result(self) -> str:
        """霊媒結果は「村人」"""
        return "村人"

    # 占われても死なない、襲撃されたら死ぬ（デフォルト動作）なので
    # on_divined, on_attacked は base.py のデフォルトのままでOK

    @property
    def night_action_type(self):
        """
        能動的なアクション（誰かをタップして選択）はしない。
        ただし、UI側で特別扱いして情報を表示するためにNoneのままにするか、
        必要に応じて識別子を持たせてもよいが、今回はNone（行動なし）とする。
        """
        return None
