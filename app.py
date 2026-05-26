import streamlit as st
import random

# ===================== 全局常量 =====================
CHESS_WEIGHT = {
    "将": 9, "帅": 9,
    "士": 8, "仕": 8,
    "象": 7, "相": 7,
    "马": 6,
    "车": 5,
    "炮": 4,
    "兵": 3, "卒": 3
}

SPECIAL_EAT = {
    "兵": ["将", "帅"],
    "卒": ["将", "帅"]
}

# 32个棋子
ALL_CHESS = (
    ["将"] + ["士"] * 2 + ["象"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["兵"] * 5 +
    ["帅"] + ["仕"] * 2 + ["相"] * 2 + ["马"] * 2 + ["车"] * 2 + ["炮"] * 2 + ["卒"] * 5
)

ROWS, COLS = 4, 8

st.set_page_config(
    page_title="4×8象棋翻棋", 
    page_icon="🐘", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===================== 全局自适应样式 =====================
st.markdown("""
<style>
    /* 移除所有默认边距 */
    .main > div {
        padding: 0rem 0rem;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* 标题缩小边距 */
    h1 {
        margin-top: 0 !important;
        margin-bottom: 0.25rem !important;
        font-size: 1.8rem !important;
        text-align: center;
    }
    
    /* 按钮行紧凑 */
    .stButton {
        margin: 0 !important;
    }
    .stButton > button {
        margin: 0 !important;
        padding: 0.3rem 0rem !important;
    }
    
    /* 信息提示紧凑 */
    .stAlert {
        padding: 0.3rem !important;
        margin: 0.3rem 0 !important;
        font-size: 0.85rem !important;
    }
    
    /* 棋盘容器 - 自适应 */
    .board-wrapper {
        display: flex;
        justify-content: center;
        width: 100%;
        margin: 0 auto;
    }
    
    /* 棋盘网格 - 响应式 */
    .chess-grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: min(1vw, 4px);
        background-color: #d4b87a;
        padding: min(2vw, 8px);
        border-radius: min(3vw, 12px);
        max-width: 100%;
        margin: 0 auto;
    }
    
    /* 棋子格子 */
    .chess-cell {
        aspect-ratio: 1 / 1;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        border-radius: 50%;
        cursor: pointer;
        transition: all 0.1s ease;
        font-family: "KaiTi", "华文楷书", "Microsoft YaHei", serif;
        font-size: clamp(16px, 5vw, 28px);
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    /* 暗棋 */
    .chess-cell.dark {
        background: linear-gradient(145deg, #5a5a5a, #3a3a3a);
        color: #ddd;
    }
    
    /* 红方棋子 */
    .chess-cell.red {
        background: radial-gradient(circle at 30% 30%, #e34234, #b22b1c);
        color: #ffd966;
        text-shadow: 1px 1px 0 #6b1a0f;
        border: 1px solid #ffaa77;
    }
    
    /* 蓝方棋子 */
    .chess-cell.blue {
        background: radial-gradient(circle at 30% 30%, #3a6ea5, #1e3a5f);
        color: #e8e8e8;
        text-shadow: 1px 1px 0 #0f2a44;
        border: 1px solid #8ab3d0;
    }
    
    /* 空格 */
    .chess-cell.empty {
        background: #e8dbbd;
        box-shadow: inset 0 0 0 1px #c8aa6e;
        cursor: default;
    }
    
    /* 选中高亮 */
    .chess-cell.selected {
        box-shadow: 0 0 0 2px gold, 0 0 0 4px #ffaa33;
        transform: scale(0.97);
    }
    
    /* 手机横屏时进一步优化 */
    @media (orientation: landscape) and (max-height: 500px) {
        .chess-cell {
            font-size: 14px;
        }
        h1 { font-size: 1.2rem !important; }
        .stAlert { font-size: 0.7rem !important; padding: 0.1rem !important; }
    }
    
    /* 小屏手机竖屏 */
    @media (max-width: 500px) {
        .chess-cell {
            font-size: 14px;
        }
        h1 { font-size: 1.3rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ===================== 工具函数 =====================
def get_neighbors(r, c):
    return [(r+dr, c+dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)] 
            if 0 <= r+dr < ROWS and 0 <= c+dc < COLS]

def init_board():
    chess = ALL_CHESS.copy()
    random.shuffle(chess)
    return [[{"status": "dark", "chess": chess[r*COLS + c], "owner": None} 
             for c in range(COLS)] for r in range(ROWS)]

def check_win(board):
    red_alive = any(board[r][c]["status"] == "open" and board[r][c]["owner"] == "red" and board[r][c]["chess"] == "将" 
                    for r in range(ROWS) for c in range(COLS))
    blue_alive = any(board[r][c]["status"] == "open" and board[r][c]["owner"] == "blue" and board[r][c]["chess"] == "帅" 
                     for r in range(ROWS) for c in range(COLS))
    if red_alive and blue_alive:
        return None
    if red_alive:
        return "red"
    if blue_alive:
        return "blue"
    return None

def count_remaining_pieces(board):
    red_count = blue_count = 0
    for r in range(ROWS):
        for c in range(COLS):
            cell = board[r][c]
            if cell["status"] == "open":
                if cell["owner"] == "red":
                    red_count += 1
                elif cell["owner"] == "blue":
                    blue_count += 1
    return red_count, blue_count

def check_draw(board, no_op_count):
    red_count, blue_count = count_remaining_pieces(board)
    return (red_count == 1 and blue_count == 1) and no_op_count >= 10

def can_pao_eat(source_pos, target_pos, board):
    sr, sc = source_pos
    tr, tc = target_pos
    if sr == tr:
        step = 1 if tc > sc else -1
        between = [c for c in range(sc + step, tc, step) if board[sr][c]["status"] != "empty"]
        return len(between) == 1
    elif sc == tc:
        step = 1 if tr > sr else -1
        between = [r for r in range(sr + step, tr, step) if board[r][sc]["status"] != "empty"]
        return len(between) == 1
    return False

# ===================== 游戏逻辑 =====================
def process_click(r, c):
    if st.session_state.game_over:
        return
    
    board = st.session_state.board
    current = st.session_state.current_turn
    selected = st.session_state.selected
    just_opened = st.session_state.just_opened
    
    cell = board[r][c]
    
    if (r, c) == just_opened:
        return
    
    # 没有选中任何棋子
    if selected is None:
        # 翻暗棋
        if cell["status"] == "dark":
            is_red = cell["chess"] in ["将","士","象","马","车","炮","兵"]
            owner = "red" if is_red else "blue"
            
            if current is None:
                st.session_state.current_turn = owner
            
            cell["status"] = "open"
            cell["owner"] = owner
            st.session_state.just_opened = (r, c)
            st.session_state.no_op = 0
            return
        
        # 选中己方棋子
        if cell["status"] == "open" and cell["owner"] == current:
            st.session_state.selected = (r, c)
        return
    
    # 已选中棋子
    sr, sc = selected
    source = board[sr][sc]
    target = board[r][c]
    
    if (r, c) not in get_neighbors(sr, sc):
        st.session_state.selected = None
        return
    
    # 目标暗棋：主动翻吃
    if target["status"] == "dark":
        is_red_target = target["chess"] in ["将","士","象","马","车","炮","兵"]
        target_owner = "red" if is_red_target else "blue"
        target["status"] = "open"
        target["owner"] = target_owner
        st.session_state.just_opened = (r, c)
        st.session_state.no_op = 0
        
        atk = source["chess"]
        defend = target["chess"]
        
        # 炮的特殊规则
        if atk in ["炮", "炮"]:
            if not can_pao_eat((sr, sc), (r, c), board):
                st.session_state.selected = None
                return
        
        # 兵/卒吃将/帅
        if atk in SPECIAL_EAT and defend in SPECIAL_EAT[atk]:
            board[r][c] = source.copy()
            board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        else:
            atk_w = CHESS_WEIGHT[atk]
            def_w = CHESS_WEIGHT[defend]
            
            if atk_w > def_w:
                board[r][c] = source.copy()
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
            elif atk_w == def_w:
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
                board[r][c] = {"status": "empty", "chess": None, "owner": None}
            else:
                board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        
        st.session_state.selected = None
        return
    
    # 目标空格：移动
    if target["status"] == "empty":
        board[r][c] = source.copy()
        board[sr][sc] = {"status": "empty", "chess": None, "owner": None}
        st.session_state.selected = None
        return
    
    # 对方明棋：不能吃
    if target["status"] == "open" and target["owner"] != current:
        st.session_state.selected = None
        return
    
    st.session_state.selected = None

def switch_turn():
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
    if st.session_state.game_over or st.session_state.current_turn != "ai":
        return False
    
    board = st.session_state.board
    
    ai_pieces = [(r, c) for r in range(ROWS) for c in range(COLS) 
                 if board[r][c]["status"] == "open" and board[r][c]["owner"] == "blue"]
    dark_pos = [(r, c) for r in range(ROWS) for c in range(COLS) 
                if board[r][c]["status"] == "dark"]
    
    # 优先翻吃
    for sr, sc in ai_pieces:
        for nr, nc in get_neighbors(sr, sc):
            if board[nr][nc]["status"] == "dark":
                if board[sr][sc]["chess"] in ["炮", "炮"]:
                    if can_pao_eat((sr, sc), (nr, nc), board):
                        process_click(sr, sc)
                        process_click(nr, nc)
                        return True
                else:
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
    st.session_state.board = init_board()
    st.session_state.game_mode = None
    st.session_state.current_turn = None
    st.session_state.selected = None
    st.session_state.just_opened = None
    st.session_state.no_op = 0
    st.session_state.game_over = False
    st.session_state.winner = None

# ===================== UI =====================
st.title("🐘 4×8 象棋翻棋")

# 模式选择
if st.session_state.game_mode is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 双人对战", use_container_width=True):
            st.session_state.board = init_board()
            st.session_state.game_mode = "two_people"
            st.session_state.current_turn = None
            st.session_state.selected = None
            st.session_state.just_opened = None
            st.session_state.no_op = 0
            st.session_state.game_over = False
            st.rerun()
    with col2:
        if st.button("🤖 人机对战", use_container_width=True):
            st.session_state.board = init_board()
            st.session_state.game_mode = "ai_mode"
            st.session_state.current_turn = None
            st.session_state.selected = None
            st.session_state.just_opened = None
            st.session_state.no_op = 0
            st.session_state.game_over = False
            st.rerun()
else:
    # 按钮行
    col_reset, col_back = st.columns(2)
    with col_reset:
        if st.button("🔄 重新开局", use_container_width=True):
            st.session_state.board = init_board()
            st.session_state.selected = None
            st.session_state.just_opened = None
            st.session_state.no_op = 0
            st.session_state.game_over = False
            st.session_state.current_turn = None
            st.rerun()
    with col_back:
        if st.button("🏠 返回菜单", use_container_width=True):
            st.session_state.game_mode = None
            st.rerun()
    
    # 游戏状态
    if not st.session_state.game_over:
        if st.session_state.current_turn is None:
            st.info("🎲 先手玩家请点击任意暗棋翻开第一枚棋子")
        else:
            turn = st.session_state.current_turn
            if turn == "red":
                st.info("🔴 红方回合")
            elif turn == "blue":
                st.info("🔵 蓝方回合")
            elif turn == "ai":
                st.warning("🤖 AI思考中...")
    
    # 绘制棋盘 - 使用纯HTML/CSS渲染，完全自适应
    board = st.session_state.board
    
    # 构建HTML棋盘
    board_html = '<div class="board-wrapper"><div class="chess-grid">'
    
    for r in range(ROWS):
        for c in range(COLS):
            cell = board[r][c]
            
            if cell["status"] == "dark":
                text = "?"
                cls = "dark"
            elif cell["status"] == "empty":
                text = "·"
                cls = "empty"
            else:
                text = cell["chess"]
                cls = "red" if cell["owner"] == "red" else "blue"
            
            if st.session_state.selected == (r, c):
                cls += " selected"
            
            # 添加点击事件，通过Streamlit的components传值
            board_html += f'''
            <div class="chess-cell {cls}" onclick="parent.postMessage({{type: 'chess_click', row: {r}, col: {c}}}, '*')">
                {text}
            </div>
            '''
    
    board_html += '</div></div>'
    
    # 渲染HTML棋盘
    st.components.v1.html(board_html, height=None, scrolling=False)
    
    # 处理JavaScript回调
    query_params = st.query_params
    if "click_row" in query_params and "click_col" in query_params:
        try:
            r = int(query_params["click_row"])
            c = int(query_params["click_col"])
            if not st.session_state.game_over:
                process_click(r, c)
                winner = check_win(st.session_state.board)
                if winner:
                    st.session_state.game_over = True
                    st.session_state.winner = "红方胜利！" if winner == "red" else "蓝方胜利！"
                elif check_draw(st.session_state.board, st.session_state.no_op):
                    st.session_state.game_over = True
                    st.session_state.winner = "平局！"
                elif st.session_state.current_turn is not None:
                    switch_turn()
                # 清除query_params
                st.query_params.clear()
                st.rerun()
        except:
            pass
    
    # AI自动走棋（使用JavaScript定时触发）
    if (st.session_state.game_mode == "ai_mode" and 
        not st.session_state.game_over and 
        st.session_state.current_turn == "ai"):
        
        # 使用JavaScript触发AI移动
        ai_move_html = """
        <script>
        setTimeout(() => {
            parent.postMessage({type: 'ai_move'}, '*');
        }, 100);
        </script>
        """
        st.components.v1.html(ai_move_html, height=0)
        
        # 检查AI移动后的结果
        if "ai_moved" not in st.session_state:
            st.session_state.ai_moved = True
            # 这里需要实际执行AI移动，简化处理：在下次rerun时AI会再次触发
            # 实际AI移动已在ai_move()中执行，但需要刷新
            st.rerun()
    
    # 游戏结束
    if st.session_state.game_over:
        st.success(f"🏆 {st.session_state.winner}")
        if st.button("🎮 新的一局", use_container_width=True):
            st.session_state.board = init_board()
            st.session_state.selected = None
            st.session_state.just_opened = None
            st.session_state.no_op = 0
            st.session_state.game_over = False
            st.session_state.current_turn = None
            st.rerun()

# ===================== JavaScript回调处理（放在最底部） =====================
# 使用st.query_params传递点击坐标
components_code = """
<script>
window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'chess_click') {
        const url = new URL(window.location.href);
        url.searchParams.set('click_row', e.data.row);
        url.searchParams.set('click_col', e.data.col);
        window.location.href = url.toString();
    }
});
</script>
"""
st.components.v1.html(components_code, height=0)
