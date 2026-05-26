"""
4×8 象棋翻棋 — Streamlit 双人对战 / 人机对战
"""

import random
import streamlit as st

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
ROWS, COLS = 4, 8

CHESS_WEIGHT = {
    "将": 9, "帅": 9,
    "士": 8, "仕": 8,
    "象": 7, "相": 7,
    "马": 6,
    "车": 5,
    "炮": 4,
    "兵": 3, "卒": 3,
}

RED_SET = {"将", "士", "象", "兵"}
BLUE_SET = {"帅", "仕", "相", "卒"}

STALE_LIMIT = 10  # 平局：连续无吃子、无翻新的回合数


def build_piece_pool():
    """生成 32 枚棋子，每枚带固定阵营 camp。"""
    red = (
        ["将"]
        + ["士"] * 2
        + ["象"] * 2
        + ["马"] * 2
        + ["车"] * 2
        + ["炮"] * 2
        + ["兵"] * 5
    )
    blue = (
        ["帅"]
        + ["仕"] * 2
        + ["相"] * 2
        + ["马"] * 2
        + ["车"] * 2
        + ["炮"] * 2
        + ["卒"] * 5
    )
    pool = [(n, "red") for n in red] + [(n, "blue") for n in blue]
    random.shuffle(pool)
    return pool


def new_cell(chess, camp):
    return {"status": "dark", "chess": chess, "camp": camp}


def empty_cell():
    return {"status": "empty", "chess": None, "camp": None}


def init_session():
    pool = build_piece_pool()
    board = []
    idx = 0
    for _ in range(ROWS):
        row = []
        for _ in range(COLS):
            chess, camp = pool[idx]
            row.append(new_cell(chess, camp))
            idx += 1
        board.append(row)

    st.session_state.board = board
    st.session_state.page = "game"
    st.session_state.selected = None  # (r, c)
    st.session_state.turn = None  # 未分色前为 None；之后 "red" / "blue"
    st.session_state.red_holder = None  # "p1" / "p2" / "human" / "ai"
    st.session_state.blue_holder = None
    st.session_state.message = "请翻开任意一枚暗棋以确定阵营"
    st.session_state.winner = None
    st.session_state.is_draw = False
    st.session_state.stale_turns = 0
    st.session_state.just_flipped = None  # 本回合刚翻开的格子 (r,c)
    st.session_state.pending_ai = False


def reset_to_menu():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.page = "menu"


def holders():
    """返回 (red方标识, blue方标识)。"""
    return st.session_state.red_holder, st.session_state.blue_holder


def camp_of_turn():
    return st.session_state.turn


def is_human_turn():
    mode = st.session_state.game_mode
    turn = st.session_state.turn
    rh, bh = holders()
    if mode == "pvp":
        return True
    if turn == "red":
        return rh == "human"
    return bh == "human"


def assign_colors_on_first_flip(camp):
    """先手翻开棋子后分配双方颜色。"""
    mode = st.session_state.game_mode
    if camp == "red":
        st.session_state.red_holder = "human" if mode == "pvai" else "p1"
        st.session_state.blue_holder = "ai" if mode == "pvai" else "p2"
    else:
        st.session_state.blue_holder = "human" if mode == "pvai" else "p1"
        st.session_state.red_holder = "ai" if mode == "pvai" else "p2"
    st.session_state.turn = camp


def switch_turn():
    st.session_state.turn = "blue" if st.session_state.turn == "red" else "red"
    st.session_state.selected = None
    st.session_state.just_flipped = None


def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def neighbors(r, c):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield nr, nc


def cell_at(r, c):
    return st.session_state.board[r][c]


def count_pieces(camp):
    """统计某阵营仍在棋盘上的棋子数（含暗棋）。"""
    n = 0
    for r in range(ROWS):
        for c in range(COLS):
            cell = cell_at(r, c)
            if cell["status"] != "empty" and cell["camp"] == camp:
                n += 1
    return n


def general_alive(camp):
    """将/帅是否仍在棋盘上（含暗棋）。"""
    target = "将" if camp == "red" else "帅"
    for r in range(ROWS):
        for c in range(COLS):
            cell = cell_at(r, c)
            if cell["status"] != "empty" and cell["chess"] == target:
                return True
    return False


def compare_strength(attacker, defender):
    """从进攻方视角：'win' / 'lose' / 'tie'。"""
    if attacker in ("兵", "卒") and defender in ("将", "帅"):
        return "win"
    if defender in ("兵", "卒") and attacker in ("将", "帅"):
        return "lose"
    wa, wd = CHESS_WEIGHT[attacker], CHESS_WEIGHT[defender]
    if wa > wd:
        return "win"
    if wa == wd:
        return "tie"
    return "lose"


def cannon_has_mount(r1, c1, r2, c2):
    """炮翻吃：两点同线且之间恰好隔一子（任意状态，非空即可）。"""
    if r1 != r2 and c1 != c2:
        return False
    between = []
    if r1 == r2:
        step = 1 if c2 > c1 else -1
        for c in range(c1 + step, c2, step):
            between.append(cell_at(r1, c))
    else:
        step = 1 if r2 > r1 else -1
        for row in range(r1 + step, r2, step):
            between.append(cell_at(row, c1))
    non_empty = [x for x in between if x["status"] != "empty"]
    return len(non_empty) == 1


def can_flip_capture_from(fr, fc, tr, tc):
    """是否可从 (fr,fc) 对 (tr,tc) 主动翻吃。"""
    src, tgt = cell_at(fr, fc), cell_at(tr, tc)
    if src["status"] != "open" or tgt["status"] != "dark":
        return False
    if src["camp"] != camp_of_turn():
        return False
    if st.session_state.just_flipped == (fr, fc):
        return False

    chess = src["chess"]
    if chess == "炮":
        if (fr, fc) in neighbors(tr, tc):
            return True
        return cannon_has_mount(fr, fc, tr, tc)
    return (fr, fc) in neighbors(tr, tc)


def can_move_to(fr, fc, tr, tc):
    src, tgt = cell_at(fr, fc), cell_at(tr, tc)
    if src["status"] != "open" or tgt["status"] != "empty":
        return False
    if src["camp"] != camp_of_turn():
        return False
    if st.session_state.just_flipped == (fr, fc):
        return False
    return (fr, fc) in neighbors(tr, tc)


def can_simple_flip(r, c):
    cell = cell_at(r, c)
    return cell["status"] == "dark" and st.session_state.selected is None


def check_end_after_action(captured_general):
    if captured_general:
        loser = "blue" if captured_general == "将" else "red"
        winner = "red" if loser == "blue" else "blue"
        st.session_state.winner = winner
        rh, bh = holders()
        if st.session_state.game_mode == "pvp":
            st.session_state.message = (
                f"{'红' if winner == 'red' else '蓝'}方获胜！"
            )
        else:
            if (winner == "red" and rh == "human") or (winner == "blue" and bh == "human"):
                st.session_state.message = "恭喜你获胜！"
            else:
                st.session_state.message = "AI 获胜，再接再厉！"
        return

    if not general_alive("red"):
        st.session_state.winner = "blue"
        st.session_state.message = "蓝方获胜！红方将被吃。"
        return
    if not general_alive("blue"):
        st.session_state.winner = "red"
        st.session_state.message = "红方获胜！蓝方帅被吃。"
        return

    red_n = count_pieces("red")
    blue_n = count_pieces("blue")
    if red_n == 1 and blue_n == 1 and st.session_state.stale_turns >= STALE_LIMIT:
        st.session_state.is_draw = True
        st.session_state.message = f"平局！双方各剩 1 子，连续 {STALE_LIMIT} 回合无吃子且无翻新。"


def end_turn(moved_only=False, flipped_new=False, captured=False):
    """回合结束：更新僵局计数并换手。"""
    if captured or flipped_new:
        st.session_state.stale_turns = 0
    elif moved_only:
        st.session_state.stale_turns += 1
    else:
        st.session_state.stale_turns += 1

    check_end_after_action(st.session_state.get("last_capture_general"))
    st.session_state.last_capture_general = None

    if st.session_state.winner or st.session_state.is_draw:
        return

    switch_turn()
    mode = st.session_state.game_mode
    if mode == "pvai" and not is_human_turn():
        st.session_state.pending_ai = True


# ---------------------------------------------------------------------------
# 动作执行
# ---------------------------------------------------------------------------
def do_simple_flip(r, c):
    cell = cell_at(r, c)
    if cell["status"] != "dark":
        return False

    flipped_new = True
    cell["status"] = "open"

    if st.session_state.turn is None:
        assign_colors_on_first_flip(cell["camp"])
        side = "红" if cell["camp"] == "red" else "蓝"
        if st.session_state.game_mode == "pvai":
            st.session_state.message = f"你执{side}方。"
        else:
            st.session_state.message = f"先手执{side}方，轮到后手。"
        st.session_state.just_flipped = (r, c)
        end_turn(flipped_new=True)
        return True

    st.session_state.just_flipped = (r, c)
    st.session_state.message = f"翻开了 {cell['chess']}，本回合不能移动该子。"
    end_turn(flipped_new=True)
    return True


def do_move(fr, fc, tr, tc):
    if not can_move_to(fr, fc, tr, tc):
        return False
    board = st.session_state.board
    board[tr][tc] = {**board[fr][fc]}
    board[fr][fc] = empty_cell()
    st.session_state.message = f"移动 {board[tr][tc]['chess']} 到 ({tr+1},{tc+1})。"
    end_turn(moved_only=True)
    return True


def do_flip_capture(fr, fc, tr, tc):
    if not can_flip_capture_from(fr, fc, tr, tc):
        return False

    board = st.session_state.board
    attacker = board[fr][fc]
    dark = board[tr][tc]
    player = camp_of_turn()
    captured_general = None
    flipped_new = True

    if dark["camp"] == player:
        dark["status"] = "open"
        st.session_state.message = f"翻开己方 {dark['chess']}，和平翻开。"
        end_turn(flipped_new=True)
        return True

    # 敌方暗棋
    result = compare_strength(attacker["chess"], dark["chess"])
    dark["status"] = "open"

    if result == "win":
        if dark["chess"] in ("将", "帅"):
            captured_general = dark["chess"]
        board[tr][tc] = {**attacker, "status": "open"}
        board[fr][fc] = empty_cell()
        st.session_state.message = f"{attacker['chess']} 翻吃 {dark['chess']}！"
    elif result == "tie":
        if dark["chess"] in ("将", "帅"):
            captured_general = dark["chess"]
        if attacker["chess"] in ("将", "帅"):
            captured_general = attacker["chess"]
        board[tr][tc] = empty_cell()
        board[fr][fc] = empty_cell()
        st.session_state.message = f"{attacker['chess']} 与 {dark['chess']} 同归于尽！"
    else:
        if attacker["chess"] in ("将", "帅"):
            captured_general = attacker["chess"]
        board[tr][tc] = {**dark, "status": "open"}
        board[fr][fc] = empty_cell()
        st.session_state.message = f"{dark['chess']} 反吃 {attacker['chess']}！"

    st.session_state.last_capture_general = captured_general
    end_turn(flipped_new=True, captured=captured_general is not None)
    return True


def handle_cell_click(r, c):
    if st.session_state.winner or st.session_state.is_draw:
        return
    if not is_human_turn() and st.session_state.game_mode == "pvai":
        return

    cell = cell_at(r, c)
    sel = st.session_state.selected

    # 未分色：只能简单翻
    if st.session_state.turn is None:
        if cell["status"] == "dark":
            do_simple_flip(r, c)
        return

    # 无选中
    if sel is None:
        if cell["status"] == "dark":
            do_simple_flip(r, c)
            return
        if cell["status"] == "open" and cell["camp"] == camp_of_turn():
            if st.session_state.just_flipped != (r, c):
                st.session_state.selected = (r, c)
                st.session_state.message = f"已选中 {cell['chess']}，请选择相邻空格移动，或翻吃相邻（炮可隔一子）暗棋。"
        return

    fr, fc = sel
    if (r, c) == sel:
        st.session_state.selected = None
        st.session_state.message = "已取消选择。"
        return

    if can_move_to(fr, fc, r, c):
        st.session_state.selected = None
        do_move(fr, fc, r, c)
        return

    if can_flip_capture_from(fr, fc, r, c):
        st.session_state.selected = None
        do_flip_capture(fr, fc, r, c)
        return

    if cell["status"] == "open" and cell["camp"] == camp_of_turn() and (r, c) != sel:
        st.session_state.selected = (r, c)
        st.session_state.message = f"改选 {cell['chess']}。"
        return

    st.session_state.message = "无效操作：只能移动至相邻空格，或翻吃合法暗棋。"


# ---------------------------------------------------------------------------
# AI（蓝方或对立阵营由 ai holder 决定）
# ---------------------------------------------------------------------------
def ai_camp():
    rh, bh = holders()
    return "blue" if bh == "ai" else "red"


def run_ai():
    if st.session_state.winner or st.session_state.is_draw:
        st.session_state.pending_ai = False
        return

    camp = ai_camp()
    st.session_state.turn = camp
    board = st.session_state.board

    # 若尚未分色（理论上不会）
    if camp is None:
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c]["status"] == "dark":
                    do_simple_flip(r, c)
                    return

    captures = []
    flips = []
    moves = []

    for r in range(ROWS):
        for c in range(COLS):
            src = board[r][c]
            if src["status"] != "open" or src["camp"] != camp:
                continue
            if st.session_state.just_flipped == (r, c):
                continue
            for tr in range(ROWS):
                for tc in range(COLS):
                    if can_flip_capture_from(r, c, tr, tc):
                        tgt = board[tr][tc]
                        if tgt["camp"] != camp:
                            result = compare_strength(src["chess"], tgt["chess"])
                            if result == "win":
                                captures.insert(0, (r, c, tr, tc, 3))
                            elif result == "tie":
                                captures.append((r, c, tr, tc, 2))
                            else:
                                captures.append((r, c, tr, tc, 1))
                        else:
                            flips.append((r, c, tr, tc))
                    if can_move_to(r, c, tr, tc):
                        moves.append((r, c, tr, tc))

    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]["status"] == "dark":
                flips.append(("simple", r, c))

    if captures:
        captures.sort(key=lambda x: -x[4])
        r, c, tr, tc, _ = captures[0]
        do_flip_capture(r, c, tr, tc)
        st.session_state.pending_ai = False
        return

    # 优先主动翻吃（己方暗棋），其次简单翻子
    active_flips = [x for x in flips if x[0] != "simple"]
    if active_flips:
        r, c, tr, tc = random.choice(active_flips)
        do_flip_capture(r, c, tr, tc)
        st.session_state.pending_ai = False
        return

    simple = [x for x in flips if x[0] == "simple"]
    if simple:
        _, r, c = random.choice(simple)
        do_simple_flip(r, c)
        st.session_state.pending_ai = False
        return

    if moves:
        r, c, tr, tc = random.choice(moves)
        do_move(r, c, tr, tc)
        st.session_state.pending_ai = False
        return

    st.session_state.message = "AI 无合法着法。"
    st.session_state.pending_ai = False


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        /* 去掉默认宽屏留白，防止横向滚动 */
        .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 100%; }
        header[data-testid="stHeader"] { background: transparent; }
        h1 { text-align: center; font-size: clamp(1.2rem, 4vw, 1.8rem) !important; margin-bottom: 0.2rem; }
        .status-bar {
            text-align: center;
            padding: 0.5rem 0.75rem;
            margin: 0.5rem auto;
            max-width: 42rem;
            background: linear-gradient(135deg, #f5e6c8 0%, #e8d4a8 100%);
            border-radius: 10px;
            font-size: clamp(0.85rem, 2.5vw, 1rem);
            border: 1px solid #c4a574;
        }
        .board-wrap {
            width: min(100%, 720px);
            margin: 0 auto;
            padding: 0.25rem;
            box-sizing: border-box;
        }
        div[data-testid="column"] { padding: 2px !important; }
        /* 棋子按钮 */
        div.stButton > button {
            width: 100% !important;
            min-height: clamp(2.4rem, 11vw, 3.5rem) !important;
            padding: 0.15rem !important;
            border-radius: 50% !important;
            font-size: clamp(0.75rem, 3.2vw, 1.15rem) !important;
            font-weight: 700 !important;
            line-height: 1.1 !important;
            border: 2px solid #5c4033 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.25);
        }
        div.stButton > button[kind="primary"] {
            box-shadow: 0 0 0 3px #ffd700, 0 2px 6px rgba(0,0,0,0.35) !important;
        }
        .btn-dark > button {
            background: linear-gradient(145deg, #4a3728, #2c1810) !important;
            color: #d4a574 !important;
        }
        .btn-red > button {
            background: radial-gradient(circle at 30% 30%, #ff6b6b, #c0392b) !important;
            color: #fff8e7 !important;
        }
        .btn-blue > button {
            background: radial-gradient(circle at 30% 30%, #5dade2, #2471a3) !important;
            color: #fff8e7 !important;
        }
        .btn-empty > button {
            background: #c9b896 !important;
            color: transparent !important;
            border: 1px dashed #8b7355 !important;
            min-height: clamp(2.2rem, 10vw, 3.2rem) !important;
        }
        .menu-box {
            max-width: 22rem;
            margin: 2rem auto;
            text-align: center;
        }
        @media (max-width: 480px) {
            .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def cell_label(cell):
    if cell["status"] == "empty":
        return "·"
    if cell["status"] == "dark":
        return "?"
    return cell["chess"]


def cell_button_type(cell, r, c):
    if st.session_state.selected == (r, c):
        return "primary"
    return "secondary"


def render_board():
    st.markdown('<div class="board-wrap">', unsafe_allow_html=True)
    board = st.session_state.board
    for r in range(ROWS):
        cols = st.columns(COLS)
        for c in range(COLS):
            cell = board[r][c]
            label = cell_label(cell)
            key = f"cell_{r}_{c}"

            css_class = "btn-dark"
            if cell["status"] == "open":
                css_class = "btn-red" if cell["camp"] == "red" else "btn-blue"
            elif cell["status"] == "empty":
                css_class = "btn-empty"

            with cols[c]:
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                disabled = bool(st.session_state.winner or st.session_state.is_draw)
                if st.session_state.game_mode == "pvai" and not is_human_turn():
                    disabled = True
                st.button(
                    label,
                    key=key,
                    on_click=handle_cell_click,
                    args=(r, c),
                    disabled=disabled,
                    type=cell_button_type(cell, r, c),
                )
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def turn_hint():
    if st.session_state.winner or st.session_state.is_draw:
        return st.session_state.message

    mode = st.session_state.game_mode
    turn = st.session_state.turn
    if turn is None:
        return st.session_state.message

    side = "红" if turn == "red" else "蓝"
    rh, bh = holders()
    if mode == "pvp":
        if (turn == "red" and rh == "p1") or (turn == "blue" and bh == "p1"):
            who = "先手（玩家一）"
        else:
            who = "后手（玩家二）"
        return f"当前：{side}方 — {who} | 僵局计数 {st.session_state.stale_turns}/{STALE_LIMIT}"

    if is_human_turn():
        return f"你的回合（{side}方）| 僵局 {st.session_state.stale_turns}/{STALE_LIMIT}"
    return f"AI 回合（{side}方）…"


def page_menu():
    st.title("象棋翻棋 4×8")
    st.markdown(
        """
        <div class="menu-box">
        <p>32 枚象棋暗摆，翻子定色，翻吃博弈。<br>
        吃掉对方将/帅获胜。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("双人对战（同屏）", use_container_width=True, type="primary"):
            st.session_state.game_mode = "pvp"
            init_session()
            st.rerun()
        if st.button("人机对战（你 vs AI）", use_container_width=True):
            st.session_state.game_mode = "pvai"
            init_session()
            st.rerun()


def page_game():
    st.title("象棋翻棋")
    st.markdown(f'<div class="status-bar">{turn_hint()}<br><small>{st.session_state.message}</small></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("返回菜单", use_container_width=True):
            reset_to_menu()
            st.rerun()
    with c2:
        if st.button("重新开局", use_container_width=True):
            mode = st.session_state.game_mode
            init_session()
            st.session_state.game_mode = mode
            st.rerun()

    render_board()

    if st.session_state.winner:
        side = "红" if st.session_state.winner == "red" else "蓝"
        st.success(st.session_state.message or f"{side}方获胜！")
    elif st.session_state.is_draw:
        st.warning(st.session_state.message)

    if st.session_state.pending_ai and not st.session_state.winner and not st.session_state.is_draw:
        run_ai()
        st.rerun()


def main():
    st.set_page_config(
        page_title="象棋翻棋 4×8",
        page_icon="♟️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    if "page" not in st.session_state:
        st.session_state.page = "menu"

    if st.session_state.page == "menu":
        page_menu()
    else:
        page_game()


if __name__ == "__main__":
    main()
