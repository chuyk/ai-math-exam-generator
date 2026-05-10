# 檔案 2：api_handler.py (雙重保險，要求 AI 自行擴大畫布)
import json
import random
import re
from google import genai
from google.genai import types

def fetch_syllabus_context(client, model_name, edu_level, topic):
    """先導任務：讓 AI 確立 108 課綱的學習內容與重點"""
    try:
        prompt = f"請列出台灣108課綱中，【{edu_level}】數學科關於單元【{topic}】的核心學習內容與次微概念。請用3到4個條列式重點說明即可，字數控制在100字內，這將作為後續嚴格命題的依據。"
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        return response.text.strip()
    except Exception:
        return "無法取得課綱內容，請依循一般台灣教育標準命題。"

def generate_question(api_key: str, model_name: str, edu_level: str, topic: str, difficulty: str, question_type: str, is_reroll: bool = False, current_question: str = "", current_code: str = "", question_index: int = 1) -> dict:
    client = genai.Client(api_key=api_key)
    
    syllabus_text = ""
    if not is_reroll and topic:
        syllabus_text = fetch_syllabus_context(client, model_name, edu_level, topic)
        
    seed = random.randint(10000, 99999)
    
    base_rules = f"""
    【⚠️ 極度重要：JSON、LaTeX 與 Python 繪圖複合規範】
    1. 課綱對齊：出題必須嚴格符合台灣「108課綱」【{edu_level}】該學習階段的認知歷程。以下為本單元課綱重點參考：
       {syllabus_text}
    2. JSON 跳脫：所有的 LaTeX 語法反斜線「必須雙重跳脫」！例如：\\\\triangle。
    3. LaTeX 包覆：所有的數學符號、方程式，絕對必須用 $ 符號包覆起來，否則網頁無法渲染！
    4. 【考卷印刷視覺規範】：所有的繪圖絕對禁止使用灰色或彩色填滿！一律「純白底、純黑線」。
    5. 【⚠️ Markdown 刪除線防呆】：若要表示分數或數字範圍，【絕對使用全形波浪號「～」或連字號「-」】，嚴禁使用半形波浪號「~」。
    6. 【⚠️ 隨機與多樣性防呆】：這是本試卷的第 {question_index} 題 (亂數種子: {seed})。請確保與其他題目有「完全不同」的數字配置、圖形旋轉角度或考點，嚴禁產出雷同的題目！
    7. 【⚠️ 線段與圓弧符號明確區分】：
       - 若表示「線段」(如線段AB)，請正常使用 \\\\overline{{AB}}。
       - 若表示「圓弧」(如弧AB)，絕對禁止使用 \\\\overparen 或 \\\\wideparen！請一律替換為 \\\\overset{{\\\\frown}}{{AB}}，這是唯一能讓網頁與 Word 雙端皆正確顯示的語法。
    8. 【⚠️ 幾何交點絕對準確防呆】：如果你出的圖形涉及「兩線相交」(如圓內兩弦相交、對角線交於 P 點)，先在程式碼中定義 P 點座標（例如 P = np.array([2, 3])），然後透過向量加減法算出 A, B, C, D 四個端點（例如 A = P + [dist, 0]），確保線段「物理上」絕對通過 P 點。嚴禁隨機猜測座標！
    9. 【⚠️ 畫布完美滿版裁切防呆】：只要有繪圖，請「務必」精確算出所有點與圓形半徑的最小與最大 x, y 值，並加上 20% 的緩衝範圍，手動設定 `ax.set_xlim` 與 `ax.set_ylim`，絕對不准讓圖形被切斷！
    """
    
    prompt = ""
    
    if is_reroll:
        prompt = f"""
        你是一位國中數學老師。請你完全保留原本的題型架構與幾何形狀，但是換成另一組合理的整數數字。
        重新計算正確答案，並修改對應的 Python 程式碼座標。
        舊題目：{current_question}
        舊程式碼：{current_code}
        {base_rules}
        請回傳包含 "question_text" 與 "python_code" 的 JSON。
        """
    else:
        if question_type == "一般幾何 (平面/複合圖形)":
            prompt = f"""
            請根據主題：【{topic}】，生成一道【{difficulty}】難度的幾何題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、四個選項與解析。文字中若出現「如圖」，則必須給出 python_code。
            2. "python_code": 
               - 使用 ax.set_aspect('equal') 與 ax.axis('off')。
               - 存為 temp_diagram.png。
            """
        elif question_type == "立體圖形三視圖 (積木堆疊)":
            target_view = random.choice(["前視圖", "上視圖", "右視圖"])
            h_matrix = f"[[{random.randint(0,3)}, {random.randint(0,3)}, {random.randint(0,2)}], " \
                       f"[{random.randint(0,3)}, {random.randint(1,3)}, {random.randint(0,3)}], " \
                       f"[{random.randint(0,2)}, {random.randint(0,3)}, {random.randint(0,2)}]]"
            
            prompt = f"""
            請生成一道【{difficulty}】難度的「立體積木三視圖」選擇題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 
               - 題目指定測驗：【{target_view}】！選項排版必須是 3x3 矩陣，使用全形 ⬛ 與 ⬜。每一列結束務必加上 `<br>`。
            2. "python_code": 
               - 請完全照抄：heights = np.array({h_matrix})
               - 加上：`ax.set_box_aspect((1, 1, 1))`
               - 積木必須是純白底黑線：`ax.voxels(cubes, facecolors='white', edgecolors='black', shade=False)`
               - 使用 ax.view_init(elev=30, azim=-45)。隱藏座標軸。存為 temp_diagram.png。
            """
        elif question_type == "立體圖形展開圖 (圓柱/圓錐/角柱)":
            prompt = f"""
            你是一位專業的數學老師。請根據主題：【{topic}】，生成一道【{difficulty}】難度的「立體圖形展開圖」幾何題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、四個選項與解析。
            2. "python_code": 繪製該圖形的展開圖。
               - 角柱展開圖請確保多邊形完美貼合邊緣。圓錐請確保底圓接在弧線正上方。存為 temp_diagram.png。
            """
        elif question_type == "統計圖表 (折線圖/圓餅圖/長條圖/直方圖)":
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的統計圖表題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、選項與解析。
            2. "python_code": 
               - 圖表的標題、X軸標籤、Y軸標籤、圖例，全部必須使用繁體中文。
               - 圖表背景強制全白，不可有灰階填色。直方圖長條必須緊密相連 (width=組距)。存為 temp_diagram.png。
            """
        elif question_type == "一元一次不等式圖解 (數線)":
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的測驗題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 題目明確問：「求此不等式的解為何？」四個選項必須是純文字的數學範圍。
            2. "python_code": 
               - 請絕對照抄以下畫法，不准用 ax.axhline，利用 spines 作為唯一數線：
                 ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
                 ax.spines['left'].set_visible(False); ax.spines['bottom'].set_position('zero')
                 ax.get_yaxis().set_visible(False)
               - 存為 temp_diagram.png。
            """
        elif question_type == "會考非選素養題 (情境+兩小題)":
            prompt = f"""
            任務說明：請根據指定的概念【{topic}】，設計一道符合台灣教育會考風格的非選擇題。
            {base_rules}
            出題核心特徵：
            1. 情境設計原則：完整生活場景鋪陳(5行以上)，建立完整故事背景。融入時事科技趨勢。
            2. 題目結構：固定兩小題設計。
            3. 解題自由度設計：絕對不預設變數(不寫「設x為...」)，不直接提示解法。
            請嚴格回傳 JSON 格式：
            1. "question_text": 
               必須包含以下三個 Markdown 標題段落：
               ### 題目情境與問題
               ### 自我檢核清單
               ### 簡要解答與評分指引
            2. "python_code": 回傳空字串 ""。
            """
        else: 
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的計算題。
            {base_rules}
            【⚠️ 嚴格禁止圖文不符】：這是純文字計算題，所以題目文字中「絕對禁止」出現「如圖」、「右圖」等字眼！
            請回傳 JSON：
            1. "question_text": 包含純文字題目、四個選項與詳解。
            2. "python_code": 絕對回傳空字串 ""。
            """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4, 
                response_mime_type="application/json"
            )
        )
        
        tick3 = chr(96) * 3
        raw_text = response.text.strip()
        
        if raw_text.startswith(tick3 + "json"): raw_text = raw_text[7:]
        elif raw_text.startswith(tick3): raw_text = raw_text[3:]
        if raw_text.endswith(tick3): raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            repaired_text = re.sub(r'(?<!\\)\\(?=[a-zA-Z])', r'\\\\', raw_text)
            try: result = json.loads(repaired_text)
            except Exception as e: return {"question_text": "題目解析失敗 (特殊符號無法辨識)，請點擊【換一題】重試。", "python_code": ""}
                
        return result
    except Exception as e:
        return {"question_text": f"伺服器連線異常 ({e})，請重試。", "python_code": ""}