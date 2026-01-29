import streamlit as st
from game import WerewolfGame
from roles import Werewolf, Seer, Guard, Medium, Madman, Fox, Fanatic
from update_history import VERSION_LOG

# ページ設定
st.set_page_config(page_title="人狼ゲーム Online", layout="centered")

# ゲームインスタンスの初期化
if "game" not in st.session_state:
    st.session_state.game = WerewolfGame()

game = st.session_state.game

# --- サイドバー (常に表示) ---
with st.sidebar:
    st.header("📖 ゲームログ")
    if game.log:
        for log in game.log[-15:]:  # 直近15件を表示
            st.write(log)
    else:
        st.write("ログはありません")

# --- メイン画面 ---

# 1. セットアップフェーズ
if game.phase == "setup":
    st.title("🐺 人狼ゲーム設定")

    # 更新履歴の表示フラグ管理
    if "show_update_log" not in st.session_state:
        st.session_state.show_update_log = False

    # プレイヤー名の入力
    player_names_input = st.text_area("プレイヤー名を改行区切りで入力してください", "プレイヤー1\nプレイヤー2\nプレイヤー3\nプレイヤー4\nプレイヤー5")
    player_names = [name.strip() for name in player_names_input.split("\n") if name.strip()]
    num_players = len(player_names)
    st.caption(f"現在のプレイヤー数: {num_players}名")

    st.subheader("役職構成")
    # 7カラムで役職設定を表示
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1: num_wolf = st.number_input("人狼", 1, num_players // 2, 1)
    with col2: num_seer = st.number_input("占い師", 0, 1, 1)
    with col3: num_guard = st.number_input("騎士", 0, 1, 1)
    with col4: num_medium = st.number_input("霊媒師", 0, 1, 0)
    with col5: num_madman = st.number_input("狂人", 0, 1, 0)
    with col6: num_fox = st.number_input("妖狐", 0, 1, 0)
    with col7: num_fanatic = st.number_input("狂信者", 0, 1, 0)

    # 村人数を自動計算
    num_villager = num_players - (num_wolf + num_seer + num_guard + num_medium + num_madman + num_fox + num_fanatic)
    
    if num_villager < 0:
        st.error(f"役職の合計がプレイヤー数を超えています（不足: {-num_villager}名）")
    else:
        st.metric("村人(自動計算)", num_villager)
        
        # 操作ボタン
        c_start, c_log = st.columns([2, 1])
        with c_start:
            if st.button("ゲーム開始", use_container_width=True, type="primary"):
                role_counts = {
                    "wolf": num_wolf, "seer": num_seer, "guard": num_guard,
                    "medium": num_medium, "madman": num_madman, "fox": num_fox,
                    "fanatic": num_fanatic
                }
                game.setup_game(player_names, role_counts)
                st.rerun()
        
        with c_log:
            log_label = "履歴を閉じる" if st.session_state.show_update_log else "更新履歴を見る"
            if st.button(log_label, use_container_width=True):
                st.session_state.show_update_log = not st.session_state.show_update_log
                st.rerun()

    # 更新履歴の表示
    if st.session_state.show_update_log:
        st.divider()
        st.info("### 🛠 アップデート情報")
        for version, changes in VERSION_LOG.items():
            with st.expander(f"バージョン {version}", expanded=(version == list(VERSION_LOG.keys())[0])):
                for change in changes:
                    st.write(f"- {change}")

# 2. 夜の行動フェーズ
elif game.phase == "night":
    st.title(f"🌙 第 {game.day} 晩：夜の行動")
    
    # 全員が行動し終えたかチェック
    if game.current_turn_idx >= len(game.players):
        if st.button("夜が明ける...", use_container_width=True, type="primary"):
            game.resolve_night()
            st.rerun()
    else:
        p_now = game.players[game.current_turn_idx]
        
        # 死亡しているプレイヤーはスキップ
        if not p_now.is_alive:
            game.current_turn_idx += 1
            st.rerun()
        
        st.subheader(f"プレイヤー: {p_now.name}")
        if st.checkbox(f"本人確認：私は {p_now.name} です", key=f"check_{p_now.idx}"):
            role = p_now.role
            st.success(f"あなたの役職は **{role.role_name}** です")
            
            # --- 役職ごとの個別UI ---
            
            # 人狼
            if isinstance(role, Werewolf):
                alive_others = [p for p in game.players if p.is_alive and p.idx != p_now.idx]
                target = st.selectbox("襲撃先を選んでください", alive_others, format_func=lambda x: x.name)
                if st.button("襲撃を決定"):
                    game.night_actions["wolf_votes"][p_now.idx] = target.idx
                    game.current_turn_idx += 1
                    st.rerun()
            
            # 狂信者 (新役職)
            elif isinstance(role, Fanatic):
                wolves = game.get_alive_wolves()
                st.info("🐺 **仲間（人狼）のリスト:**")
                for w in wolves:
                    st.write(f"- {w.name}")
                if st.button("確認しました"):
                    game.current_turn_idx += 1
                    st.rerun()

            # 占い師
            elif isinstance(role, Seer):
                alive_others = [p for p in game.players if p.is_alive and p.idx != p_now.idx]
                target = st.selectbox("占う相手を選んでください", alive_others, format_func=lambda x: x.name)
                if st.button("占う"):
                    result = target.role.get_divination_result()
                    st.session_state[f"seer_res_{game.day}"] = f"{target.name} は **{result}** です。"
                    game.night_actions["seer_target"] = target.idx
                    # 副作用(呪殺)はgameクラス側で処理される
                
                if f"seer_res_{game.day}" in st.session_state:
                    st.warning(st.session_state[f"seer_res_{game.day}"])
                    if st.button("次へ"):
                        game.current_turn_idx += 1
                        st.rerun()

            # 騎士
            elif isinstance(role, Guard):
                alive_others = [p for p in game.players if p.is_alive and p.idx != p_now.idx]
                target = st.selectbox("守る相手を選んでください", alive_others, format_func=lambda x: x.name)
                if st.button("守る"):
                    game.night_actions["guard_target"] = target.idx
                    game.current_turn_idx += 1
                    st.rerun()

            # その他（能力なし）
            else:
                st.write("夜の行動はありません。")
                if st.button("次へ"):
                    game.current_turn_idx += 1
                    st.rerun()

# 3. 昼の議論・処刑フェーズ
elif game.phase == "day":
    st.title(f"☀️ 第 {game.day} 日：昼の議論")
    
    # 昨晩の結果表示
    if game.log:
        st.error(game.log[-1]) # 最新の結果を表示
    
    alive_players = [p for p in game.players if p.is_alive]
    
    # 霊媒師がいる場合の結果表示
    if any(isinstance(p.role, Medium) for p in alive_players) and game.last_executed_idx is not None:
        last_p = game.players[game.last_executed_idx]
        st.info(f"🔮 霊媒結果: 昨日処刑された {last_p.name} は **{last_p.role.get_medium_result()}** でした。")

    st.subheader("処刑投票")
    target = st.selectbox("処刑する人を選んでください", alive_players, format_func=lambda x: x.name)
    if st.button("処刑を確定"):
        game.resolve_day(target.idx)
        st.rerun()

# 4. ゲーム終了
elif game.phase == "game_over":
    st.title("🏁 ゲーム終了")
    st.header(game.winner)
    
    # 最終結果の表示
    st.subheader("役職一覧")
    for p in game.players:
        status = "生存" if p.is_alive else "死亡"
        st.write(f"{p.name}: {p.role.role_name} ({status})")
    
    if st.button("新しいゲームを始める", use_container_width=True):
        st.session_state.game = WerewolfGame()
        st.rerun()
