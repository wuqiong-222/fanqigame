import base64
import random
import streamlit as st

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

STALE_LIMIT = 10

def build_piece_pool():
    red = ["将"] + ["士"] * 2 + ["象"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["兵"] * 5
    black = ["帅"] + ["仕"] * 2 + ["相"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["卒"] * 5
    pool = [(n, "red") for n in red] + [(n, "black") for n in black]
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
    st.session_state.selected = None
    st.session_state.turn = None
    st.session_state.red_holder = None
    st.session_state.black_holder = None
    st.session_state.message = "玩家一：32 枚棋子已随机暗摆，请翻开一枚确定红/黑阵营"
    st.session_state.winner = None
    st.session_state.is_draw = False
    st.session_state.stale_turns = 0
    st.session_state.pending_ai = False
    st.session_state.run_ai_step = False
    st.session_state.last_capture_general = None

def reset_to_menu():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.page = "menu"

def holders():
    return st.session_state.red_holder, st.session_state.black_holder

def camp_of_turn():
    return st.session_state.turn

def human_camp():
    rh, bh = holders()
    if rh == "human":
        return "red"
    if bh == "human":
        return "black"
    return None

def player_label(camp):
    rh, bh = holders()
    if camp == "red":
        return "玩家一" if rh == "p1" else "玩家二"
    return "玩家一" if bh == "p1" else "玩家二"

def is_human_turn():
    mode = st.session_state.game_mode
    if mode == "pvp":
        return True
    turn = st.session_state.turn
    if turn is None:
        return True
    rh, bh = holders()
    return (turn == "red" and rh == "human") or (turn == "black" and bh == "human")

def assign_colors_on_first_flip(camp):
    mode = st.session_state.game_mode
    if camp == "red":
        st.session_state.red_holder = "human" if mode == "pvai" else "p1"
        st.session_state.black_holder = "ai" if mode == "pvai" else "p2"
    else:
        st.session_state.black_holder = "human" if mode == "pvai" else "p1"
        st.session_state.red_holder = "ai" if mode == "pvai" else "p2"
    st.session_state.turn = camp

def switch_turn():
    st.session_state.turn = "black" if st.session_state.turn == "red" else "red"
    st.session_state.selected = None

def cell_at(r, c):
    return st.session_state.board[r][c]

def can_jump_attack(r1, c1, r2, c2):
    if (r1, c1) == (r2, c2):
        return False
    return r1 == r2 or c1 == c2

def compare_strength(attacker, defender):
    wa, wd = CHESS_WEIGHT[attacker], CHESS_WEIGHT[defender]
    if wa > wd:
        return "win"
    if wa == wd:
        return "tie"
    return "lose"

def count_pieces(camp):
    return sum(
        1
        for r in range(ROWS)
        for c in range(COLS)
        if st.session_state.board[r][c]["status"] != "empty"
        and st.session_state.board[r][c]["camp"] == camp
    )

def general_alive(camp):
    target = "将" if camp == "red" else "帅"
    return any(
        st.session_state.board[r][c]["status"] != "empty"
        and st.session_state.board[r][c]["chess"] == target
        for r in range(ROWS)
        for c in range(COLS)
    )

def check_end_after_action():
    captured = st.session_state.get("last_capture_general")
    if captured:
        loser = "black" if captured == "将" else "red"
        winner = "red" if loser == "black" else "black"
        st.session_state.winner = winner
        if st.session_state.game_mode == "pvp":
            st.session_state.message = f"{player_label(winner)}（{'红' if winner == 'red' else '黑'}方）获胜！"
        else:
            rh, bh = holders()
            human_won = (winner == "red" and rh == "human") or (winner == "black" and bh == "human")
            st.session_state.message = "恭喜你获胜！" if human_won else "AI 获胜！"
        return

    if not general_alive("red"):
        st.session_state.winner = "black"
        st.session_state.message = "黑方获胜！"
        return
    if not general_alive("black"):
        st.session_state.winner = "red"
        st.session_state.message = "红方获胜！"
        return

    if count_pieces("red") == 1 and count_pieces("black") == 1 and st.session_state.stale_turns >= STALE_LIMIT:
        st.session_state.is_draw = True
        st.session_state.message = f"平局！连续 {STALE_LIMIT} 回合无吃子且无翻新。"

def finish_action(flipped_new=False, captured=False):
    if captured or flipped_new:
        st.session_state.stale_turns = 0
    else:
        st.session_state.stale_turns += 1

    check_end_after_action()
    st.session_state.last_capture_general = None
    st.session_state.selected = None

    if st.session_state.winner or st.session_state.is_draw:
        return

    switch_turn()
    if st.session_state.game_mode == "pvai" and not is_human_turn():
        st.session_state.pending_ai = True

def resolve_battle(attacker_cell, attacker_pos, defender_cell, defender_pos):
    board = st.session_state.board
    ar, ac = attacker_pos
    dr, dc = defender_pos
    result = compare_strength(attacker_cell["chess"], defender_cell["chess"])
    captured_general = None

    if result == "win":
        if defender_cell["chess"] in ("将", "帅"):
            captured_general = defender_cell["chess"]
        board[dr][dc] = {**attacker_cell, "status": "open"}
        board[ar][ac] = empty_cell()
        st.session_state.message = f"{attacker_cell['chess']} 吃掉 {defender_cell['chess']}！"
    elif result == "tie":
        if defender_cell["chess"] in ("将", "帅"):
            captured_general = defender_cell["chess"]
        if attacker_cell["chess"] in ("将", "帅"):
            captured_general = attacker_cell["chess"]
        board[dr][dc] = empty_cell()
        board[ar][ac] = empty_cell()
        st.session_state.message = f"{attacker_cell['chess']} 与 {defender_cell['chess']} 同归于尽！"
    else:
        if attacker_cell["chess"] in ("将", "帅"):
            captured_general = attacker_cell["chess"]
        board[dr][dc] = {**defender_cell, "status": "open"}
        board[ar][ac] = empty_cell()
        st.session_state.message = f"{defender_cell['chess']} 反吃 {attacker_cell['chess']}！"

    st.session_state.last_capture_general = captured_general
    return captured_general is not None

def do_simple_flip(r, c):
    cell = cell_at(r, c)
    if cell["status"] != "dark":
        return False

    cell["status"] = "open"

    if st.session_state.turn is None:
        assign_colors_on_first_flip(cell["camp"])
        side = "红" if cell["camp"] == "red" else "黑"
        if st.session_state.game_mode == "pvai":
            st.session_state.message = f"你执{side}方。首翻 {cell['chess']}，轮到对方。"
        else:
            st.session_state.message = f"玩家一执{side}方。首翻 {cell['chess']}，轮到玩家二。"
        finish_action(flipped_new=True)
        return True

    st.session_state.message = f"翻开 {cell['chess']}，留在原地。"
    finish_action(flipped_new=True)
    return True

def do_dark_eat_open(dr, dc, tr, tc):
    board = st.session_state.board
    dark, tgt = board[dr][dc], board[tr][tc]
    player = camp_of_turn()

    if dark["status"] != "dark" or tgt["status"] != "open":
        return False
    if tgt["camp"] == player or not can_jump_attack(dr, dc, tr, tc):
        return False
    if dark["camp"] != player:
        st.session_state.message = "只能用己方暗棋吃对方明棋。"
        return False

    dark["status"] = "open"
    captured = resolve_battle({**dark}, (dr, dc), tgt, (tr, tc))
    finish_action(flipped_new=True, captured=captured)
    return True

def do_open_eat_dark(fr, fc, tr, tc):
    board = st.session_state.board
    src, dark = board[fr][fc], board[tr][tc]
    player = camp_of_turn()

    if src["status"] != "open" or dark["status"] != "dark":
        return False
    if src["camp"] != player or not can_jump_attack(fr, fc, tr, tc):
        return False

    if dark["camp"] == player:
        dark["status"] = "open"
        st.session_state.message = f"翻开己方 {dark['chess']}，留在原地。"
        finish_action(flipped_new=True)
        return True

    dark["status"] = "open"
    captured = resolve_battle({**src}, (fr, fc), dark, (tr, tc))
    finish_action(flipped_new=True, captured=captured)
    return True

def do_open_eat_open(fr, fc, tr, tc):
    board = st.session_state.board
    src, tgt = board[fr][fc], board[tr][tc]
    player = camp_of_turn()

    if src["status"] != "open" or tgt["status"] != "open":
        return False
    if src["camp"] != player or tgt["camp"] == player:
        return False
    if not can_jump_attack(fr, fc, tr, tc):
        return False

    captured = resolve_battle({**src}, (fr, fc), tgt, (tr, tc))
    finish_action(captured=captured)
    return True

def handle_cell_click(r, c):
    if st.session_state.winner or st.session_state.is_draw:
        return
    if not is_human_turn() and st.session_state.game_mode == "pvai":
        return

    cell = cell_at(r, c)
    player = camp_of_turn()
    sel = st.session_state.selected

    if player is None:
        if cell["status"] == "dark":
            do_simple_flip(r, c)
        return

    if sel is None:
        if cell["status"] == "dark":
            do_simple_flip(r, c)
        elif cell["status"] == "open" and cell["camp"] == player:
            st.session_state.selected = (r, c)
            st.session_state.message = f"已选 {cell['chess']}，请点同行/同列的暗棋或敌明棋（跳吃）。"
        elif cell["status"] == "open" and cell["camp"] != player:
            st.session_state.selected = (r, c)
            st.session_state.message = f"已选对方 {cell['chess']}，请点同行/同列的己方暗棋（跳吃）。"
        return

    sr, sc = sel
    if (r, c) == sel:
        st.session_state.selected = None
        st.session_state.message = "已取消选择。"
        return

    src = cell_at(sr, sc)

    if src["status"] == "open" and src["camp"] == player:
        if do_open_eat_dark(sr, sc, r, c):
            return
        if do_open_eat_open(sr, sc, r, c):
            return
        if cell["status"] == "open" and cell["camp"] == player:
            st.session_state.selected = (r, c)
            st.session_state.message = f"改选 {cell['chess']}。"
            return
        st.session_state.message = "请点同行/同列的暗棋或敌明棋（跳吃）。"
        return

    if src["status"] == "open" and src["camp"] != player:
        if do_dark_eat_open(r, c, sr, sc):
            return
        st.session_state.message = "请点同行/同列的己方暗棋（跳吃）。"
        return

def ai_camp():
    rh, bh = holders()
    return "black" if bh == "ai" else "red"

def run_ai():
    if st.session_state.winner or st.session_state.is_draw:
        st.session_state.pending_ai = False
        return

    camp = ai_camp()
    board = st.session_state.board
    best = []

    for r in range(ROWS):
        for c in range(COLS):
            src = board[r][c]
            if src["status"] != "open" or src["camp"] != camp:
                continue
            for tr in range(ROWS):
                for tc in range(COLS):
                    if not can_jump_attack(r, c, tr, tc):
                        continue
                    tgt = board[tr][tc]
                    if tgt["status"] == "dark":
                        res = compare_strength(src["chess"], tgt["chess"])
                        score = 3 if res == "win" else (1 if res == "tie" else 0)
                        best.append((score, r, c, tr, tc, "open_dark"))
                    elif tgt["status"] == "open" and tgt["camp"] != camp:
                        res = compare_strength(src["chess"], tgt["chess"])
                        score = 3 if res == "win" else (1 if res == "tie" else 0)
                        best.append((score, r, c, tr, tc, "open_open"))

    for r in range(ROWS):
        for c in range(COLS):
            dark = board[r][c]
            if dark["status"] != "dark" or dark["camp"] != camp:
                continue
            for tr in range(ROWS):
                for tc in range(COLS):
                    tgt = board[tr][tc]
                    if tgt["status"] != "open" or tgt["camp"] == camp:
                        continue
                    if not can_jump_attack(r, c, tr, tc):
                        continue
                    res = compare_strength(dark["chess"], tgt["chess"])
                    score = 3 if res == "win" else (1 if res == "tie" else 0)
                    best.append((score, r, c, tr, tc, "dark_open"))

    if best:
        best.sort(key=lambda x: -x[0])
        _, r, c, tr, tc, kind = best[0]
        if kind == "open_dark":
            do_open_eat_dark(r, c, tr, tc)
        elif kind == "open_open":
            do_open_eat_open(r, c, tr, tc)
        else:
            do_dark_eat_open(r, c, tr, tc)
    else:
        darks = [(r, c) for r in range(ROWS) for c in range(COLS) if board[r][c]["status"] == "dark"]
        if darks:
            r, c = random.choice(darks)
            do_simple_flip(r, c)

    st.session_state.pending_ai = False

def piece_svg_img(cell, selected=False):
    ring = (
        '<circle cx="50" cy="50" r="48" fill="none" stroke="#ffd700" stroke-width="5"/>'
        if selected
        else ""
    )

    if cell["status"] == "empty":
        body = (
            '<circle cx="50" cy="50" r="44" fill="rgba(255,248,220,0.15)" '
            'stroke="#8b6914" stroke-width="2" stroke-dasharray="6,4"/>'
        )
    elif cell["status"] == "dark":
        body = (
            '<circle cx="50" cy="50" r="44" fill="#3d2518" stroke="#2c1810" stroke-width="3"/>'
            '<text x="50" y="62" text-anchor="middle" font-size="38" font-weight="bold" '
            'fill="#c9a66b" font-family="SimSun, serif">?</text>'
        )
    elif cell["camp"] == "red":
        ch = cell["chess"]
        body = (
            '<circle cx="50" cy="50" r="44" fill="#ffe0e0" stroke="#b71c1c" stroke-width="4"/>'
            f'<text x="50" y="64" text-anchor="middle" font-size="48" font-weight="bold" '
            f'fill="#d50000" font-family="SimSun, KaiTi, serif">{ch}</text>'
        )
    else:
        ch = cell["chess"]
        body = (
            '<circle cx="50" cy="50" r="44" fill="#e8e8e8" stroke="#000000" stroke-width="4"/>'
            f'<text x="50" y="64" text-anchor="middle" font-size="48" font-weight="bold" '
            f'fill="#000000" font-family="SimSun, KaiTi, serif">{ch}</text>'
        )

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{ring}{body}</svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img class="piece-img" src="data:image/svg+xml;base64,{b64}" alt=""/>'

def inject_css():
    st.markdown(
        """
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
        html, body {
            overflow: hidden !important;
            touch-action: manipulation !important;
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.3rem !important;
            padding-right: 0.3rem !important;
            max-width: 100vw !important;
            width: 100vw !important;
        }
        h1 {
            margin: 0.2rem 0 !important;
            font-size: clamp(1.1rem, 4vw, 1.6rem) !important;
            text-align: center !important;
        }
        .status-bar {
            text-align: center;
            padding: 0.3rem;
            margin: 0.2rem auto;
            background: #f5e6c8;
            border: 2px solid #8b6914;
            border-radius: 8px;
            font-size: clamp(0.7rem, 3vw, 0.95rem);
        }
        /* 横屏自动放大棋盘 */
        .board-frame {
            width: 98vw !important;
            max-width: min(90vh, 98vw) !important;
            margin: 0 auto !important;
            padding: 4px !important;
            background: #4a2810;
            border-radius: 8px;
        }
        .piece-img {
            width: 100% !important;
            height: auto !important;
            object-fit: contain !important;
            display: block !important;
            aspect-ratio: 1/1 !important;
        }
        div[data-testid="column"] {
            padding: 0.5px !important;
            min-width: 0 !important;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0px !important;
        }
        .cell-box {
            background: rgba(255,248,220,0.12);
            border: 1px solid rgba(92,58,18,0.3);
            border-radius: 4px;
            padding: 1px;
        }
        .cell-box div.stButton > button {
            padding: 0px !important;
            height: 20px !important;
            font-size: 0px !important;
            border-radius: 4px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_legend():
    st.markdown("""
        <div style="text-align:center; font-size:11px; margin:2px 0;">
        手机横屏体验更佳｜同行同列跳吃
        </div>
    """, unsafe_allow_html=True)

def render_board():
    board = st.session_state.board
    frozen = bool(st.session_state.winner or st.session_state.is_draw)
    disabled = frozen or (st.session_state.game_mode == "pvai" and not is_human_turn())

    st.markdown('<div style="background:linear-gradient(160deg,#dcb35c,#b8842f);padding:3px;border:2px solid #5c3a12;">', unsafe_allow_html=True)
    for r in range(ROWS):
        cols = st.columns(COLS, gap="small")
        for c in range(COLS):
            cell = board[r][c]
            selected = st.session_state.selected == (r, c)
            with cols[c]:
                st.markdown('<div class="cell-box">', unsafe_allow_html=True)
                st.markdown(piece_svg_img(cell, selected), unsafe_allow_html=True)
                st.button("", key=f"cell_{r}_{c}", on_click=handle_cell_click, args=(r, c), disabled=disabled, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def turn_hint():
    if st.session_state.winner or st.session_state.is_draw:
        return st.session_state.message
    if st.session_state.turn is None:
        return "【玩家一】请翻棋定阵营"
    side = "红" if st.session_state.turn == "red" else "黑"
    if st.session_state.game_mode == "pvp":
        who = player_label(st.session_state.turn)
        return f"当前回合：{who}（{side}方）"
    if is_human_turn():
        my = "红" if human_camp() == "red" else "黑"
        return f"你的回合（执{my}方）"
    return "AI 回合"

def page_menu():
    st.title("象棋翻棋")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("双人对战", use_container_width=True, type="primary"):
            st.session_state.game_mode = "pvp"
            init_session()
            st.rerun()
        if st.button("人机对战", use_container_width=True):
            st.session_state.game_mode = "pvai"
            init_session()
            st.rerun()

def page_game():
    st.title("象棋翻棋")
    st.markdown(f'<div class="status-bar"><b>{turn_hint()}</b><br>{st.session_state.message}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
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

    render_legend()
    st.markdown('<div class="board-frame">', unsafe_allow_html=True)
    render_board()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.winner:
        st.success(st.session_state.message)
    elif st.session_state.is_draw:
        st.warning(st.session_state.message)

    if st.session_state.run_ai_step:
        st.session_state.run_ai_step = False
        run_ai()
        st.rerun()
    elif st.session_state.pending_ai and not st.session_state.winner and not st.session_state.is_draw:
        st.session_state.run_ai_step = True
        st.rerun()

def main():
    st.set_page_config(
        page_title="象棋翻棋",
        page_icon="♟️",
        layout="wide",
        initial_sidebar_state="collapsed"
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
