# 檔案 2：api_handler.py
import json
import random
import re
import time  # 🚀 新增：處理 429 重試等待
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
    10. 【🚀 換行與排版防呆】：
       - 題目本文結束後，四個選項 (A) (B) (C) (D) 必須「各自獨立換行」顯示，不可連在同一行。
       - 「解析」必須與選項之間空一行，且必須以「詳解：」或「解析：」開頭。
       - 表示角度時，一律使用 LaTeX 語法（例如：$45^\\circ$），絕對嚴禁使用純文字的全形符號 ∘。
    """
    
    prompt = ""
    if is_reroll:
        prompt = f"你是一位國中數學老師。請你完全保留原本的題型架構與幾何形狀，但是換成另一組合理的整數數字。重新計算正確答案，並修改對應的 Python 程式碼座標。\n舊題目：{current_question}\n舊程式碼：{current_code}\n{base_rules}\n請回傳包含 'question_text' 與 'python_code' 的 JSON。"
    else:
        if question_type == "一般幾何 (平面/複合圖形)":
            prompt = f"請根據主題：【{topic}】，生成一道【{difficulty}】難度的幾何題。\n{base_rules}\n請回傳 JSON：1. 'question_text': 包含題目、四個選項與解析。文字中若出現「如圖」，則必須給出 python_code。2. 'python_code': 使用 ax.set_aspect('equal') 與 ax.axis('off')，存為 temp_diagram.png。"
        elif question_type == "立體圖形三視圖 (積木堆疊)":
            target_view = random.choice(["前視圖", "上視圖", "右視圖"])
            h_matrix = f"[[{random.randint(0,3)}, {random.randint(0,3)}, {random.randint(0,2)}], [{random.randint(0,3)}, {random.randint(1,3)}, {random.randint(0,3)}], [{random.randint(0,2)}, {random.randint(0,3)}, {random.randint(0,2)}]]"
            prompt = f"請生成一道【{difficulty}】難度的「立體積木三視圖」選擇題。\n{base_rules}\n請回傳 JSON：1. 'question_text': 題目指定測驗：【{target_view}】！選項排版必須是 3x3 矩陣，使用全形 ⬛ 與 ⬜。每一列結束務必加上 <br>。2. 'python_code': 請完全照抄 heights = np.array({h_matrix})；加上 ax.set_box_aspect((1, 1, 1))；積木必須純白底黑線；存為 temp_diagram.png。"
        elif question_type == "立體圖形展開圖 (圓柱/圓錐/角柱)":
            prompt = f"請根據主題：【{topic}】，生成一道【{difficulty}】難度的「立體圖形展開圖」幾何題。\n{base_rules}\n請回傳 JSON：1. 'question_text': 包含題目、四個選項與解析。2. 'python_code': 繪製該圖形的展開圖，存為 temp_diagram.png。"
        elif question_type == "統計圖表 (折線圖/圓餅圖/長條圖/直方圖)":
            prompt = f"請生成一道【{difficulty}】難度，主題為【{topic}】的統計圖表題。\n{base_rules}\n請回傳 JSON：1. 'question_text': 包含題目、選項與解析。2. 'python_code': 標題與軸標籤須為繁體中文，圖表背景強制全白，存為 temp_diagram.png。"
        elif question_type == "一元一次不等式圖解 (數線)":
            prompt = f"請生成一道【{difficulty}】難度，主題為【{topic}】的測驗題。\n{base_rules}\n請回傳 JSON：1. 'question_text': 題目問「求此不等式的解為何？」選項為純文字範圍。2. 'python_code': 利用 spines 作為唯一數線並存為 temp_diagram.png。"
        elif question_type == "會考非選素養題 (情境+兩小題)":
            prompt = f"請根據主題：【{topic}】，設計一道符合台灣教育會考風格的非選擇題。\n{base_rules}\n1. 情境鋪陳 5 行以上。2. 固定兩小題。3. 不預設變數。\n請回傳 JSON：1. 'question_text': 包含 ### 題目情境、### 自我檢核、### 簡要解答。2. 'python_code': 空字串。"
        else: 
            prompt = f"請生成一道【{difficulty}】難度，主題為【{topic}】的計算題。\n{base_rules}\n【⚠️ 禁止圖文不符】：文字禁止出現「如圖」字眼。\n請回傳 JSON：1. 'question_text': 包含純文字題目、選項與詳解。2. 'python_code': 空字串。"

    # 🚀 API 呼叫的自動重試與異常處理機制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4, response_mime_type="application/json")
            )
            
            tick3 = chr(96) * 3
            raw_text = response.text.strip()
            if raw_text.startswith(tick3 + "json"): raw_text = raw_text[7:]
            elif raw_text.startswith(tick3): raw_text = raw_text[3:]
            if raw_text.endswith(tick3): raw_text = raw_text[:-3]
            
            # 🚀 終極清洗：將 AI 產出的「字面 \n」轉為真正的換行符
            raw_text = raw_text.replace("\\n", "\n").strip()

            try:
                result = json.loads(raw_text)
            except json.JSONDecodeError:
                repaired_text = re.sub(r'(?<!\\)\\(?=[a-zA-Z])', r'\\\\', raw_text)
                try: result = json.loads(repaired_text)
                except Exception: return {"question_text": "題目解析失敗 (符號無法辨識)，請重新生成。", "python_code": ""}
            return result

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(6 + attempt * 2) # 暫停重試
                    continue 
                else:
                    return {"question_text": "🚨 伺服器連續拒絕連線。若持續發生，代表已達「每日額度上限」，請更換 API Key！", "python_code": ""}
            return {"question_text": f"伺服器連線異常 ({error_msg})，請重試。", "python_code": ""}