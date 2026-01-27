import random
from roles import Villager, Werewolf, Seer, Guard, Medium, Madman, Fox

class Player:
    def __init__(self, idx, name, role):
        self.idx = idx
        self.name = name
        self.role = role
        self.is_alive = True

class WerewolfGame:
    def __init__(self):
        self.phase = "menu"
        self.num_players = 4
        self.players = []  # List[Player]
        self.day_count = 1
        self.current_turn_idx = 0  # 夜や役職確認の順番管理
        self.log = []
        self.last_night_info = ""
        self.executed_yesterday_idx = None  # 霊媒用
        self.game_winner = None
        
        # 夜のアクション一時保存用
        self.night_actions = self._init_night_actions()

    def _init_night_actions(self):
        return {
            "guard_target": None,
            "seer_target": None,
            "seer_killed": None, # 呪殺フラグ
            "wolf_votes": {},    # {player_idx: (target_idx, confidence_bool)}
        }

    def add_log(self, message):
        self.log.append(f"Day{self.day_count}: {message}")
        if len(self.log) > 20:
            self.log.pop(0)

    def setup_game(self, player_names, role_counts):
        """ゲームの初期化と役職配布"""
        total_roles = []
        role_map = {
            "人狼": (Werewolf, role_counts["wolf"]),
            "占い師": (Seer, role_counts["seer"]),
            "騎士": (Guard, role_counts["guard"]),
            "霊媒師": (Medium, role_counts["medium"]),
            "狂人": (Madman, role_counts["madman"]),
            "妖狐": (Fox, role_counts["fox"]),
        }
        
        # 指定役職を追加
        current_count = 0
        for r_name, (r_class, count) in role_map.items():
            total_roles.extend([r_class() for _ in range(count)])
            current_count += count
        
        # 残りを村人で埋める
        num_villager = len(player_names) - current_count
        total_roles.extend([Villager() for _ in range(num_villager)])
        
        random.shuffle(total_roles)
        
        self.players = []
        for i, name in enumerate(player_names):
            self.players.append(Player(i, name, total_roles[i]))

        self.phase = "show_roles"
        self.day_count = 1
        self.log = []
        self.executed_yesterday_idx = None
        self.add_log("ゲーム開始")

    # --- 情報取得系ヘルパー ---
    def get_player(self, idx):
        return self.players[idx]

    def get_alive_players(self):
        return [p for p in self.players if p.is_alive]

    def get_alive_wolves(self):
        return [p for p in self.players if p.is_alive and isinstance(p.role, Werewolf)]

    # --- アクション処理 ---
    def register_wolf_vote(self, wolf_idx, target_idx, confidence):
        self.night_actions["wolf_votes"][wolf_idx] = (target_idx, confidence)

    def register_seer_action(self, seer_idx, target_idx):
        target = self.players[target_idx]
        result_faction = target.role.get_team_for_seer()
        self.night_actions["seer_target"] = target_idx
        
        # 呪殺判定
        if isinstance(target.role, Fox):
            self.night_actions["seer_killed"] = target_idx
        else:
            self.night_actions["seer_killed"] = None
            
        return f"{target.name}: {result_faction}"

    def register_guard_action(self, guard_idx, target_idx):
        self.night_actions["guard_target"] = target_idx

    def get_medium_result_text(self):
        if self.executed_yesterday_idx is not None:
            dead_p = self.players[self.executed_yesterday_idx]
            result = dead_p.role.get_species_for_medium()
            return f"前日処刑者: {dead_p.name}（{result}）"
        return None

    # --- 夜の解決 ---
    def resolve_night(self):
        wolves = self.get_alive_wolves()
        night_deaths = []
        
        # 1. 呪殺 (最優先で死亡判定)
        seer_killed_idx = self.night_actions.get("seer_killed")
        if seer_killed_idx is not None and self.players[seer_killed_idx].is_alive:
            self.players[seer_killed_idx].is_alive = False
            night_deaths.append(seer_killed_idx)

        # 2. 襲撃先決定
        attack_target_idx = None
        if wolves and self.night_actions["wolf_votes"]:
            # 自信ありの票を抽出
            confident_votes = [t for t, c in self.night_actions["wolf_votes"].values() if c]
            if confident_votes:
                attack_target_idx = random.choice(confident_votes)
            else:
                # 自信なしのみなら全票から抽選
                all_votes = [t for t, _ in self.night_actions["wolf_votes"].values()]
                attack_target_idx = random.choice(all_votes)

        # 3. 襲撃実行処理
        guard_target_idx = self.night_actions.get("guard_target")
        
        if attack_target_idx is not None and self.players[attack_target_idx].is_alive:
            target_p = self.players[attack_target_idx]
            
            # 妖狐は襲撃無効 (ただし呪殺ですでに死んでる場合は無視)
            if isinstance(target_p.role, Fox) and attack_target_idx not in night_deaths:
                pass # 死亡しない
            
            # 護衛成功なら死亡しない
            elif attack_target_idx == guard_target_idx:
                pass 
            
            else:
                # 死亡
                target_p.is_alive = False
                night_deaths.append(attack_target_idx)

        # 4. 結果生成
        if not night_deaths:
            msg = "昨夜の犠牲者はいませんでした"
        else:
            names = "、".join([self.players[i].name for i in night_deaths])
            msg = f"{names}が死亡しました"

        self.last_night_info = msg
        self.add_log(msg)
        self.add_log(f"{self.day_count}日目の朝が訪れました")
        
        # ステート更新
        self.day_count += 1
        self.phase = "day"
        self.current_turn_idx = 0
        self.night_actions = self._init_night_actions()

    # --- 処刑処理 ---
    def execute_player(self, target_idx):
        if target_idx is not None:
            self.players[target_idx].is_alive = False
            self.executed_yesterday_idx = target_idx
            self.add_log(f"{self.players[target_idx].name}が処刑されました")
        else:
            self.add_log("投票の結果、処刑は行われませんでした")

    # --- 勝敗判定 ---
    def check_winner(self):
        alive = self.get_alive_players()
        alive_wolves = len([p for p in alive if isinstance(p.role, Werewolf)])
        alive_foxes = len([p for p in alive if isinstance(p.role, Fox)])
        alive_humans = len(alive) - alive_wolves # 妖狐もカウント上は人間側(数合わせ)だが、勝利条件は特殊

        # 人狼全滅
        if alive_wolves == 0:
            if alive_foxes > 0:
                self.game_winner = "妖狐"
                self.add_log("妖狐の勝利")
            else:
                self.game_winner = "村人陣営"
                self.add_log("村人陣営の勝利")
            return True
        
        # 人狼数が人間数以上 (P - W <= W つまり P <= 2W)
        if len(alive) <= 2 * alive_wolves:
            if alive_foxes > 0:
                self.game_winner = "妖狐"
                self.add_log("妖狐の勝利")
            else:
                self.game_winner = "人狼陣営"
                self.add_log("人狼陣営の勝利")
            return True
            
        return False
