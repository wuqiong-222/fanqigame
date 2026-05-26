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

# 特殊吃子规则（小吃大）
SPECIAL_EAT = {"兵": ["将", "帅"], "卒": ["将", "帅"]}

# 所有棋子（32个）- 正确生成
ALL_CHESS = (
    ["将"] + ["士"] * 2 + ["象"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["兵"] * 5 +
    ["帅"] + ["仕"] * 2 + ["相"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["卒"] * 5
)

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
/* 棋盘容器 */
.board-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 10px;
}

/* 按钮样式 - 圆形棋子 */
.stButton > button {
    aspect-ratio: 1 / 1;
    font-size: 24px;
    font-weight: bold;
    border-radius: 50%;
    padding: 0;
    margin: 2px;
    width: 100%;
    font-family: "KaiTi", "华文楷书", "Microsoft YaHei", serif;
    transition: all 0.1s ease;
}

/* 红方棋子 */
.red-btn .stButton > button {
    background: linear-gradient(145deg, #e34234, #b22b1c);
    color: #ffd966;
    border: 2px solid #ffaa77;
}

/* 蓝方棋子 */
.blue-btn .stButton > button {
    background: linear-gradient(145deg, #3a6ea5, #1e3a5f);
    color: #e8e8e8;
    border: 2px solid #8ab3d0;
}

/* 暗棋 */
.dark-btn .stButton > button {
    background: linear-gradient(145deg, #5a5a5a, #3a3a3a);
    color: white;
    border: 1px solid #666;
    font-size: 20px;
}

/* 空格 */
.empty-btn .stButton > button {
    background: #e8dbbd;
    color: #e8dbbd;
    border: 1px solid #c8aa6e;
    box-shadow: inset 0 0 0 1px #c8aa6e;
}

/* 选中高亮 */
.selected .stButton > button {
    box-shadow: 0 0 0 3px gold, 0 0 0 6px #ffaa33;
    transform: scale(0.98);
}

/* 移动端适配 */
@media (max-width: 600px) {
    .stButton > button {
        font-size: 18px;
    }
    .dark-btn .stButton > button {
        font-size: 16px;
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
    """初始化棋盘"""
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
    """检查胜利"""
    has_red = False
    has_blue = False
    for r in range(ROWS):
        for c in range(COLS):
            cell = board[r][c]
            if cell["status"] == "open":
                if cell["owner"] == "red" and cell["chess"] == "将":
                    has_red = True
                if cell["owner"] == "blue" and cell["chess"] == "帅":
                    has_blue = True
    if not has_red:
        return "blue"
    if not has_blue:
        return "red"
    return None

def reset_game_state():
    """重置游戏"""
    st.session_state.board = init_board()
    st.session_state.game_mode = None
    st.session_state.current_turn = None
    st.session_state.selected = None
    st.session_state.just_opened = None
    st.session_state.no_op = 0
    st.session_state.game_over = False
    st.session_state.winner = None

# ===================== 核心游戏逻辑 =====================
def process_click(r, c):
    """处理点击 - 这个函数会在每次按钮点击时调用"""
    if st.session_state.game_over:
        return
    
    board = st.session_state.board
    current = st.session_state.current_turn
    selected = st.session_state.selected
    just_opened = st.session_state.just_opened
    
    cell = board[r][c]
    
    # 不能点击刚翻开的棋子
    if (r, c) == just_opened:
        return
    
    # 情况1：没有选中任何棋子
    if selected is None:
        # 点击暗棋
        if cell["status"] == "dark":
            # 判断颜色
            is_red = cell["chess"] in ["将","士","象","马","车","炮","兵"]
            owner = "red" if is_red else "blue"
            
            # 如果是第一步，设置当前玩家
            if current is None:
                if st.session_state.game_mode == "two_people":
                    st.session_state.current_turn = "blue" if owner == "red" else "red"
                else:
                    st.session_state.current_turn = "ai" if owner == "red" else "red"
            
            cell["status"] = "open"
            cell["owner"] = owner
            st.session_state.just_opened = (r, c)
            st.session_state.no_op = 0
            return
        
        # 点击己方明棋
        if cell["status"] == "open" and cell["owner"] == current:
            st.session_state.selected = (r, c)
            return
        
        return
    
    # 情况2：已选中棋子
    sr, sc = selected
    source = board[sr][sc]
    target = board[r][c]
    
    # 检查是否相邻
    if (r, c) not in get_neighbors(sr, sc):
        st.session_state.selected = None
        return
    
    # 目标是暗棋（主动翻吃）
    if target["status"] == "dark":
        # 翻开目标
        is_red_target = target["chess"] in ["将","士","象","马","车","炮","兵"]
        target_owner = "red" if is_red_target else "blue"
        target["status"] = "open"
        target["owner"] = target_owner
        st.session_state.just_opened = (r, c)
        st.session_state.no_op = 0
        
        # 判定大小
        atk = source["chess"]
        defend = target["chess"]
        
        # 兵/卒特殊规则
        if atk in SPECIAL_EAT and defend in SPECIAL_EAT[atk]:
            # 吃将/帅
            board[r][c] = source.copy()
            board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        else:
            atk_w = CHESS_WEIGHT.get(atk, 0)
            def_w = CHESS_WEIGHT.get(defend, 0)
            
            if atk_w > def_w:
                # 大吃小
                board[r][c] = source.copy()
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
            elif atk_w == def_w:
                # 同级互吃
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
                board[r][c] = {"status": "empty", "chess": None, "owner": None}
            else:
                # 被反吃
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        
        st.session_state.selected = None
        return
    
    # 目标是空格
    if target["status"] == "empty":
        board[r][c] = source.copy()
        board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        st.session_state.selected = None
        return
    
    # 其他情况（对方明棋）不能吃
    st.session_state.selected = None

def switch_turn():
    """切换回合"""
    if st.session_state.game_mode == "two_people":
        st.session_state.current_turn = "blue" if st.session_state.current_turn == "red" else "red"
    else:
        if st.session_state.current_turn == "red":
            st.session_state.current_turn = "ai"
        elif st.session_state.current_turn == "ai":
            st.session_state.current_turn = "red"
    
    st.session_state.just_opened = None
    st.session_state.selected = None
    st.session_state.no_op += 1

# ===================== AI逻辑 =====================
def ai_move():
    """AI走棋"""
    if st.session_state.game_over:
        return
    if st.session_state.current_turn != "ai":
        return
    
    board = st.session_state.board
    
    # 找AI棋子
    ai_pieces = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]["status"] == "open" and board[r][c]["owner"] == "blue":
                ai_pieces.append((r, c))
    
    # 找暗棋
    dark_pos = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]["status"] == "dark":
                dark_pos.append((r, c))
    
    # 尝试翻吃
    for sr, sc in ai_pieces:
        for nr, nc in get_neighbors(sr, sc):
            if board[nr][nc]["status"] == "dark":
                process_click(sr, sc)
                process_click(nr, nc)
                return True
    
    # 翻暗棋
    if dark_pos:
        r, c = random.choice(dark_pos)
        process_click(r, c)
        return True
    
    # 移动
    for sr, sc in ai_pieces:
        for nr, nc in get_neighbors(sr, sc):
            if board[nr][nc]["status"] == "empty":
                process_click(sr, sc)
                process_click(nr, nc)
                return True
    
    return False

# ===================== 初始化 =====================
if "board" not in st.session_state:
    reset_game_state()

# ===================== UI =====================
st.title("🐘 4×8 象棋翻棋")

# 模式选择
if st.session_state.game_mode is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 双人对战", key="mode_two", use_container_width=True):
            reset_game_state()
            st.session_state.game_mode = "two_people"
            st.session_state.current_turn = "red"
            st.rerun()
    with col2:
        if st.button("🤖 人机对战", key="mode_ai", use_container_width=True):
            reset_game_state()
            st.session_state.game_mode = "ai_mode"
            st.session_state.current_turn = "red"
            st.rerun()
else:
    # 重置按钮
    if st.button("🔄 重新开局", key="reset_btn", use_container_width=True):
        reset_game_state()
        st.rerun()
    
    # 游戏状态
    if not st.session_state.game_over:
        turn = st.session_state.current_turn
        if turn == "red":
            st.info("🔴 红方回合")
        elif turn == "blue":
            st.info("🔵 蓝方回合")
        elif turn == "ai":
            st.warning("🤖 AI思考中...")
    
    # 绘制棋盘 - 使用4行8列的按钮网格
    board = st.session_state.board
    
    for r in range(ROWS):
        cols = st.columns(COLS)
        for c in range(COLS):
            cell = board[r][c]
            
            # 确定按钮内容和样式
            if cell["status"] == "dark":
                button_text = "?"
                css_class = "dark-btn"
                disabled = False
            elif cell["status"] == "empty":
                button_text = "·"
                css_class = "empty-btn"
                disabled = True
            else:
                button_text = cell["chess"]
                css_class = "red-btn" if cell["owner"] == "red" else "blue-btn"
                disabled = False
            
            # 检查是否被选中
            is_selected = (st.session_state.selected == (r, c))
            if is_selected:
                css_class += " selected"
            
            # 创建带样式的按钮
            with cols[c]:
                # 使用容器包装按钮并应用样式
                with st.container():
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                    if st.button(
                        button_text,
                        key=f"btn_{r}_{c}",
                        use_container_width=True,
                        disabled=disabled
                    ):
                        if not st.session_state.game_over:
                            # 处理点击
                            process_click(r, c)
                            
                            # 检查胜负
                            winner = check_win(board)
                            if winner:
                                st.session_state.game_over = True
                                st.session_state.winner = "红方胜利！" if winner == "red" else "蓝方胜利！"
                            elif st.session_state.no_op >= 10:
                                st.session_state.game_over = True
                                st.session_state.winner = "平局！"
                            else:
                                switch_turn()
                            
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # 人机模式AI自动走棋
    if st.session_state.game_mode == "ai_mode" and not st.session_state.game_over and st.session_state.current_turn == "ai":
        ai_move()
        
        # 检查胜负
        winner = check_win(st.session_state.board)
        if winner:
            st.session_state.game_over = True
            st.session_state.winner = "红方胜利！" if winner == "red" else "蓝方胜利！"
        elif st.session_state.no_op >= 10:
            st.session_state.game_over = True
            st.session_state.winner = "平局！"
        
        st.rerun()
    
    # 游戏结束显示
    if st.session_state.game_over:
        st.success(f"🏆 {st.session_state.winner}")
        if st.button("🎮 新的一局", key="new_game", use_container_width=True):
            reset_game_state()
            st.rerun()
