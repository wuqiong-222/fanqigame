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
ALL_CHESS = [
    "将","士","象","马","车","炮","兵",
    "帅","仕","相","马","车","炮","卒"
] * 2

# 特殊吃子规则（小吃大）
SPECIAL_EAT = {"兵":["将","帅"], "卒":["将","帅"]}

ROWS = 4
COLS = 8

# ===================== 页面配置 =====================
st.set_page_config(
    page_title="4×8象棋翻棋",
    page_icon="🐘",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===================== 传统象棋样式CSS =====================
st.markdown("""
<style>
/* 整体容器 */
.main {
    max-width: 700px;
    margin: 0 auto;
    padding: 10px;
}

/* 棋盘网格 */
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

/* 棋子格子 - 圆形传统象棋风格 */
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

/* 暗棋（背面） */
.cell.dark {
    background: linear-gradient(145deg, #5a5a5a, #3a3a3a);
    color: #2c2c2c;
    box-shadow: inset 0 1px 3px rgba(255,255,255,0.2), 0 2px 4px rgba(0,0,0,0.3);
    font-size: 28px;
}

/* 红方棋子 */
.cell.red {
    background: radial-gradient(circle at 30% 30%, #e34234, #b22b1c);
    color: #ffd966;
    text-shadow: 1px 1px 0 #6b1a0f;
    border: 1px solid #ffaa77;
}

/* 蓝方（黑方）棋子 */
.cell.blue {
    background: radial-gradient(circle at 30% 30%, #3a6ea5, #1e3a5f);
    color: #e8e8e8;
    text-shadow: 1px 1px 0 #0f2a44;
    border: 1px solid #8ab3d0;
}

/* 空格 */
.cell.empty {
    background: #e8dbbd;
    box-shadow: inset 0 0 0 1px #c8aa6e, 0 1px 2px rgba(0,0,0,0.1);
}

/* 选中高亮 */
.cell.selected {
    box-shadow: 0 0 0 3px gold, 0 0 0 6px #ffaa33;
    transform: scale(0.98);
    z-index: 10;
}

/* 按钮样式 */
.stButton > button {
    font-size: 18px !important;
    padding: 12px 16px !important;
    border-radius: 30px !important;
    background: #4a6a3b !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}

.stButton > button:hover {
    background: #5e8048 !important;
}

/* 提示文字 */
.info-text {
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    padding: 10px;
    border-radius: 20px;
    margin: 10px 0;
}

/* 移动端适配 */
@media (max-width: 600px) {
    .cell {
        font-size: 20px;
    }
    .cell.dark {
        font-size: 22px;
    }
    .stButton > button {
        font-size: 16px !important;
        padding: 10px 12px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ===================== 工具函数 =====================
def get_neighbors(r, c):
    """获取相邻格子坐标"""
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    res = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            res.append((nr, nc))
    return res

def init_board():
    """初始化棋盘：所有棋子背面朝上，随机摆放"""
    chess_list = ALL_CHESS.copy()
    random.shuffle(chess_list)
    board = []
    idx = 0
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            row.append({
                "status": "dark",       # dark/open/empty
                "chess": chess_list[idx],
                "owner": None           # red / blue
            })
            idx += 1
        board.append(row)
    return board

def check_win(board):
    """检查胜利条件：将或帅被吃"""
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
    """平局：双方僵持超过10回合无进展"""
    return no_op_count >= 10

def reset_game():
    """重置游戏状态"""
    st.session_state.board = init_board()
    st.session_state.game_mode = None
    st.session_state.current_turn = None
    st.session_state.selected_pos = None
    st.session_state.just_opened = None   # 刚翻开的格子，本回合不能移动
    st.session_state.no_op_counter = 0
    st.session_state.game_over = False
    st.session_state.winner = None

# ===================== 核心游戏逻辑 =====================
def handle_click(r, c):
    """处理点击事件"""
    if st.session_state.game_over:
        return
    
    board = st.session_state.board
    current = st.session_state.current_turn
    selected = st.session_state.selected_pos
    just_opened = st.session_state.just_opened
    
    cell = board[r][c]
    
    # 如果点击的是刚翻开的格子，无效
    if (r, c) == just_opened:
        return
    
    # 情况1：没有选中任何棋子
    if selected is None:
        # 1.1 点击暗棋 → 翻开（确定颜色/阵营）
        if cell["status"] == "dark":
            # 如果当前还没有阵营（游戏刚开始）
            if current is None:
                # 翻开第一个棋子，决定玩家颜色
                owner = "red"
                if st.session_state.game_mode == "two_people":
                    st.session_state.current_turn = "blue"  # 红方翻完，轮到蓝方
                else:
                    st.session_state.current_turn = "ai"    # 人机模式，轮到AI（蓝方）
            else:
                # 已经有阵营了，翻开的棋子归当前玩家所有？
                # 规则：翻开的棋子颜色固定，但归当前回合玩家控制吗？
                # 根据传统翻棋，翻出来的棋子颜色固定红或蓝，自动归对应玩家控制
                owner = "red" if cell["chess"] in ["将","士","象","马","车","炮","兵"] else "blue"
            
            cell["status"] = "open"
            cell["owner"] = owner
            st.session_state.just_opened = (r, c)
            st.session_state.no_op_counter = 0
            st.session_state.selected_pos = None
            return
        
        # 1.2 点击已翻开的己方棋子 → 选中
        if cell["status"] == "open" and cell["owner"] == current:
            st.session_state.selected_pos = (r, c)
            return
        
        # 点击其他无效（空格、对方棋子）
        return
    
    # 情况2：已经选中了一个棋子，尝试移动/翻吃
    sr, sc = selected
    
    # 检查是否相邻
    if (r, c) not in get_neighbors(sr, sc):
        st.session_state.selected_pos = None
        return
    
    target = board[r][c]
    source = board[sr][sc]
    
    # 2.1 目标是暗棋 → 主动翻吃（核心规则）
    if target["status"] == "dark":
        # 翻开目标
        target_owner = "red" if target["chess"] in ["将","士","象","马","车","炮","兵"] else "blue"
        target["status"] = "open"
        target["owner"] = target_owner
        
        st.session_state.just_opened = (r, c)
        st.session_state.no_op_counter = 0
        
        # 判定吃子结果
        atk_chess = source["chess"]
        def_chess = target["chess"]
        
        # 特殊规则：兵/卒可吃将/帅
        if atk_chess in SPECIAL_EAT and def_chess in SPECIAL_EAT[atk_chess]:
            # 进攻方吃防守方，防守方消失，进攻方移动到目标位置
            board[r][c] = source.copy()
            board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        else:
            atk_w = CHESS_WEIGHT[atk_chess]
            def_w = CHESS_WEIGHT[def_chess]
            
            if atk_w > def_w:
                # 进攻方吃防守方，移动到目标位置
                board[r][c] = source.copy()
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
            elif atk_w == def_w:
                # 同级互吃，双方消失
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
                board[r][c] = {"status": "empty", "chess": None, "owner": None}
            else:
                # 进攻方被反吃，防守方占据进攻方位置，进攻方消失
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
                # 防守方已经在原位（翻开时已设置），不需要额外移动
        
        st.session_state.selected_pos = None
        return
    
    # 2.2 目标是空格 → 移动棋子
    if target["status"] == "empty":
        board[r][c] = source.copy()
        board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        st.session_state.selected_pos = None
        return
    
    # 2.3 目标是对方棋子（明棋）→ 不允许直接吃（按规则只能翻吃暗棋）
    # 清空选中
    st.session_state.selected_pos = None
    return

def switch_turn():
    """切换回合"""
    if st.session_state.game_mode == "two_people":
        # 双人对战：红蓝交替
        if st.session_state.current_turn == "red":
            st.session_state.current_turn = "blue"
        else:
            st.session_state.current_turn = "red"
    else:
        # 人机模式：玩家(red) 和 AI(blue) 交替
        if st.session_state.current_turn == "red":
            st.session_state.current_turn = "ai"
        else:
            st.session_state.current_turn = "red"
    
    st.session_state.just_opened = None
    st.session_state.selected_pos = None
    st.session_state.no_op_counter += 1

# ===================== AI逻辑 =====================
def ai_move():
    """AI走棋（简单优先级：翻暗棋 > 吃子 > 移动）"""
    if st.session_state.game_over:
        return
    if st.session_state.current_turn != "ai":
        return
    
    board = st.session_state.board
    
    # 收集所有AI棋子位置
    ai_pieces = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]["status"] == "open" and board[r][c]["owner"] == "blue":
                ai_pieces.append((r, c))
    
    # 收集所有暗棋位置
    dark_positions = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]["status"] == "dark":
                dark_positions.append((r, c))
    
    # 优先级1：用AI棋子翻吃相邻的暗棋
    for sr, sc in ai_pieces:
        for nr, nc in get_neighbors(sr, sc):
            if board[nr][nc]["status"] == "dark" and (nr, nc) != st.session_state.just_opened:
                handle_click(sr, sc)
                handle_click(nr, nc)
                switch_turn()
                return
    
    # 优先级2：翻任意暗棋
    if dark_positions:
        r, c = random.choice(dark_positions)
        handle_click(r, c)
        switch_turn()
        return
    
    # 优先级3：移动AI棋子到空格
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

# ===================== UI界面 =====================
st.title("🐘 4×8 象棋翻棋")

# 模式选择（仅在未开始时显示）
if st.session_state.game_mode is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 双人对战", use_container_width=True):
            reset_game()
            st.session_state.game_mode = "two_people"
            st.session_state.current_turn = "red"
    with col2:
        if st.button("🤖 人机对战", use_container_width=True):
            reset_game()
            st.session_state.game_mode = "ai_mode"
            st.session_state.current_turn = "red"
    st.rerun()
else:
    # 重置按钮
    if st.button("🔄 重新开局", use_container_width=True):
        reset_game()
        st.rerun()
    
    # 游戏状态提示
    if not st.session_state.game_over:
        turn = st.session_state.current_turn
        if turn == "red":
            st.info("🔴 红方回合")
        elif turn == "blue":
            st.info("🔵 蓝方回合")
        elif turn == "ai":
            st.warning("🤖 AI思考中...")
    
    # 绘制棋盘
    board = st.session_state.board
    
    # 用HTML渲染棋盘
    board_html = '<div class="chess-board">'
    for r in range(ROWS):
        for c in range(COLS):
            cell = board[r][c]
            css_class = "cell"
            text = ""
            
            if cell["status"] == "dark":
                css_class += " dark"
                text = "?"  # 背面显示？或●
            elif cell["status"] == "empty":
                css_class += " empty"
                text = ""
            else:
                css_class += " red" if cell["owner"] == "red" else " blue"
                text = cell["chess"]
            
            if st.session_state.selected_pos == (r, c):
                css_class += " selected"
            
            board_html += f'<button class="{css_class}" onclick="parent.postMessage({{type: "chess_click", row: {r}, col: {c}}}, "*")">{text}</button>'
    board_html += '</div>'
    
    st.components.v1.html(board_html, height=450, scrolling=False)
    
    # 处理点击的JavaScript回调
    click_data = st.session_state.get("click_data", None)
    if click_data:
        r, c = click_data
        handle_click(r, c)
        # 检查胜负
        winner = check_win(board)
        if winner:
            st.session_state.game_over = True
            st.session_state.winner = "红方胜利！" if winner == "red" else "蓝方胜利！"
        elif check_draw(st.session_state.no_op_counter):
            st.session_state.game_over = True
            st.session_state.winner = "平局！"
        else:
            switch_turn()
        st.session_state.click_data = None
        st.rerun()
    
    # 人机模式AI自动走棋
    if st.session_state.game_mode == "ai_mode" and not st.session_state.game_over and st.session_state.current_turn == "ai":
        ai_move()
        # 再次检查胜负
        winner = check_win(board)
        if winner:
            st.session_state.game_over = True
            st.session_state.winner = "红方胜利！" if winner == "red" else "蓝方胜利！"
        elif check_draw(st.session_state.no_op_counter):
            st.session_state.game_over = True
            st.session_state.winner = "平局！"
        st.rerun()
    
    # 显示游戏结束信息
    if st.session_state.game_over:
        st.success(f"🏆 {st.session_state.winner}")
        if st.button("🎮 新的一局"):
            reset_game()
            st.rerun()
