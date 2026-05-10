import streamlit as st
import time
import os
import random
from api_handler import generate_question
from plot_utils import execute_ai_plot_code, clean_up_temp_images
from docx_generator import generate_word_documents

# ==========================================
# 1. 網頁基本設定與樣式 (淡色舒適風格)
# ==========================================
st.set_page_config(page_title="AI 智慧命題系統", layout="wide", page_icon="📝")

# 自訂 CSS 隱藏預設選單，並美化介面
st.markdown("""
    <style>
    .main { background-color: #FAFAFA; }
    h1, h2, h3 { color: #2C3E50; }
    .stAlert { border-radius: 10px; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .question-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 行動裝置醒目警告
st.warning("📱 **【系統提示】** 本系統涉及複雜的數學公式渲染與版面配置，強烈建議使用 **電腦版網頁** 開啟，以獲得最佳的操作體驗與預覽效果！")

# 標題與版權宣告
st.title("📝 校園 AI 智慧命題系統")
st.markdown("#### *宜蘭縣中華國中 - 褚煜凱老師設計*")
st.divider()

# ==========================================
# 2. 狀態管理 (Session State) 初始化
# ==========================================
if "questions" not in st.session_state:
    st.session_state.questions = []
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# ==========================================
# 3. 左側邊欄：系統設定與 API 驗證
# ==========================================
with st.sidebar:
    st.header("⚙️ 系統設定")
    
    # API Key 設定區塊
    api_key = st.text_input("輸入 Google API Key", type="password")
    st.markdown("[👉 點此前往 Google AI Studio 獲取金鑰](https://aistudio.google.com/app/api-keys)", unsafe_allow_html=True)
    
    # 啟動碼驗證
    auth_code = st.text_input("系統啟動碼", type="password", placeholder="請輸入啟動碼以啟用系統")
    
    # 模型選擇
    model_options = [
        "gemini-3-flash-preview", 
        "gemini-3.1-flash-lite", 
        "gemini-3.1-flash-lite-preview", 
        "gemma-4-31B-it", 
        "gemma-4-26B-A4B-it"
    ]
    selected_model = st.selectbox("選擇 AI 模型", model_options)
    
    st.divider()
    st.header("📄 考卷格式設定")
    uploaded_file = st.file_uploader("上傳學校 Word 範本 (.docx)", type=["docx"])
    if uploaded_file is not None:
        with open("template.docx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ 範本已載入")

# ==========================================
# 4. 主畫面：命題參數設定
# ==========================================
if auth_code not in ["kai", "kai36"]:
    st.info("🔒 請於左側邊欄輸入正確的「啟動碼」以解鎖命題功能。")
    st.stop()
elif not api_key:
    st.warning("🔑 請輸入 Google API Key 以連線至 AI 引擎。")
    st.stop()

st.subheader("🎯 命題條件設定")
col1, col2 = st.columns(2)

with col1:
    topics_input = st.text_input("單元主題", placeholder="例如：平行四邊形, 幾何證明")
    difficulty = st.selectbox("整體難易度", ["基礎 (B)", "中等 (B++)", "進階挑戰 (A)"])

with col2:
    num_single = st.number_input("四選一單選題 (題數)", min_value=0, max_value=20, value=5)
    num_fill = st.number_input("填充題 (題數)", min_value=0, max_value=20, value=5)
    num_essay = st.number_input("素養非選題 (題數)", min_value=0, max_value=5, value=1)

total_questions = num_single + num_fill + num_essay

# 題數限制與警告邏輯
max_allowed = 36 if auth_code == "kai36" else 15
if total_questions > max_allowed:
    st.error(f"❌ 您目前的啟動碼最高僅支援 {max_allowed} 題，請減少題數或使用進階啟動碼。")
    st.stop()

if auth_code == "kai36" and total_questions > 15:
    st.warning("⚠️ **【大題庫模式啟用】** 您設定的題數較多，為避免觸發 AI 伺服器流量限制，系統將在背景啟動安全延遲保護。出卷時間預估需 3～5 分鐘，請耐心等候！")

# ==========================================
# 5. 核心邏輯：生成考卷
# ==========================================
if st.button("🚀 開始一鍵生成考卷", type="primary", use_container_width=True):
    if total_questions == 0:
        st.warning("請至少設定一題！")
    elif not topics_input:
        st.warning("請輸入單元主題！")
    else:
        st.session_state.is_generating = True
        st.session_state.questions = []
        clean_up_temp_images([f"temp_img_{i}.png" for i in range(40)]) # 清理舊圖
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 建立題型需求列表
        task_list = ["純文字計算題 (無插圖)"] * num_single + \
                    ["一般幾何 (平面/複合圖形)"] * num_fill + \
                    ["會考非選素養題 (情境+兩小題)"] * num_essay
        
        for idx, q_type in enumerate(task_list):
            status_text.text(f"⏳ 正在思考第 {idx+1}/{total_questions} 題... ({q_type})")
            
            # API 呼叫
            result = generate_question(
                api_key=api_key, model_name=selected_model, 
                topic=topics_input, difficulty=difficulty, question_type=q_type
            )
            
            # 處理繪圖
            img_path = f"temp_img_{idx}.png"
            has_img = execute_ai_plot_code(result.get("python_code", ""), img_path)
            
            st.session_state.questions.append({
                "id": idx,
                "type": q_type,
                "text": result.get("question_text", "題目生成失敗"),
                "code": result.get("python_code", ""),
                "img": img_path if has_img else None
            })
            
            progress_bar.progress((idx + 1) / total_questions)
            
            # 大題庫模式的流量保護延遲 (每 5 題休息 8 秒)
            if auth_code == "kai36" and total_questions > 15 and (idx + 1) % 5 == 0:
                status_text.text("🛡️ 觸發流量保護機制，系統冷卻中 (約 8 秒)...")
                time.sleep(8)
                
        status_text.text("✅ 所有題目生成完畢！")
        st.session_state.is_generating = False

# ==========================================
# 6. 預覽與單題重測區
# ==========================================
if st.session_state.questions and not st.session_state.is_generating:
    st.divider()
    st.subheader("👁️ 考卷預覽與微調")
    
    for idx, q_data in enumerate(st.session_state.questions):
        # 使用 HTML/CSS 建立卡片視覺
        st.markdown(f"<div class='question-card'>", unsafe_allow_html=True)
        st.markdown(f"**第 {idx+1} 題** ({q_data['type']})")
        
        # 顯示題目 (Streamlit markdown 自動支援 KaTeX 數學渲染)
        st.markdown(q_data["text"])
        
        # 顯示圖片
        if q_data["img"] and os.path.exists(q_data["img"]):
            st.image(q_data["img"], width=400)
            
        # 重新生成單題按鈕
        if st.button(f"🔄 換一題 (第 {idx+1} 題)", key=f"reroll_{idx}"):
            with st.spinner("重新生成中..."):
                new_result = generate_question(
                    api_key=api_key, model_name=selected_model, 
                    topic=topics_input, difficulty=difficulty, 
                    question_type=q_data['type'], is_reroll=True,
                    current_question=q_data["text"], current_code=q_data["code"]
                )
                has_img = execute_ai_plot_code(new_result.get("python_code", ""), q_data["img"])
                
                st.session_state.questions[idx]["text"] = new_result.get("question_text", "生成失敗")
                st.session_state.questions[idx]["code"] = new_result.get("python_code", "")
                st.session_state.questions[idx]["img"] = q_data["img"] if has_img else None
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # 7. 最終匯出 Word (包含學校排版與原生方程式)
    # ==========================================
    st.divider()
    st.subheader("🖨️ 匯出正式考卷")
    
    template_path = "template.docx" if os.path.exists("template.docx") else None
    
    if st.button("📥 下載教師用解答本 (.docx)", type="primary"):
        with st.spinner("正在執行 Pandoc 方程式轉換與 Word 無損縫合，請稍候..."):
            output_file = generate_word_documents(
                questions_data=st.session_state.questions,
                template_path=template_path,
                generate_student_version=False # 預設只產生教師版
            )
            
            if os.path.exists(output_file):
                with open(output_file, "rb") as file:
                    st.download_button(
                        label="✅ 點擊此處儲存檔案",
                        data=file,
                        file_name="中華國中_AI數學考卷.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )