import json
import random
from google import genai
from google.genai import types

def generate_question(api_key: str, model_name: str, topic: str, difficulty: str, question_type: str, is_reroll: bool = False, current_question: str = "", current_code: str = "") -> dict:
    """
    向 Google Gemini API 請求生成題目與繪圖程式碼。
    """
    client = genai.Client(api_key=api_key)
    
    base_rules = r"""
    【⚠️ 極度重要：JSON、LaTeX 與 Python 繪圖複合規範】
    1. JSON 跳脫：所有的 LaTeX 語法反斜線「必須雙重跳脫」！例如：\\triangle。
    2. LaTeX 包覆：所有的數學符號、方程式，絕對必須用 $ 符號包覆起來，否則網頁無法渲染！
    3. 【考卷印刷視覺規範】：所有的繪圖絕對禁止使用灰色或彩色填滿！一律「純白底、純黑線」。
    4. 【⚠️ Markdown 刪除線防呆】：若要表示分數或數字範圍，【絕對使用全形波浪號「～」或連字號「-」】（例如 50～60 或 50-60），嚴禁使用半形波浪號「~」，否則會觸發 Markdown 刪除線導致排版大亂！
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
               - 【⚠️ 圖片裁切防禦機制】：繪圖最後，請「絕對」加上以下三行，強迫系統重新計算邊界並留白，防止圓弧或圖形被卡斷：
                 ax.relim()
                 ax.autoscale_view()
                 ax.margins(0.15)
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
               - 【⚠️ AI 空間推算防呆】：請務必根據我提供的 heights 陣列，精準推算出正確的 {target_view} 畫面，並確保它存在於選項中！
               - 【⚠️ 選項排版絕對防呆】：四個選項必須是完美的 3x3 矩陣。請「絕對」使用全形 ⬛ 與 ⬜。每一列結束務必加上 `<br>`。例如："(A)<br>⬜⬜⬜<br>⬜⬛⬜<br>⬛⬛⬛"
            2. "python_code": 
               - 【⚠️ 答案同步與重力防呆】：絕對不可以使用 np.random！請完全照抄以下我給你的陣列（這是我給你的新題目數據）：
                 heights = np.array({h_matrix})
                 cubes = np.zeros((3, 3, 3), dtype=bool)
                 for x in range(3):
                     for y in range(3):
                         for z in range(heights[x, y]):
                             cubes[x, y, z] = True
               - 【⚠️ 正方體鎖定與純黑白防呆】：繪圖時「必須」加上這行：`ax.set_box_aspect((1, 1, 1))`
               - 積木必須是純白底黑線，絕對不可有灰階陰影！請絕對照抄這行畫積木：`ax.voxels(cubes, facecolors='white', edgecolors='black', shade=False)`
               - 使用 ax.view_init(elev=30, azim=-45)。隱藏座標軸。存為 temp_diagram.png (bbox_inches='tight')。
            """
        elif question_type == "一元一次不等式圖解 (數線)":
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的測驗題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 
               - 系統只配一張正確的圖作為解析，題目【絕對不可以】問「請選出正確的圖解」。
               - 題目明確問：「求此不等式的解為何？」
               - 四個選項必須是純文字的數學範圍（如 (A) $x > 3$）。數學式必須加上 $ 包覆。
            2. "python_code": 
               - 【⚠️ 完美單一數線防呆】：請絕對照抄以下畫法，不准用 ax.axhline，直接利用 spines 作為唯一數線：
                 ax.spines['top'].set_visible(False)
                 ax.spines['right'].set_visible(False)
                 ax.spines['left'].set_visible(False)
                 ax.spines['bottom'].set_position('zero')
                 ax.get_yaxis().set_visible(False)
                 # 【⚠️ 警告系統：不准亂縮放！強迫顯示完整的左右範圍！】
                 ax.set_xlim(ans - 6, ans + 6)
                 ax.set_xticks(np.arange(ans-5, ans+6, 1))
                 ax.plot([ans, ans], [0, 0.5], 'k-', lw=1.5) # 垂直線
                 # 若向右 x_end = ans + 4；若向左 x_end = ans - 4
                 ax.annotate('', xy=(x_end, 0.5), xytext=(ans, 0.5), arrowprops=dict(arrowstyle='->', lw=1.5))
                 ax.plot(ans, 0, marker='o', markersize=8, markerfacecolor='black', markeredgecolor='black', zorder=5)
                 ax.set_ylim(-0.5, 1)
                 # 【⚠️ 圖片裁切防禦】：強制留白
                 ax.margins(0.15)
               - 存為 temp_diagram.png (bbox_inches='tight')。
            """
        elif question_type == "會考非選素養題 (情境+兩小題)":
            prompt = f"""
            任務說明：你是專業的台灣國中教育會考數學科出題老師，請根據指定的概念【{topic}】，設計一道符合教育會考風格的非選擇題。
            {base_rules}
            出題核心特徵：
            1. 情境設計原則：完整生活場景鋪陳(5行以上的文字描述)，建立完整故事背景。融入當前熱門時事科技趨勢。自然融入數學，素養導向。
            2. 題目結構：固定兩小題設計。
               - 第一小題：考核心概念理解，避免直接問法，答案必須是整數。
               - 第二小題：具有挑戰性的應用題，需3-4個步驟思考，不超出國中範圍。
            3. 解題自由度設計：絕對不預設變數(不寫「設x為...」)，不直接提示解法，開放多元解法。
            請嚴格回傳 JSON 格式：
            1. "question_text": 
               必須包含以下三個 Markdown 標題段落：
               ### 題目情境與問題
               ### 自我檢核清單
               ### 簡要解答與評分指引
            2. "python_code": 回傳空字串 ""。
            """
        else:
            # 預設：純文字或其它類型
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的計算題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、四個選項與詳解。
            2. "python_code": 回傳空字串 ""。
            """

    # 為了確保系統穩定，強制要求 AI 回傳純 JSON 格式
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, # 降低隨機性，保證數學嚴謹
                response_mime_type="application/json"
            )
        )
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"API 呼叫或 JSON 解析失敗: {e}")
        return {"question_text": "題目生成失敗，請重試。", "python_code": ""}