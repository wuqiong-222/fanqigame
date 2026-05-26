import streamlit as st
import random

# -------------------------- 1. 初始化状态 --------------------------
if "board" not in st.session_state:
    # 4x4 棋盘，数字1~8成对，共16格
    nums = list(range(1, 9)) * 2
    random.shuffle(nums)
    st.session_state.board = nums
    st.session_state.revealed = [False] * 16  # 是否翻开
    st.session_state.first = None              # 第一次点击
    st.session_state.moves = 0
    st.session_state.game_over = False

# -------------------------- 2. 工具函数 --------------------------
def reset_game():
    nums = list(range(1, 9)) * 2
    random.shuffle(nums)
    st.session_state.board = nums
    st.session_state.revealed = [False] * 16
    st.session_state.first = None
    st.session_state.moves = 0
    st.session_state.game_over = False

def handle_click(idx):
    if st.session_state.game_over:
        return
    if st.session_state.revealed[idx]:
        return

    st.session_state.revealed[idx] = True

    if st.session_state.first is None:
        # 第一次翻
        st.session_state.first = idx
    else:
        # 第二次翻，判断是否匹配
        first_idx = st.session_state.first
        if st.session_state.board[first_idx] != st.session_state.board[idx]:
            # 不匹配，延迟翻回去
            st.session_state.revealed[first_idx] = False
            st.session_state.revealed[idx] = False
        st.session_state.first = None
        st.session_state.moves += 1

    # 判断游戏结束
    if all(st.session_state.revealed):
        st.session_state.game_over = True

# -------------------------- 3. UI 渲染 --------------------------
st.title("🧠 益智翻棋游戏")
st.subheader(f"步数：{st.session_state.moves}")

if st.button("🔄 重新开始"):
    reset_game()

# 渲染4x4棋盘
cols = st.columns(4)
for i in range(16):
    with cols[i % 4]:
        if st.session_state.revealed[i]:
            st.button(f"{st.session_state.board[i]}", key=f"btn_{i}", disabled=True)
        else:
            st.button("❓", key=f"btn_{i}", on_click=handle_click, args=(i,))

if st.session_state.game_over:
    st.success(f"🎉 恭喜！你用 {st.session_state.moves} 步完成游戏！")