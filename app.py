import streamlit as st
from game import WerewolfGame
from roles import Villager, Werewolf, Seer, Guard, Medium, Madman, Fox, Fanatic

# --- UI Theme Helpers ---
def get_theme():
    # phaseはgameオブジェクト内にあるが、session_state経由で取得
    current_phase = st.session_state.game.phase if "game" in st.session_state else "menu"
    if current_phase == "night":
        return {"bg": "#1e1e2e", "fg": "#cdd6f4"}
    return {"bg": "#eff1f5", "fg": "#4c4f69"}

theme = get_theme()
st.markdown(
    f"""
    <style>
    .main {{background-color: {theme['bg']}; color: {theme['fg']};}}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Initialization ---
if "game" not in st.session_state:
    st.session_state.game = WerewolfGame()

game = st.session_state.game  # ショートカット

st.title("人狼ゲーム (OOP版)")

# --- Sidebar ---
with st.sidebar:
    st.header("ゲームログ")
    if game.log:
        for log in game.log[-10:]:
            st.write(log)
    
    if st.button("状態リセット"):
        st.session_state.game = WerewolfGame()
        st.rerun()

# --- Phases ---

if game.phase == "menu":
    st.header("ゲームメニュー")
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("新規ゲーム開始", use_container_width=True):
            game.phase = "setup"
            st.rerun()
    with col2:
        if st.button("リセット", use_container_width=True):
            st.session_state.game = WerewolfGame()
            st.rerun()

elif game.phase == "setup":
    st.header("ゲーム設定")
    num_players = st.slider("プレイヤー数", 4, 11, 6)

    st.subheader("プレイヤー名")
    player_names = []
    for i in range(num_players):
        # 名前入力の保持用に一時的なkeyを使う
        default_name = f"P{i+1}"
        name = st.text_input(f"P{i+1}", value=default_name, key=f"name_{i}")
        player_names.append(name)

    st.subheader("役職構成")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1: num_wolf = st.number_input("人狼", 1, num_players // 2, 2)
    with col2: num_seer = st.number_input("占い師", 0, 1, 1)
    with col3: num_guard = st.number_input("騎士", 0, 1, 1)
    with col4: num_medium = st.number_input("霊媒師", 0, 1, 0)
    with col5: num_madman = st.number_input("狂人", 0, 1, 0)
    with col6: num_fox = st.number_input("妖狐", 0, 1, 0)
    with col7: num_fanatic = st.number_input("狂信者", 0, 1, 0)

    num_villager = num_players - (num_wolf + num_seer + num_guard + num_medium + num_madman + num_fox)
    st.metric("村人", num_villager)

    if st.button("ゲーム開始", use_container_width=True):
        role_counts = {
            "wolf": num_wolf, "seer": num_seer, "guard": num_guard,
            "medium": num_medium, "madman": num_madman, "fox": num_fox,
            "fanatic": num_fanatic
        }
        game.setup_game(player_names, role_counts)
        st.rerun()

elif game.phase == "show_roles":
    st.header("役職確認")
    p_idx = game.current_turn_idx
    if p_idx < len(game.players):
        player = game.get_player(p_idx)
        st.info(f"プレイヤー {p_idx+1}: {player.name}")

        if st.checkbox(f"私は {player.name} です", key=f"role_confirm_{p_idx}"):
            st.success(f"あなたの役職: **{player.role.role_name}**")
            if st.button("確認完了（次へ）", use_container_width=True):
                game.current_turn_idx += 1
                st.rerun()
    else:
        game.add_log("全員役職確認完了。1日目の昼へ")
        game.phase = "day"
        game.current_turn_idx = 0
        st.rerun()

elif game.phase == "night":
    st.header(f"{game.day_count}日目の夜")
    alive_players = game.get_alive_players()
    
    # 全員の行動が終わったら夜明け処理へ
    if game.current_turn_idx >= len(alive_players):
        game.resolve_night()
        st.rerun()
    
    # プレイヤーごとの行動
    p_now = alive_players[game.current_turn_idx]
    
    st.info(f"プレイヤー: {p_now.name}")
    if st.checkbox(f"私は {p_now.name} です", key=f"night_act_{p_now.idx}"):
        role = p_now.role
        st.success(f"あなたの役職: {role.role_name}")
        
        # --- 人狼の行動 ---
        if isinstance(role, Werewolf):
            alive_wolves = game.get_alive_wolves()
            st.info("👥 **仲間の人狼**:")
            cols = st.columns(3)
            for i, w in enumerate(alive_wolves):
                with cols[i%3]: st.success(f"{w.name}", icon="🐺")
            
            st.subheader("襲撃")
            col1, col2 = st.columns(2)
            with col1:
                conf = st.radio("自信", ["あり", "なし"], key=f"w_conf_{p_now.idx}")
            with col2:
                # 自分以外の生存者
                targets = [p for p in alive_players if p.idx != p_now.idx]
                target_name = st.selectbox("襲撃対象", [p.name for p in targets], key=f"w_tgt_{p_now.idx}")
            
            if st.button("決定", use_container_width=True):
                target_obj = next(p for p in targets if p.name == target_name)
                game.register_wolf_vote(p_now.idx, target_obj.idx, conf == "あり")
                game.current_turn_idx += 1
                st.rerun()

        # --- 狂信者の行動 ---
        elif isinstance(role, Fanatic):
            alive_wolves = game.get_alive_wolves()
            st.info("👥 **ご主人様（人狼）**: ")
            if alive_wolves:
                cols = st.columns(3)
                for i, w in enumerate(alive_wolves):
                    with cols[i%3]: st.success(f"{w.name}", icon="🐺")
            else:
                st.warning("人狼は全滅しています。")
            
            if st.button("確認して次へ", use_container_width=True):
                game.current_turn_idx += 1
                st.rerun()

        # --- 占い師の行動 ---
        elif isinstance(role, Seer):
            # 既に結果が出ている場合（結果確認待ち）
            # Note: シンプル化のため、行動→即結果表示→次へボタンとする
            targets = [p for p in alive_players if p.idx != p_now.idx]
            target_name = st.selectbox("占う相手", [p.name for p in targets], key=f"s_tgt_{p_now.idx}")
            
            # 結果表示用state
            res_key = f"seer_res_{p_now.idx}"
            if res_key not in st.session_state:
                if st.button("占う", use_container_width=True):
                    target_obj = next(p for p in targets if p.name == target_name)
                    res_text = game.register_seer_action(p_now.idx, target_obj.idx)
                    st.session_state[res_key] = res_text
                    st.rerun()
            else:
                st.error(f"🔮 **占い結果**: {st.session_state[res_key]}")
                if st.button("確認して次へ", use_container_width=True):
                    del st.session_state[res_key]
                    game.current_turn_idx += 1
                    st.rerun()

        # --- 騎士の行動 ---
        elif isinstance(role, Guard):
            targets = alive_players # 自分も守れる
            target_name = st.selectbox("守る相手", [p.name for p in targets], key=f"g_tgt_{p_now.idx}")
            if st.button("守る", use_container_width=True):
                target_obj = next(p for p in targets if p.name == target_name)
                game.register_guard_action(p_now.idx, target_obj.idx)
                game.current_turn_idx += 1
                st.rerun()

        # --- 霊媒師の行動 ---
        elif isinstance(role, Medium):
            medium_text = game.get_medium_result_text()
            if medium_text:
                st.info(medium_text)
            else:
                st.info("前日に処刑された人はいません。")
            
            if st.button("確認して次へ", use_container_width=True):
                game.current_turn_idx += 1
                st.rerun()

        # --- 夜行動のない役職 ---
        else:
            st.info("夜の行動はありません。")
            if st.button("次へ", use_container_width=True):
                game.current_turn_idx += 1
                st.rerun()

elif game.phase == "day":
    st.header(f"{game.day_count-1}日目の昼")
    st.info(game.last_night_info)

    st.subheader("生存者")
    alive = game.get_alive_players()
    cols = st.columns(3)
    for i, p in enumerate(alive):
        with cols[i % 3]:
            st.button(p.name, key=f"alive_btn_{p.idx}", disabled=True)

    if st.button("投票へ", use_container_width=True):
        game.phase = "vote"
        st.rerun()

elif game.phase == "vote":
    st.header(f"{game.day_count-1}日目の投票")
    alive = game.get_alive_players()
    
    target_name = st.selectbox("処刑対象", [p.name for p in alive])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("処刑する", use_container_width=True):
            target_obj = next(p for p in alive if p.name == target_name)
            game.execute_player(target_obj.idx)
            game.phase = "result"
            st.rerun()
    with col2:
        if st.button("スキップ", use_container_width=True):
            game.execute_player(None) # 誰も処刑しない
            game.phase = "result"
            st.rerun()

elif game.phase == "result":
    st.header("結果")
    
    # 勝敗チェック
    has_winner = game.check_winner()

    st.subheader("現在の生存状況")
    cols = st.columns(3)
    for i, p in enumerate(game.players):
        status = "🟢" if p.is_alive else "🔴"
        with cols[i % 3]:
            st.button(f"{p.name} {status}", key=f"res_view_{i}", disabled=True)

    if has_winner:
        st.success(f"{game.game_winner}の勝利！")
        if st.button("メニューに戻る", use_container_width=True):
            st.session_state.game = WerewolfGame()
            st.rerun()
    else:
        if st.button("次の夜へ", use_container_width=True):
            game.phase = "night"
            st.rerun()
