import json
import random
from google import genai
from google.genai import types

def generate_question(api_key: str, model_name: str, edu_level: str, topic: str, difficulty: str, question_type: str, is_reroll: bool = False, current_question: str = "", current_code: str = "") -> dict:
    client = genai.Client(api_key=api_key)
    
    base_rules = f"""
    【⚠️ 極度重要：JSON、LaTeX 與 Python 繪圖複合規範】
    1. 身分設定：你是一位台灣【{edu_level}】專業數學老師。出題必須嚴格符合台灣「108課綱」該學習階段的認知歷程與名詞。
    2. 【⚠️ 題型多樣性防呆】：絕對不可一直重複相同的子概念或圖形！例如單元是「四邊形」，請務必隨機涵蓋「箏形、梯形、菱形、矩形、平行四邊形」等不同變化，增添考卷豐富度。
    3. JSON 跳脫：所有的 LaTeX 語法反斜線「必須雙重跳脫」！例如：\\\\triangle。
    4. 【⚠️ LaTeX 渲染嚴格防呆】：所有的數學符號必須用 $ 包覆，且 $ 與數學式之間「絕對不可以有任何空白」！正確範例：$\\overline{{AB}}$；錯誤範例：$ \\overline{{AB}} $。
    5. 【考卷印刷視覺規範】：所有的繪圖絕對禁止使用灰色或彩色填滿！一律「純白底、純黑線」。
    6. 【⚠️ Markdown 刪除線防呆】：若要表示分數或數字範圍，【絕對使用全形波浪號「～」或連字號「-」】，嚴禁使用半形波浪號「~」。
    """
    
    prompt = ""
    
    if is_reroll:
        prompt = f"""
        {base_rules}
        你是一位國中數學老師。請你完全保留原本的題型架構與幾何形狀，但是換成另一組合理的整數數字。
        重新計算正確答案，並修改對應的 Python 程式碼座標。
        舊題目：{current_question}
        舊程式碼：{current_code}
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
            h_matrix = f"[[{random.randint(0,3)}, {random.randint(0,3)}, {random.randint(0,2)}], [{random.randint(0,3)}, {random.randint(1,3)}, {random.randint(0,3)}], [{random.randint(0,2)}, {random.randint(0,3)}, {random.randint(0,2)}]]"
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
        elif question_type == "立體圖形展開圖 (圓柱/圓錐/角柱)":
            prompt = f"""
            你是一位專業的數學老師。請根據主題：【{topic}】，生成一道【{difficulty}】難度的「立體圖形展開圖」幾何題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、四個選項與解析。
            2. "python_code": 繪製該圖形的展開圖。
               - 【⚠️ 角柱展開圖防呆演算法】：AI你不會算旋轉，請【絕對照抄】這段演算法畫角柱，它保證多邊形 100% 完美貼合矩形邊緣(以 N角柱為例)：
                 N = 5 # 依照題目多邊形邊數修改(如3,4,5,6)
                 a = 2; h = 5
                 for i in range(N): ax.add_patch(Rectangle((i*a, 0), a, h, fc='white', ec='black', lw=1.5))
                 R = a / (2 * np.sin(np.pi/N)); apothem = a / (2 * np.tan(np.pi/N))
                 ax.add_patch(RegularPolygon((a/2, -apothem), numVertices=N, radius=R, orientation=np.pi/N, fc='white', ec='black', lw=1.5))
                 ax.add_patch(RegularPolygon((a/2, h + apothem), numVertices=N, radius=R, orientation=(np.pi/N if N%2==0 else np.pi/N + np.pi), fc='white', ec='black', lw=1.5))
               - 【⚠️ 圓錐防呆】：底圓必須接在「弧線」正上方！請絕對照抄這段程式：
                 L = 10; r = 3; theta = 360 * (r / L)
                 ax.add_patch(Wedge((0,0), L, 90 - theta/2, 90 + theta/2, fc='white', ec='black', lw=1.5))
                 ax.add_patch(Circle((0, L + r), r, fc='white', ec='black', lw=1.5))
               - 使用 ax.set_aspect('equal') 與 ax.axis('off')。務必使用 ax.set_xlim 與 ax.set_ylim 包含全圖。
               - 存為 temp_diagram.png (bbox_inches='tight')。
            """
        elif question_type == "統計圖表 (折線圖/圓餅圖/長條圖/直方圖)":
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的統計圖表題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、選項與解析。
            2. "python_code": 
               - 【⚠️ 繁體中文防呆】：圖表的標題、X軸標籤、Y軸標籤、圖例，全部必須使用繁體中文。
               - 圖表背景強制全白，不可有灰階填色。直方圖長條必須緊密相連 (width=組距)。
               - 存為 temp_diagram.png (bbox_inches='tight')。
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
                 ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
                 ax.spines['left'].set_visible(False); ax.spines['bottom'].set_position('zero')
                 ax.get_yaxis().set_visible(False)
                 ax.set_xlim(ans - 6, ans + 6)
                 ax.set_xticks(np.arange(ans-5, ans+6, 1))
                 ax.plot([ans, ans], [0, 0.5], 'k-', lw=1.5)
                 ax.annotate('', xy=(x_end, 0.5), xytext=(ans, 0.5), arrowprops=dict(arrowstyle='->', lw=1.5))
                 ax.plot(ans, 0, marker='o', markersize=8, markerfacecolor='black', markeredgecolor='black', zorder=5)
                 ax.set_ylim(-0.5, 1); ax.margins(0.15)
               - 存為 temp_diagram.png (bbox_inches='tight')。
            """
        elif question_type == "會考非選素養題 (情境+兩小題)":
            prompt = f"""
            任務說明：請根據指定的概念【{topic}】，設計一道符合台灣教育會考風格的非選擇題。
            {base_rules}
            出題核心特徵：
            1. 情境設計原則：完整生活場景鋪陳(5行以上的文字描述)，建立完整故事背景。融入當前熱門時事科技趨勢。自然融入數學，素養導向。
            2. 題目結構：固定兩小題設計。第一小題考核心概念理解；第二小題為挑戰應用題。
            3. 解題自由度設計：絕對不預設變數(不寫「設x為...」)，不直接提示解法，開放多元解法。
            請嚴格回傳 JSON 格式：
            1. "question_text": 
               必須包含以下三個 Markdown 標題段落：
               ### 題目情境與問題
               ### 自我檢核清單
               ### 簡要解答與評分指引
            2. "python_code": 回傳空字串 ""。
            """
        else: # "純文字計算題 (無插圖)"
            prompt = f"""
            請生成一道【{difficulty}】難度，主題為【{topic}】的計算題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、四個選項與詳解。
            2. "python_code": 回傳空字串 ""。
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
        
        # 安全解析，不觸發引號問題
        raw_text = response.text.strip()
        bt = "`" * 3
        if raw_text.startswith(f"{bt}json"): 
            raw_text = raw_text[7:]
        elif raw_text.startswith(bt): 
            raw_text = raw_text[3:]
        if raw_text.endswith(bt): 
            raw_text = raw_text[:-3]
            
        result = json.loads(raw_text.strip())
        return result
        
    except Exception as e:
        print(f"API 呼叫或 JSON 解析失敗: {e}")
        return {"question_text": f"題目生成失敗 ({e})，請點擊重試。", "python_code": ""}