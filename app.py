import streamlit as st
import random

# ===================== 全局常量配置 =====================
CHESS_WEIGHT = {
    "将": 9, "帅": 9,
    "士": 8, "仕": 8,
    "象": 7, "相": 7,
    "马": 6,
    "车": 5,
    "炮": 4,
    "兵": 3, "卒": 3
}

# 所有棋子（32个）
ALL_CHESS = (
    ["将"] * 1 + ["士"] * 2 + ["象"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["兵"] * 5 +
    ["帅"] * 1 + ["仕"] * 2 + ["相"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["卒"] * 5
)
SPECIAL_EAT = {"兵": ["将", "帅"], "卒": ["将", "帅"]}

ROWS = 4
COLS = 8

# ===================== 页面配置 =====================
st.set_page_config(
    page_title="4×8象棋翻棋",
    page_icon="🐘",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===================== 样式 =====================
st.markdown("""
<style>
.main {max-width: 700px; margin: 0 auto; padding: 10px;}
.chess-board {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 4px;
    background-color: #d4b87a;
    padding: 12px;
    border-radius: 12px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    margin: 15px 0;
}
.cell {
    aspect-ratio: 1 / 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    font-weight: bold;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.1s ease;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    font-family: "KaiTi", "华文楷书", "Microsoft YaHei", serif;
}
.cell.dark {background: linear-gradient(145deg, #5a5a5a, #3a3a3a); color: #2c2c2c; font-size: 28px;}
.cell.red {background: radial-gradient(circle at 30% 30%, #e34234, #b22b1c); color: #ffd966;}
.cell.blue {background: radial-gradient(circle at 30% 30%, #3a6ea5, #1e3a5f); color: #e8e8e8;}
.cell.empty {background: #e8dbbd;}
.cell.selected {box-shadow: 0 0 0 3px gold; transform: scale(0.98);}
@media (max-width: 600px) {
    .cell {font-size: 20px;}
    .cell.dark {font-size: 22px;}
}
</style>
""", unsafe_allow_html=True)

# ===================== 工具函数 =====================
def get_neighbors(r, c):
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    res = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            res.append((nr, nc))
    return res

def init_board():
    chess_list = ALL_CHESS.copy()
    random.shuffle(chess_list)
    board = []
    idx = 0
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            row.append({
                "status": "dark",
                "chess": chess_list[idx],
                "owner": None
            })
            idx += 1
        board.append(row)
    return board

def check_win(board):
    has_red_general = False
    has_blue_general = False
    for r in range(ROWS):
        for c in range(COLS):
            cell = board[r][c]
            if cell["status"] == "open":
                if cell["owner"] == "red" and cell["chess"] == "将":
                    has_red_general = True
                if cell["owner"] == "blue" and cell["chess"] == "帅":
                    has_blue_general = True
    if not has_red_general:
        return "blue"
    if not has_blue_general:
        return "red"
    return None

def check_draw(no_op_count):
    return no_op_count >= 10

def reset_game():
    st.session_state.board = init_board()
    st.session_state.game_mode = None
    st.session_state.current_turn = None
    st.session_state.selected_pos = None
    st.session_state.just_opened = None
    st.session_state.no_op_counter = 0
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.clicked_cell = None  # 新增：记录点击的格子坐标

# ===================== 核心游戏逻辑 =====================
def handle_click(r, c):
    if st.session_state.game_over:
        return False
    board = st.session_state.board
    current = st.session_state.current_turn
    selected = st.session_state.selected_pos
    just_opened = st.session_state.just_opened
    cell = board[r][c]

    if (r, c) == just_opened:
        return False

    if selected is None:
        if cell["status"] == "dark":
            is_red = cell["chess"] in ["将","士","象","马","车","炮","兵"]
            owner = "red" if is_red else "blue"
            if current is None:
                if st.session_state.game_mode == "two_people":
                    st.session_state.current_turn = "blue" if owner == "red" else "red"
                else:
                    st.session_state.current_turn = "ai" if owner == "red" else "red"
            cell["status"] = "open"
            cell["owner"] = owner
            st.session_state.just_opened = (r, c)
            st.session_state.no_op_counter = 0
            return True
        if cell["status"] == "open" and cell["owner"] == current:
            st.session_state.selected_pos = (r, c)
            return True
        return False

    sr, sc = selected
    if (r, c) not in get_neighbors(sr, sc):
        st.session_state.selected_pos = None
        return False

    target = board[r][c]
    source = board[sr][sc]

    if target["status"] == "dark":
        is_red_target = target["chess"] in ["将","士","象","马","车","炮","兵"]
        target_owner = "red" if is_red_target else "blue"
        target["status"] = "open"
        target["owner"] = target_owner
        st.session_state.just_opened = (r, c)
        st.session_state.no_op_counter = 0
        atk_chess = source["chess"]
        def_chess = target["chess"]
        if atk_chess in SPECIAL_EAT and def_chess in SPECIAL_EAT[atk_chess]:
            board[r][c] = source.copy()
            board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        else:
            atk_w = CHESS_WEIGHT.get(atk_chess, 0)
            def_w = CHESS_WEIGHT.get(def_chess, 0)
            if atk_w > def_w:
                board[r][c] = source.copy()
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
            elif atk_w == def_w:
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
                board[r][c] = {"status": "empty", "chess": None, "owner": None}
            else:
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        st.session_state.selected_pos = None
        return True

    if target["status"] == "empty":
        board[r][c] = source.copy()
        board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        st.session_state.selected_pos = None
        return True

    st.session_state.selected_pos = None
    return False

def switch_turn():
    if st.session_state.game_mode == "two_people":
        st.session_state.current_turn = "blue" if st.session_state.current_turn == "red" else "red"
    else:
        st.session_state.current_turn = "ai" if st.session_state.current_turn == "red" else "red"
    st.session_state.just_opened = None
    st.session_state.selected_pos = None
    st.session_state.no_op_counter += 1

# ===================== AI逻辑 =====================
def ai_move():
    if st.session_state.game_over or st.session_state.current_turn != "ai":
        return
    board = st.session_state.board
    ai_pieces = [(r,c) for r in range(ROWS) for c in range(COLS) if board[r][c]["status"] == "open" and board[r][c]["owner"] == "blue"]
    dark_positions = [(r,c) for r in range(ROWS) for c in range(COLS) if board[r][c]["status"] == "dark"]
    for sr, sc in ai_pieces:
        for nr, nc in get_neighbors(sr, sc):
            if board[nr][nc]["status"] == "dark" and (nr, nc) != st.session_state.just_opened:
                handle_click(sr, sc)
                handle_click(nr, nc)
                switch_turn()
                return
    if dark_positions:
        r, c = random.choice(dark_positions)
        handle_click(r, c)
        switch_turn()
        return
    for sr, sc in ai_pieces:
        for nr, nc in get_neighbors(sr, sc):
            if board[nr][nc]["status"] == "empty":
                handle_click(sr, sc)
                handle_click(nr, nc)
                switch_turn()
                return
    switch_turn()

# ===================== 会话状态初始化 =====================
if "board" not in st.session_state:
    reset_game()

# ===================== 处理点击事件（关键修复） =====================
if st.session_state.clicked_cell is not None:
    r, c = st.session_state.clicked_cell
    action_success = handle_click(r, c)
    if action_success:
        winner = check_win(st.session_state.board)
        if winner:
            st.session_state.game_over = True
            st.session_state.winner = "红方胜利！" if winner == "red" else "蓝方胜利！"
        elif check_draw(st.session_state.no_op_counter):
            st.session_state.game_over = True
            st.session_state.winner = "平局！"
        else:
            switch_turn()
    st.session_state.clicked_cell = None
    st.rerun()

# ===================== UI界面 =====================
st.title("🐘 4×8 象棋翻棋")

if st.session_state.game_mode is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 双人对战", use_container_width=True):
            reset_game()
            st.session_state.game_mode = "two_people"
            st.session_state.current_turn = "red"
            st.rerun()
    with col2:
        if st.button("🤖 人机对战", use_container_width=True):
            reset_game()
            st.session_state.game_mode = "ai_mode"
            st.session_state.current_turn = "red"
            st.rerun()
else:
    if st.button("🔄 重新开局", use_container_width=True):
        reset_game()
        st.rerun()
    if not st.session_state.game_over:
        turn = st.session_state.current_turn
        if turn == "red":
            st.info("🔴 红方回合")
        elif turn == "blue":
            st.info("🔵 蓝方回合")
        elif turn == "ai":
            st.warning("🤖 AI思考中...")

    # 渲染棋盘（关键修复：点击事件通过状态变量传递）
    board_html = '<div class="chess-board">'
    for r in range(ROWS):
        for c in range(COLS):
            cell = st.session_state.board[r][c]
            cls = "cell"
            text = ""
            if cell["status"] == "dark":
                cls += " dark"
                text = "?"
            elif cell["status"] == "empty":
                cls += " empty"
                text = ""
            else:
                if cell["owner"] == "red":
                    cls += " red"
                else:
                    cls += " blue"
                text = cell["chess"]
            if st.session_state.selected_pos == (r, c):
                cls += " selected"
            # 点击事件通过JS传递到状态变量
            board_html += f'''
            <div class="{cls}" onclick="document.getElementById('click_btn_{r}_{c}').click()">
                {text}
            </div>
            '''
    board_html += '</div>'
    st.markdown(board_html, unsafe_allow_html=True)

    # 隐藏的按钮，用于接收点击事件
    for r in range(ROWS):
        for c in range(COLS):
            if st.button("", key=f"click_btn_{r}_{c}", use_container_width=True):
                st.session_state.clicked_cell = (r, c)
                st.rerun()

    # 人机模式AI自动走棋
    if st.session_state.game_mode == "ai_mode" and not st.session_state.game_over and st.session_state.current_turn == "ai":
        ai_move()
        st.rerun()

    if st.session_state.game_over:
        st.success(f"🏆 {st.session_state.winner}")
        if st.button("🎮 新的一局"):
            reset_game()
            st.rerun()
