import streamlit as st
import time
import os
from api_handler import generate_question
from plot_utils import execute_ai_plot_code, clean_up_temp_images
from docx_generator import generate_word_documents

st.set_page_config(page_title="阿凱的數學出卷系統", layout="wide", page_icon="📝")

st.markdown("""
    <style>
    .main { background-color: #FAFAFA; }
    h1, h2, h3 { color: #2C3E50; }
    .question-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.warning("📱 **【系統提示】** 強烈建議使用 **電腦版網頁** 開啟，以獲得最佳的操作體驗與預覽效果！")
st.title("📝 阿凱的數學出卷系統(含幾何圖形)")
st.divider()

if "questions" not in st.session_state:
    st.session_state.questions = []
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

with st.sidebar:
    st.header("⚙️ 系統設定")
    api_key = st.text_input("輸入 Google API Key", type="password")
    st.markdown("[👉 點此前往獲取金鑰](https://aistudio.google.com/app/api-keys)", unsafe_allow_html=True)
    auth_code = st.text_input("系統啟動碼", type="password")
    
    model_options = [
        "gemini-3-flash-preview", 
        "gemini-3.1-flash-lite", 
        "gemini-3.1-flash-lite-preview", 
        "gemma-4-31b-it", 
        "gemma-4-26b-a4b-it"
    ]
    selected_model = st.selectbox("選擇 AI 模型", model_options, index=1)
    
    st.divider()
    st.header("📄 考卷格式設定")
    uploaded_file = st.file_uploader("上傳學校 Word 範本 (.docx)", type=["docx"])
    if uploaded_file is not None:
        with open("template.docx", "wb") as f: f.write(uploaded_file.getbuffer())
        st.success("✅ 範本已載入")
        
    st.divider()
    st.caption("© 宜蘭縣中華國中 - 褚煜凱老師設計")

if auth_code not in ["kai", "kai36"]:
    st.info("🔒 請輸入正確的「啟動碼」解鎖功能。"); st.stop()
elif not api_key:
    st.warning("🔑 請輸入 API Key。"); st.stop()

st.subheader("🎯 命題條件設定")
col1, col2 = st.columns(2)

with col1:
    edu_level = st.selectbox("教育階段 (108課綱)", ["國小", "國中", "高中"], index=1)
    topics_input = st.text_input("單元主題", placeholder="例如：圓內角與圓周角")
    difficulty = st.selectbox("整體難易度", ["基礎", "中等", "進階"], index=1)

with col2:
    # 🚀 已更新預設題數為 2, 2, 1
    num_single = st.number_input("單選題", min_value=0, max_value=20, value=2)
    num_fill = st.number_input("填充題", min_value=0, max_value=20, value=2)
    num_essay = st.number_input("素養題", min_value=0, max_value=5, value=1)

total_questions = num_single + num_fill + num_essay
max_allowed = 36 if auth_code == "kai36" else 15

if total_questions > max_allowed:
    st.error(f"❌ 最高僅支援 {max_allowed} 題。"); st.stop()

# 🚀 佈局修正：將按鈕固定在條件設定區的正下方
start_btn = st.button("🚀 開始漸進式生成考卷", type="primary", use_container_width=True)

# 🚀 佈局修正：在按鈕「之後」才宣告顯示區容器，這樣考卷長出來時只會往下長，不會把按鈕推走
final_view_container = st.empty()

if start_btn:
    if not topics_input: 
        st.warning("請輸入單元！")
        st.stop()
        
    final_view_container.empty()
    st.session_state.questions = []
    st.session_state.is_generating = True
    st.rerun()

# 將後續的所有生成與預覽畫面，強制鎖進 final_view_container 中
if st.session_state.is_generating:
    with final_view_container.container():
        clean_up_temp_images([f"temp_img_{i}.png" for i in range(40)])
        
        st.divider()
        st.subheader("👁️ 考卷即時預覽 (生成中...)")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        preview_container = st.container()
        
        task_list = ["純文字計算題 (無插圖)"]*num_single + ["一般幾何 (平面/複合圖形)"]*num_fill + ["會考非選素養題 (情境+兩小題)"]*num_essay
        
        for idx, q_type in enumerate(task_list):
            status_text.text(f"⏳ 正在思考並繪製第 {idx+1}/{total_questions} 題... ({q_type})")
            
            result = generate_question(api_key, selected_model, edu_level, topics_input, difficulty, q_type, question_index=idx+1)
            
            if isinstance(result, list) and len(result) > 0: result = result[0]
            if not isinstance(result, dict): result = {"question_text": "格式異常", "python_code": ""}
            
            img_path = f"temp_img_{idx}.png"
            p_code = result.get("python_code")
            if p_code is None: p_code = ""
                
            has_img = execute_ai_plot_code(p_code, img_path)
            
            new_q = {
                "id": idx, "type": q_type, 
                "text": result.get("question_text", "生成失敗"), 
                "code": p_code, 
                "img": img_path if has_img else None
            }
            st.session_state.questions.append(new_q)
            
            with preview_container:
                st.markdown(f"<div class='question-card'>", unsafe_allow_html=True)
                st.markdown(f"**第 {idx+1} 題**")
                st.markdown(new_q["text"])
                if new_q["img"]: st.image(new_q["img"], width=400)
                st.markdown("</div>", unsafe_allow_html=True)
                
            progress_bar.progress((idx + 1) / total_questions)
            if auth_code == "kai36" and total_questions > 15 and (idx + 1) % 5 == 0:
                status_text.text("🛡️ 流量冷卻中 (8 秒)..."); time.sleep(8)
                
        status_text.text("✅ 生成完畢！您可以點擊下方按鈕匯出檔案，或針對單題重新生成。")
        st.session_state.is_generating = False
        st.rerun()

if st.session_state.questions and not st.session_state.is_generating:
    with final_view_container.container():
        st.divider()
        st.subheader("👁️ 考卷微調與下載區")
        
        for idx, q_data in enumerate(st.session_state.questions):
            st.markdown(f"<div class='question-card'>", unsafe_allow_html=True)
            st.markdown(f"**第 {idx+1} 題** ({q_data['type']})")
            st.markdown(q_data["text"])
            if q_data["img"] and os.path.exists(q_data["img"]): st.image(q_data["img"], width=400)
                
            if st.button(f"🔄 換一題 (第 {idx+1} 題)", key=f"reroll_{idx}"):
                with st.spinner("重新生成中..."):
                    new_res = generate_question(api_key, selected_model, edu_level, topics_input, difficulty, q_data['type'], True, q_data["text"], q_data["code"], question_index=idx+1)
                    
                    if isinstance(new_res, list) and len(new_res) > 0: new_res = new_res[0]
                    if not isinstance(new_res, dict): new_res = {"question_text": "錯誤", "python_code": ""}
                    
                    new_p_code = new_res.get("python_code")
                    if new_p_code is None: new_p_code = ""
                        
                    has_img = execute_ai_plot_code(new_p_code, q_data["img"])
                    
                    st.session_state.questions[idx]["text"] = new_res.get("question_text", "失敗")
                    st.session_state.questions[idx]["code"] = new_p_code
                    st.session_state.questions[idx]["img"] = q_data["img"] if has_img else None
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("🖨️ 匯出正式考卷")
        
        template_path = "template.docx" if os.path.exists("template.docx") else None
        
        with st.spinner("準備檔案中..."):
            docx_file, raw_md = generate_word_documents(st.session_state.questions, template_path)
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            if os.path.exists(docx_file):
                with open(docx_file, "rb") as file:
                    st.download_button("📥 下載 Word 考卷 (.docx)", data=file, file_name="阿凱數學考卷.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary", use_container_width=True)
        with col_dl2:
            st.download_button("📥 下載 Markdown 原始碼 (.md)", data=raw_md, file_name="阿凱數學考卷_原始碼.md", mime="text/markdown", use_container_width=True)