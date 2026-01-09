import streamlit as st
import os
from docx import Document
import re
import random

# --- 页面配置 ---
st.set_page_config(page_title="外语私教工作站", layout="wide")

# --- 工具函数：判断是否包含中文 ---
def contains_chinese(text):
    return re.search(r'[\u4e00-\u9fa5]', text) is not None

# --- 核心函数：解析 Word 语料 ---
def load_corpus(file_path):
    try:
        doc = Document(file_path)
        # 获取所有非空行
        lines = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        
        # 模式 A：听写模式需要的纯英文列表
        english_only = [line for line in lines if not contains_chinese(line)]
        
        # 模式 B：回译模式需要的双语配对 (寻找 中文-英文 的组合)
        pairs = []
        for i in range(len(lines) - 1):
            # 如果当前行是中文，下一行是英文，则组成一对
            if contains_chinese(lines[i]) and not contains_chinese(lines[i+1]):
                pairs.append({"q": lines[i], "a": lines[i+1]})
        
        return english_only, pairs
    except Exception as e:
        st.error(f"解析文件失败: {e}")
        return [], []

# --- 初始化 Session State ---
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'shuffled_data' not in st.session_state:
    st.session_state.shuffled_data = None
if 'last_file_mode' not in st.session_state:
    st.session_state.last_file_mode = ""

# --- 侧边栏 ---
st.sidebar.title("🎧 学习设置")
mode = st.sidebar.radio("选择模式", ["🎧 英文听写", "✍️ 中译英回译"])

DICTATION_DIR = "corpora/dictation"
TRANSLATION_DIR = "corpora/translation"
folder = DICTATION_DIR if "听写" in mode else TRANSLATION_DIR
files = [f for f in os.listdir(folder) if f.endswith('.docx')] if os.path.exists(folder) else []

if not files:
    st.warning(f"请在 {folder} 文件夹中放入 .docx 语料")
else:
    selected_file = st.sidebar.selectbox("选择语料文件", files)
    file_path = os.path.join(folder, selected_file)
    
    # 加载数据
    en_list, cn_en_pairs = load_corpus(file_path)
    
    # 确定当前使用的数据集
    active_data = en_list if "听写" in mode else cn_en_pairs
    
    # 检查文件或模式是否切换，若切换则重置
    current_key = f"{selected_file}_{mode}"
    if st.session_state.last_file_mode != current_key:
        st.session_state.current_index = 0
        st.session_state.last_file_mode = current_key
        st.session_state.shuffled_data = None

    if not active_data:
        st.error("语料解析失败：听写模式需要英文行；回译模式需要'中文行+英文行'的对照格式。")
    else:
        # --- 乱序逻辑 ---
        if "回译" in mode:
            is_random = st.sidebar.checkbox("乱序练习")
            if is_random and st.session_state.shuffled_data is None:
                st.session_state.shuffled_data = random.sample(active_data, len(active_data))
            elif not is_random:
                st.session_state.shuffled_data = None
        
        display_data = st.session_state.shuffled_data if st.session_state.shuffled_data else active_data
        total = len(display_data)
        
        # --- 界面渲染 ---
        st.title(mode)
        st.progress((st.session_state.current_index + 1) / total)
        st.caption(f"进度：{st.session_state.current_index + 1} / {total}")

        st.write("---")

        if "听写" in mode:
            # 听写逻辑
            current_item = display_data[st.session_state.current_index]
            st.subheader("第一步：听音频")
            st.info("（此处播放音频...）")
            
            st.subheader("第二步：拼写英文")
            user_input = st.text_area("输入你听到的英文内容：", key=f"dict_{st.session_state.current_index}")
            
            with st.expander("查看英文原文"):
                st.code(current_item)

        else:
            # 回译逻辑 (中译英)
            current_item = display_data[st.session_state.current_index]
            st.subheader("🚩 请将下句译为英文：")
            st.warning(current_item['q']) # 显示中文
            
            user_input = st.text_area("在此输入英文译文：", key=f"trans_{st.session_state.current_index}")
            
            if st.button("检查答案"):
                if user_input.strip().lower() == current_item['a'].strip().lower():
                    st.success("完全正确！")
                else:
                    st.write("💡 参考答案：")
                    st.success(current_item['a'])

        # --- 翻页控制 ---
        st.write("---")
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            if st.button("⬅️ 上一句"):
                if st.session_state.current_index > 0:
                    st.session_state.current_index -= 1
                    st.rerun()
        with col2:
            if st.button("下一句 ➡️"):
                if st.session_state.current_index < total - 1:
                    st.session_state.current_index += 1
                    st.rerun()
                else:
                    st.balloons()
                    st.success("本篇练习完成！")