# 檔案 2：api_handler.py (已加入：圖文不符防呆、畫布裁切防呆)
import json
import random
import re
from google import genai
from google.genai import types

def fetch_syllabus_context(client, model_name, edu_level, topic):
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

def generate_question(api_key: str, model_name: str, edu_level: str, topic: str, difficulty: str, question_type: str, is_reroll: bool = False, current_question: str = "", current_code: str = "") -> dict:
    client = genai.Client(api_key=api_key)
    
    syllabus_text = ""
    if not is_reroll and topic:
        syllabus_text = fetch_syllabus_context(client, model_name, edu_level, topic)
    
    base_rules = f"""
    【⚠️ 極度重要：JSON、LaTeX 與 Python 繪圖複合規範】
    1. 課綱對齊：出題必須嚴格符合台灣「108課綱」【{edu_level}】該學習階段的認知歷程。以下為本單元課綱重點參考：
       {syllabus_text}
    2. JSON 跳脫：所有的 LaTeX 語法反斜線「必須雙重跳脫」！例如：\\\\triangle。
    3. LaTeX 包覆：所有的數學符號、方程式，絕對必須用 $ 符號包覆起來，否則網頁無法渲染！
    4. 【考卷印刷視覺規範】：所有的繪圖絕對禁止使用灰色或彩色填滿！一律「純白底、純黑線」。
    5. 【⚠️ Markdown 刪除線防呆】：若要表示分數或數字範圍，【絕對使用全形波浪號「～」或連字號「-」】（例如 50～60 或 50-60），嚴禁使用半形波浪號「~」。
    6. 多樣性要求：請確保題型與圖形的多樣性，若為四邊形單元，請隨機考慮梯形、箏形、菱形等不同圖形。
    7. 【⚠️ 線段與圓弧符號明確區分】：
       - 若表示「線段」(如線段AB)，請正常使用 \\\\overline{{AB}}。
       - 若表示「圓弧」(如弧AB)，絕對禁止使用 \\\\overparen 或 \\\\wideparen！請一律替換為 \\\\overset{{\\\\frown}}{{AB}}，這是唯一共通正確語法。
    8. 【⚠️ 無圖防呆】：如果你的題目文字中出現「如圖」、「右圖」、「如圖所示」等字眼，你「絕對必須」在 python_code 產生對應的圖形程式碼！
    9. 【⚠️ 畫布邊界防呆】：繪製圖形時，務必確保 set_xlim 與 set_ylim 足夠大，能夠完美包覆所有的幾何形狀與「頂點文字標籤(A, B, C)」，多留 20% 空白，絕對不可讓圖形超出邊界被裁切！
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
            1. "question_text": 包含題目、四個選項與解析。
            2. "python_code": 
               - 使用 ax.set_aspect('equal') 與 ax.axis('off')。
               - 【⚠️ 直角記號絕對防呆】：必須照抄以下向量邏輯：
                 u = (A - D) / np.linalg.norm(A - D); v = (C - D) / np.linalg.norm(C - D)
                 p1 = D + 0.5 * u; p2 = p1 + 0.5 * v; p3 = D + 0.5 * v
                 ax.plot([p1[0], p2[0], p3[0]], [p1[1], p2[1], p3[1]], 'k-', lw=1.5)
               - 存為 temp_diagram.png (bbox_inches='tight')。
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
               - 題目指定測驗：【{target_view}】！
               - 題目問：「如圖為正方體堆疊的立體圖形，請判斷其【{target_view}】為何？」
               - 【⚠️ 選項排版絕對防呆】：四個選項必須是完美的 3x3 矩陣。請「絕對」使用全形 ⬛ 與 ⬜。每一列結束務必加上 `<br>`。
            2. "python_code": 
               - 【⚠️ 答案同步防呆】：請完全照抄：
                 heights = np.array({h_matrix})
                 cubes = np.zeros((3, 3, 3), dtype=bool)
                 for x in range(3):
                     for y in range(3):
                         for z in range(heights[x, y]):
                             cubes[x, y, z] = True
               - 【⚠️ 純黑白防呆】：繪圖時「必須」加上這行：`ax.set_box_aspect((1, 1, 1))`
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
               - 【⚠️ 角柱展開圖防呆演算法】：AI你不會算旋轉，請【絕對照抄】這段演算法畫角柱：
                 N = 5 # 依照題目多邊形邊數修改(如3,4,5,6)
                 a = 2; h = 5
                 for i in range(N): ax.add_patch(Rectangle((i*a, 0), a, h, fc='white', ec='black', lw=1.5))
                 R = a / (2 * np.sin(np.pi/N)); apothem = a / (2 * np.tan(np.pi/N))
                 ax.add_patch(RegularPolygon((a/2, -apothem), numVertices=N, radius=R, orientation=np.pi/N, fc='white', ec='black', lw=1.5))
                 ax.add_patch(RegularPolygon((a/2, h + apothem), numVertices=N, radius=R, orientation=(np.pi/N if N%2==0 else np.pi/N + np.pi), fc='white', ec='black', lw=1.5))
               - 圓錐請確保底圓接在弧線正上方。存為 temp_diagram.png。
            """
        elif question_type == "統計圖表 (折線圖/圓餅圖/長條圖/直方圖)":
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的統計圖表題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、選項與解析。
            2. "python_code": 
               - 【⚠️ 繁體中文防呆】：圖表的標題、X軸標籤、Y軸標籤、圖例，全部必須使用繁體中文。
               - 圖表背景強制全白，不可有灰階填色。直方圖長條必須緊密相連 (width=組距)。存為 temp_diagram.png。
            """
        elif question_type == "一元一次不等式圖解 (數線)":
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的測驗題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 題目明確問：「求此不等式的解為何？」四個選項必須是純文字的數學範圍。
            2. "python_code": 
               - 【⚠️ 完美單一數線防呆】：請絕對照抄以下畫法，不准用 ax.axhline：
                 ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
                 ax.spines['left'].set_visible(False); ax.spines['bottom'].set_position('zero')
                 ax.get_yaxis().set_visible(False)
                 ax.set_xlim(ans - 6, ans + 6)
                 ax.set_xticks(np.arange(ans-5, ans+6, 1))
                 ax.plot([ans, ans], [0, 0.5], 'k-', lw=1.5)
                 ax.annotate('', xy=(x_end, 0.5), xytext=(ans, 0.5), arrowprops=dict(arrowstyle='->', lw=1.5))
                 ax.plot(ans, 0, marker='o', markersize=8, markerfacecolor='black', markeredgecolor='black', zorder=5)
                 ax.set_ylim(-0.5, 1); ax.margins(0.15)
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
        else: # 純文字計算題
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的計算題。
            {base_rules}
            【⚠️ 嚴格禁止圖文不符】：這是純文字計算題，所以題目文字中「絕對禁止」出現「如圖」、「右圖」、「下圖」等依賴圖形的字眼！
            請回傳 JSON：
            1. "question_text": 包含純文字題目、四個選項與詳解。
            2. "python_code": 絕對回傳空字串 ""。
            """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3, 
                response_mime_type="application/json"
            )
        )
        
        tick3 = chr(96) * 3
        raw_text = response.text.strip()
        
        if raw_text.startswith(tick3 + "json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith(tick3):
            raw_text = raw_text[3:]
        if raw_text.endswith(tick3):
            raw_text = raw_text[:-3]
            
        raw_text = raw_text.strip()

        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            repaired_text = re.sub(r'(?<!\\)\\(?=[a-zA-Z])', r'\\\\', raw_text)
            try:
                result = json.loads(repaired_text)
            except Exception as e:
                print(f"JSON 二次修復失敗: {e}")
                return {"question_text": "題目解析失敗 (特殊符號無法辨識)，請點擊【換一題】重試。", "python_code": ""}
                
        return result
        
    except Exception as e:
        print(f"API 呼叫失敗: {e}")
        return {"question_text": f"伺服器連線異常 ({e})，請重試。", "python_code": ""}