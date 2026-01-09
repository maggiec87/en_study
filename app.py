import streamlit as st
import pandas as pd
import os
from docx import Document

# --- 页面配置 ---
st.set_page_config(page_title="外语私教 - 综合训练系统", layout="wide")

# --- 路径定义 ---
DICT_DIR = "corpora/dictation"
TRANS_DIR = "corpora/translation"
DICT_AUDIO_DIR = "corpora/dictation/audio"

# --- 核心函数 ---
def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

@st.cache_data
def load_excel(file_path):
    df = pd.read_excel(file_path)
    df.columns = ['Chinese', 'English'] + (['Audio'] if 'Audio' in df.columns or len(df.columns)>2 else [])
    return df.to_dict('records')

# --- 侧边栏：模式切换 ---
st.sidebar.title("🚀 学习模式")
mode = st.sidebar.radio("请选择：", ["🎧 听写模式 (听音写文)", "✍️ 回译模式 (全文预览+逐句练习)"])

# --- 逻辑 A：听写模式 ---
if "听写" in mode:
    st.sidebar.subheader("听写配置")
    files = [f for f in os.listdir(DICT_DIR) if f.endswith(('.xlsx', '.xls'))]
    
    if not files:
        st.info("请在 corpora/dictation 放入 Excel 语料")
    else:
        selected_file = st.sidebar.selectbox("选择听写课目", files)
        data = load_excel(os.path.join(DICT_DIR, selected_file))
        
        if 'dict_idx' not in st.session_state: st.session_state.dict_idx = 0
        
        curr = data[st.session_state.dict_idx]
        st.title("🎧 英文听写")
        
        # 音频播放
        audio_path = os.path.join(DICT_AUDIO_DIR, str(curr.get('Audio', '')))
        if os.path.exists(audio_path):
            st.audio(audio_path)
        else:
            st.error(f"未找到音频文件: {curr.get('Audio')}")

        user_input = st.text_area("听音写英文：", key=f"dict_{st.session_state.dict_idx}")
        
        with st.expander("查看参考答案"):
            st.write(f"**英文：** {curr['English']}")
            st.write(f"**中文：** {curr['Chinese']}")

        # 翻页
        c1, c2 = st.columns(2)
        if c1.button("上一句") and st.session_state.dict_idx > 0:
            st.session_state.dict_idx -= 1
            st.rerun()
        if c2.button("下一句") and st.session_state.dict_idx < len(data)-1:
            st.session_state.dict_idx += 1
            st.rerun()

# --- 逻辑 B：回译模式 ---
else:
    st.sidebar.subheader("回译配置")
    # 获取回译目录下的所有 docx 文件作为索引
    docx_files = [f for f in os.listdir(TRANS_DIR) if f.endswith('.docx')]
    
    if not docx_files:
        st.info("请在 corpora/translation 放入 Word(全文) 和 Excel(逐句)")
    else:
        selected_base = st.sidebar.selectbox("选择回译课目", docx_files)
        base_name = os.path.splitext(selected_base)[0]
        
        # 查找对应的 Excel 文件
        excel_path = os.path.join(TRANS_DIR, f"{base_name}.xlsx")
        docx_path = os.path.join(TRANS_DIR, selected_base)

        # 步骤选择：预览 vs 练习
        step = st.radio("学习步骤：", ["1. 全文预览 (Word)", "2. 逐句回译练习 (Excel)"], horizontal=True)

        if "1. 全文预览" in step:
            st.title("📖 全文通读")
            if os.path.exists(docx_path):
                content = read_docx(docx_path)
                st.text_area("文章内容", content, height=400)
            else:
                st.error("未找到对应的 Word 文件")
        
        else:
            st.title("✍️ 中译英回译")
            if not os.path.exists(excel_path):
                st.error(f"未找到对应的 Excel 练习表: {base_name}.xlsx")
            else:
                trans_data = load_excel(excel_path)
                if 'trans_idx' not in st.session_state: st.session_state.trans_idx = 0
                
                # 乱序功能
                if st.sidebar.checkbox("乱序练习"):
                    if 'shuffled_trans' not in st.session_state:
                        st.session_state.shuffled_trans = random.sample(trans_data, len(trans_data))
                    display_data = st.session_state.shuffled_trans
                else:
                    display_data = trans_data

                curr = display_data[st.session_state.trans_idx]
                
                st.info(f"中文提示：{curr['Chinese']}")
                user_ans = st.text_area("请输入英文翻译：", key=f"tr_{st.session_state.trans_idx}")
                
                if st.button("检查答案"):
                    if user_ans.strip().lower() == str(curr['English']).strip().lower():
                        st.success("太棒了！完全正确。")
                    else:
                        st.warning(f"参考答案：{curr['English']}")

                # 翻页
                c1, c2 = st.columns(2)
                if c1.button("上一句") and st.session_state.trans_idx > 0:
                    st.session_state.trans_idx -= 1
                    st.rerun()
                if c2.button("下一句") and st.session_state.trans_idx < len(display_data)-1:
                    st.session_state.trans_idx += 1
                    st.rerun()