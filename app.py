import random
import streamlit as st

def get_theme():
    if st.session_state.get("phase") == "night":
        return {"bg": "#1e1e2e", "fg": "#cdd6f4"}
    return {"bg": "#eff1f5", "fg": "#4c4f69"}

def init_game_state():
    st.session_state.clear()
    st.session_state.phase = "menu"
    st.session_state.num_players = 4
    st.session_state.roles = [None] * 11
    st.session_state.alive = [False] * 11
    st.session_state.player_names = [f"P{i+1}" for i in range(11)]
    st.session_state.day_count = 1
    st.session_state.current_player = 0
    st.session_state.night_actions = {
        "guard_target": None,
        "seer_target": None,
        "medium_target": None,
        "wolf_votes": {},
        "seer_result": None,
        "seer_killed": None,   # 占いで死亡したプレイヤー（妖狐呪殺用）
    }
    st.session_state.last_night_info = ""
    st.session_state.game_winner = None
    st.session_state.log = []
    st.session_state.executed_yesterday = None

if "phase" not in st.session_state:
    init_game_state()

def get_player_name(idx):
    return st.session_state.player_names[idx] if idx < len(st.session_state.player_names) else f"P{idx+1}"

def get_alive_players():
    return [i for i, alive in enumerate(st.session_state.alive[:st.session_state.num_players]) if alive]

def get_alive_wolves():
    return [
        i for i, r in enumerate(st.session_state.roles[:st.session_state.num_players])
        if r == "人狼" and st.session_state.alive[i]
    ]

def get_faction(role: str) -> str:
    """占い結果（妖狐・狂人も村人陣営として表示）"""
    if role == "人狼":
        return "人狼陣営"
    # 狂人・妖狐・その他村側役職は全部「村人陣営」
    return "村人陣営"

def get_medium_result(role: str) -> str:
    """霊媒結果（妖狐は妖狐と出る）"""
    if role == "妖狐":
        return "妖狐"
    return role

def add_log(message):
    st.session_state.log.append(f"Day{st.session_state.day_count}: {message}")
    if len(st.session_state.log) > 20:
        st.session_state.log.pop(0)

# テーマ適用
theme = get_theme()
st.markdown(
    f"""
    <style>
    .main {{background-color: {theme['bg']}; color: {theme['fg']};}}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("人狼ゲーム")

# サイドバー
with st.sidebar:
    st.header("ゲームログ")
    if hasattr(st.session_state, "log") and st.session_state.log:
        for log in st.session_state.log[-10:]:
            st.write(log)
    if st.button("状態リセット"):
        init_game_state()
        st.rerun()

if st.session_state.phase == "menu":
    st.header("ゲームメニュー")
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("新規ゲーム開始", use_container_width=True):
            st.session_state.phase = "setup"
            st.rerun()
    with col2:
        if st.button("リセット", use_container_width=True):
            init_game_state()
            st.rerun()

elif st.session_state.phase == "setup":
    st.header("ゲーム設定")
    st.session_state.num_players = st.slider("プレイヤー数", 4, 11, 6)

    st.subheader("プレイヤー名")
    for i in range(st.session_state.num_players):
        st.session_state.player_names[i] = st.text_input(
            f"P{i+1}", value=st.session_state.player_names[i], key=f"name_{i}"
        )

    st.subheader("役職構成")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        num_wolf = st.number_input(
            "人狼", 1, st.session_state.num_players // 2, 2, key="num_wolf"
        )
    with col2:
        num_seer = st.number_input("占い師", 0, 1, 1, key="num_seer")
    with col3:
        num_guard = st.number_input("騎士", 0, 1, 1, key="num_guard")
    with col4:
        num_medium = st.number_input("霊媒師", 0, 1, 0, key="num_medium")
    with col5:
        num_madman = st.number_input("狂人", 0, 1, 0, key="num_madman")
    with col6:
        num_fox = st.number_input("妖狐", 0, 1, 0, key="num_fox")

    num_villager = (
        st.session_state.num_players
        - num_wolf
        - num_seer
        - num_guard
        - num_medium
        - num_madman
        - num_fox
    )
    st.metric("村人", num_villager)

    if st.button("ゲーム開始", use_container_width=True):
        roles = (
            ["村人"] * num_villager
            + ["人狼"] * num_wolf
            + ["占い師"] * num_seer
            + ["騎士"] * num_guard
            + ["霊媒師"] * num_medium
            + ["狂人"] * num_madman
            + ["妖狐"] * num_fox
        )
        random.shuffle(roles)
        st.session_state.roles[: st.session_state.num_players] = roles
        st.session_state.alive[: st.session_state.num_players] = [True] * st.session_state.num_players
        st.session_state.log = []
        st.session_state.executed_yesterday = None
        add_log("ゲーム開始")
        st.session_state.phase = "show_roles"
        st.session_state.current_player = 0
        st.rerun()

elif st.session_state.phase == "show_roles":
    st.header("役職確認")
    current_idx = st.session_state.current_player
    name = get_player_name(current_idx)

    st.info(f"プレイヤー {current_idx+1}: {name}")

    if st.checkbox(f"私は {name} です", key=f"role_confirm_{current_idx}"):
        st.success(f"あなたの役職: **{st.session_state.roles[current_idx]}**")
        if st.button("確認完了（次へ）", use_container_width=True):
            st.session_state.current_player += 1
            if st.session_state.current_player >= st.session_state.num_players:
                add_log("全員役職確認完了。1日目の昼へ")
                st.session_state.phase = "day"
                st.session_state.current_player = 0
                st.rerun()
            st.rerun()
    else:
        st.info("「私は〇〇です」にチェックを入れて本人確認してください")

elif st.session_state.phase == "night":
    st.header(f"{st.session_state.day_count}日目の夜")
    alive_players = get_alive_players()

    if st.session_state.current_player < len(alive_players):
        p_idx = alive_players[st.session_state.current_player]
        role = st.session_state.roles[p_idx]
        name = get_player_name(p_idx)

        st.info(f"プレイヤー {p_idx+1}: {name}")

        if st.checkbox(f"私は {name} です", key=f"night_confirm_{p_idx}"):
            st.success(f"あなたの役職: {role}")

            if role == "人狼":
                alive_wolves = get_alive_wolves()
                st.info("👥 **仲間の人狼**:")
                cols = st.columns(3)
                for i, wolf in enumerate(alive_wolves):
                    with cols[i % 3]:
                        st.success(f"{get_player_name(wolf)}(P{wolf+1})", icon="🐺")

                st.subheader("人狼の襲撃")
                col1, col2 = st.columns(2)
                with col1:
                    confidence = st.radio(
                        "自信", ["あり", "なし"], key=f"wolf_conf{p_idx}"
                    )
                with col2:
                    target = st.selectbox(
                        "襲撃対象",
                        [i for i in alive_players if i != p_idx],
                        key=f"wolf_target{p_idx}",
                    )
                if st.button("決定", use_container_width=True):
                    st.session_state.night_actions["wolf_votes"][p_idx] = (
                        target,
                        confidence == "あり",
                    )
                    st.session_state.current_player += 1
                    st.rerun()

            elif role == "占い師" and st.session_state.night_actions.get("seer_result"):
                st.error(f"🔮 **占い結果**: {st.session_state.night_actions['seer_result']}")
                if st.button("結果確認済み（次へ）", use_container_width=True):
                    st.session_state.current_player += 1
                    st.rerun()

            else:
                if role == "占い師":
                    st.subheader("占い師の行動")
                    target = st.selectbox(
                        "占う相手", [i for i in alive_players if i != p_idx]
                    )
                    if st.button("占う", use_container_width=True):
                        target_role = st.session_state.roles[target]
                        result = get_faction(target_role)
                        st.session_state.night_actions["seer_target"] = target
                        st.session_state.night_actions["seer_result"] = (
                            f"{get_player_name(target)}: {result}"
                        )
                        # 妖狐なら呪殺フラグ
                        if target_role == "妖狐":
                            st.session_state.night_actions["seer_killed"] = target
                        else:
                            st.session_state.night_actions["seer_killed"] = None
                        st.rerun()

                elif role == "騎士":
                    st.subheader("騎士の行動")
                    target = st.selectbox(
                        "守る相手", alive_players
                    )
                    if st.button("守る", use_container_width=True):
                        st.session_state.night_actions["guard_target"] = target
                        st.session_state.current_player += 1
                        st.rerun()

                elif role == "霊媒師":
                    st.subheader("霊媒師の確認")
                    if (
                        st.session_state.executed_yesterday is not None
                        and not st.session_state.alive[st.session_state.executed_yesterday]
                    ):
                        idx = st.session_state.executed_yesterday
                        dead_role = st.session_state.roles[idx]
                        medium_text = get_medium_result(dead_role)
                        st.info(
                            f"前日処刑者: {get_player_name(idx)}（{medium_text}）"
                        )
                    if st.button("次へ", use_container_width=True):
                        st.session_state.current_player += 1
                        st.rerun()

                elif role in ["狂人", "妖狐"]:
                    st.info(f"{role}は夜に行動しません")
                    if st.button("次へ", use_container_width=True):
                        st.session_state.current_player += 1
                        st.rerun()

                else:
                    st.info("村人は夜に行動しません")
                    if st.button("次へ", use_container_width=True):
                        st.session_state.current_player += 1
                        st.rerun()
        else:
            st.info("「私は〇〇です」にチェックを入れて本人確認してください")

    else:
        # 夜フェーズ終了処理（妖狐呪殺＋襲撃で最大2人死亡）
        wolves = get_alive_wolves()
        attack_target = None

        if wolves and st.session_state.night_actions["wolf_votes"]:
            confident = [
                (t, c)
                for _, (t, c) in st.session_state.night_actions["wolf_votes"].items()
                if c
            ]
            if confident:
                attack_target = random.choice([t for t, _ in confident])
            else:
                attack_target = list(
                    st.session_state.night_actions["wolf_votes"].values()
                )[0][0]

        seer_killed = st.session_state.night_actions.get("seer_killed")
        guard_target = st.session_state.night_actions.get("guard_target")

        night_deaths = []

        # 1) 妖狐呪殺（占いで死亡）
        if seer_killed is not None and st.session_state.alive[seer_killed]:
            st.session_state.alive[seer_killed] = False
            night_deaths.append(seer_killed)

        # 2) 人狼襲撃
        if attack_target is not None and st.session_state.alive[attack_target]:
            # 妖狐で、まだ呪殺されていない ⇒ 襲撃無効
            if (
                st.session_state.roles[attack_target] == "妖狐"
                and attack_target not in night_deaths
            ):
                # 何も起きない（ログだけ統一）
                pass
            # 守護されていなければ襲撃成功
            elif attack_target != guard_target:
                st.session_state.alive[attack_target] = False
                night_deaths.append(attack_target)

        # 結果メッセージ
        if not night_deaths:
            msg = "昨夜の犠牲者はいませんでした"
        elif len(night_deaths) == 1:
            v = night_deaths[0]
            msg = f"{get_player_name(v)}が死亡しました"
        else:
            names = "、".join(get_player_name(i) for i in night_deaths)
            msg = f"{names}が死亡しました"

        st.session_state.last_night_info = msg
        add_log(msg)
        add_log(f"{st.session_state.day_count}日目の朝が訪れました")

        st.session_state.phase = "day"
        st.session_state.day_count += 1
        st.session_state.current_player = 0
        st.session_state.night_actions = {
            "guard_target": None,
            "seer_target": None,
            "medium_target": None,
            "wolf_votes": {},
            "seer_result": None,
            "seer_killed": None,
        }
        st.rerun()

elif st.session_state.phase == "day":
    st.header(f"{st.session_state.day_count-1}日目の昼")
    st.info(st.session_state.last_night_info)

    st.subheader("生存者")
    alive = get_alive_players()
    cols = st.columns(3)
    for i, p in enumerate(alive):
        with cols[i % 3]:
            st.button(get_player_name(p), key=f"alive_{p}", disabled=True)

    if st.button("投票へ", use_container_width=True):
        st.session_state.phase = "vote"
        st.rerun()

elif st.session_state.phase == "vote":
    st.header(f"{st.session_state.day_count-1}日目の投票")
    alive = get_alive_players()

    selected = st.selectbox(
        "処刑対象", [f"{get_player_name(i)}(P{i+1})" for i in alive]
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("処刑する", use_container_width=True):
            exec_idx = next(
                i for i in alive if f"{get_player_name(i)}(P{i+1})" == selected
            )
            st.session_state.alive[exec_idx] = False
            st.session_state.executed_yesterday = exec_idx
            add_log(f"{get_player_name(exec_idx)}が処刑されました")
            st.session_state.phase = "result"
            st.rerun()
    with col2:
        if st.button("スキップ（処刑しない）", use_container_width=True):
            st.session_state.phase = "result"
            st.rerun()

elif st.session_state.phase == "result":
    st.header("結果")

    st.subheader("生存状況")
    cols = st.columns(3)
    for i in range(st.session_state.num_players):
        if st.session_state.roles[i] is not None:
            status = "🟢" if st.session_state.alive[i] else "🔴"
            with cols[i % 3]:
                st.button(
                    f"{get_player_name(i)}{status}",
                    key=f"result_{i}",
                    disabled=True,
                )

    alive_fox = sum(
        1
        for i in range(st.session_state.num_players)
        if st.session_state.alive[i] and st.session_state.roles[i] == "妖狐"
    )
    alive_wolves = sum(
        1
        for i in range(st.session_state.num_players)
        if st.session_state.alive[i] and st.session_state.roles[i] == "人狼"
    )
    alive_count = len(get_alive_players())
   
    if alive_wolves == 0:
        if alive_fox > 0:
            st.session_state.game_winner = "妖狐"
            add_log("妖狐の勝利")
        else:
            st.session_state.game_winner = "村人陣営"
            add_log("村人陣営の勝利")
    elif alive_count == alive_wolves:
        if alive_fox > 0:
            st.session_state.game_winner = "妖狐"
            add_log("妖狐の勝利")
        else:
            st.session_state.game_winner = "人狼陣営"
            add_log("人狼陣営の勝利")

    if st.session_state.game_winner:
        st.success(f"{st.session_state.game_winner}の勝利！")
        if st.button("メニューに戻る", use_container_width=True):
            init_game_state()
            st.rerun()
    else:
        if st.button("次の夜へ", use_container_width=True):
            st.session_state.phase = "night"
            st.session_state.current_player = 0
            st.session_state.night_actions = {
                "guard_target": None,
                "seer_target": None,
                "medium_target": None,
                "wolf_votes": {},
                "seer_result": None,
                "seer_killed": None,
            }
            st.rerun()
