# 檔案 2：api_handler.py
import json
import random
import re
import time
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
    8. 【⚠️ 幾何交點絕對準確防呆】：如果你出的圖形涉及「兩線相交」，先在程式碼中定義 P 點座標，再算出其他端點確保線段通過 P 點。嚴禁隨機猜測座標！
    9. 【⚠️ 畫布完美滿版裁切防呆】：只要有繪圖，請「務必」設定 `ax.set_xlim` 與 `ax.set_ylim`，絕對不准讓圖形被切斷！
    10. 【🚀 換行與排版防呆】：
       - 題目本文結束後，四個選項 (A) (B) (C) (D) 必須「各自獨立換行」顯示，不可連在同一行。
       - 「解析」必須與選項之間空一行，且必須以「詳解：」或「解析：」開頭。
       - 表示角度時，一律使用 LaTeX 語法（例如：$45^\\circ$），絕對嚴禁使用 ∘。
    11. 【🚀 圖片排版定位 (非常重要)】：若題目文字中包含「如圖」，請「務必」在題目敘述結束後、選項 (A) 開始之前，獨立一行插入「[插入圖片]」這四個字！
    12. 【🛑 直角坐標系與防洩題規範】：
       - 若繪製 x 軸與 y 軸，正向「必須」有箭頭 (可使用 ax.annotate 畫出箭頭)。
       - 嚴禁在圖形上標示出交點的確切座標值或答案！
    13. 【⚠️ 繁體中文防呆 (最高原則)】：無論是哪種題型，圖形的幾何頂點說明、圖表的標題、X/Y軸標籤、圖例等，全部【必須】使用繁體中文。系統已內建中文支援，請大膽寫中文。
    14. 【⚠️ 三視圖平面圖絕對防呆】：只要題目或圖形要求畫出「前視圖」、「上視圖」或「右視圖」的平面圖形，【絕對禁止】自己用 Rectangle 拼湊！【必須】呼叫系統內建的 `draw_grid_option(ax, title, active_indices)` 函式，它會自動畫出包含 3x3 淺色底線與斜線網底的完美九宮格。
       - 例如畫出三個視圖的語法必須是：
         ax1 = fig.add_subplot(131); draw_grid_option(ax1, "前視圖", [1,4,7,8,9])
         ax2 = fig.add_subplot(132); draw_grid_option(ax2, "上視圖", [7,8,9])
         ax3 = fig.add_subplot(133); draw_grid_option(ax3, "右視圖", [3,6,7,8,9])
    """
    
    prompt = ""
    if is_reroll:
        prompt = f"你是一位國中數學老師。請你完全保留原本的題型架構與幾何形狀，但是換成另一組合理的整數數字。重新計算正確答案，並修改對應的 Python 程式碼座標。\n舊題目：{current_question}\n舊程式碼：{current_code}\n{base_rules}\n請回傳包含 'question_text' 與 'python_code' 的 JSON。"
    else:
        if question_type == "一般幾何 (平面/複合圖形)":
            prompt = f"請根據主題：【{topic}】，生成一道【{difficulty}】難度的幾何題。\n{base_rules}\n請回傳 JSON：1. 'question_text': 包含題目、四個選項與解析。文字中若出現「如圖」，則必須給出 python_code。2. 'python_code': 使用 ax.set_aspect('equal') 與 ax.axis('off')，存為 temp_diagram.png。"
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
               - 題目問：「如圖，請判斷該立體圖形的【{target_view}】為何？」
               - 因為選項 (A) (B) (C) (D) 已經繪製在圖片中了，所以在文字選項部分，請直接寫上：
                 (A) 如圖
                 (B) 如圖
                 (C) 如圖
                 (D) 如圖
               - 【⚠️ 空間推算防呆】：請精準推算正確的 {target_view}，並確保它存在於其中一個選項中！
            2. "python_code": 
               - 【⚠️ 絕對照抄繪圖架構】：系統已內建 `draw_grid_option` 函式。請完全照抄以下架構，【絕對禁止】自行撰寫繪製 2D 視圖的邏輯，僅修改 `active_indices` 陣列來佈局選項 (1為左上，9為右下)：
                 fig = plt.figure(figsize=(10, 5))
                 
                 # 左側畫立體主圖
                 ax_main = fig.add_subplot(121, projection='3d')
                 heights = np.array({h_matrix})
                 cubes = np.zeros((3, 3, 3), dtype=bool)
                 for x in range(3):
                     for y in range(3):
                         for z in range(heights[x, y]): cubes[x, y, z] = True
                 ax_main.voxels(cubes, facecolors='white', edgecolors='black', shade=False)
                 ax_main.set_box_aspect((1, 1, 1))
                 ax_main.view_init(elev=30, azim=-45)
                 ax_main.axis('off')
                 
                 # 右側畫選項 (強迫使用內建 3x3 九宮格繪圖函式)
                 ax_a = fig.add_subplot(243); draw_grid_option(ax_a, "(A)", [1, 2, 3, 5]) # 請修改陣列設計混淆選項
                 ax_b = fig.add_subplot(244); draw_grid_option(ax_b, "(B)", [4, 5, 6, 8]) # 請修改陣列設計混淆選項
                 ax_c = fig.add_subplot(247); draw_grid_option(ax_c, "(C)", [2, 4, 5, 6]) # 請修改陣列設計混淆選項
                 ax_d = fig.add_subplot(248); draw_grid_option(ax_d, "(D)", [7, 8, 9]) # 請修改陣列設計正確答案
                 
                 plt.subplots_adjust(wspace=0.1, hspace=0.3)
               - 存為 temp_diagram.png (bbox_inches='tight')。
            """
        elif question_type == "立體圖形展開圖 (圓柱/圓錐/角柱)":
            prompt = f"""
            你是一位專業的國中數學老師。請根據主題：【{topic}】，生成一道【{difficulty}】難度的「立體圖形展開圖」幾何題。
            {base_rules}
            請回傳 JSON：
            1. "question_text": 包含題目、四個選項與解析。
            2. "python_code": 繪製該圖形的展開圖。
               - 【⚠️ 角柱展開圖防呆演算法】：AI你不會算旋轉，請【絕對照抄】這段演算法畫角柱，它保證多邊形 100% 完美貼合矩形邊緣(以 N角柱為例)：
                 N = 5 # 依照題目多邊形邊數修改(如3,4,5,6)
                 a = 2; h = 5
                 for i in range(N): ax.add_patch(Rectangle((i*a, 0), a, h, fc='white', ec='black', lw=1.5))
                 R = a / (2 * np.sin(np.pi/N)); apothem = a / (2 * np.tan(np.pi/N))
                 # 下底 (完美貼合)
                 ax.add_patch(RegularPolygon((a/2, -apothem), numVertices=N, radius=R, orientation=np.pi/N, fc='white', ec='black', lw=1.5))
                 # 上底 (完美翻轉 180 度貼合)
                 ax.add_patch(RegularPolygon((a/2, h + apothem), numVertices=N, radius=R, orientation=(np.pi/N if N%2==0 else np.pi/N + np.pi), fc='white', ec='black', lw=1.5))
               - 【⚠️ 圓錐防呆】：底圓必須接在「弧線」正上方！請絕對照抄這段程式：
                 L = 10; r = 3; theta = 360 * (r / L)
                 # 扇形開口朝上 (弧線在上方)
                 ax.add_patch(Wedge((0,0), L, 90 - theta/2, 90 + theta/2, fc='white', ec='black', lw=1.5))
                 # 圓接在上方弧線的頂點
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
               - 四個選項必須是純文字的數學範圍（如 (A) $x > 3$）。數學式必須加上 $ 包覆。範圍隨機向右或向左。
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
                 ax.plot(ans, 0, marker='o', markersize=8, markerfacecolor='black', markeredgecolor='black', zorder=5) # 實心fc='black', 空心fc='white'
                 ax.set_ylim(-0.5, 1)
                 # 【⚠️ 圖片裁切防禦】：強制留白，確保箭頭不被切掉
                 ax.margins(0.15)
               - 存為 temp_diagram.png (bbox_inches='tight')。
            """
        elif question_type == "會考非選素養題 (情境+兩小題)":
            prompt = f"請根據主題：【{topic}】，設計一道符合台灣教育會考風格的非選擇題。\n{base_rules}\n1. 情境鋪陳 5 行以上。2. 固定兩小題。3. 不預設變數。\n請回傳 JSON：1. 'question_text': 包含 ### 題目情境、### 自我檢核、### 簡要解答。2. 'python_code': 空字串。"
        else: 
            prompt = f"請生成一道【{difficulty}】難度，主題為【{topic}】的計算題。\n{base_rules}\n【⚠️ 禁止圖文不符】：文字禁止出現「如圖」字眼。\n請回傳 JSON：1. 'question_text': 包含純文字題目、選項與詳解。2. 'python_code': 空字串。"

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
            raw_text = raw_text.strip()

            try:
                result = json.loads(raw_text)
            except json.JSONDecodeError:
                repaired_text = re.sub(r'(?<!\\)\\(?=[a-zA-Z])', r'\\\\', raw_text)
                try: 
                    result = json.loads(repaired_text)
                except Exception: 
                    return {"question_text": "題目解析失敗 (符號無法辨識)，請點擊【換一題】重試。", "python_code": ""}
            
            if "question_text" in result:
                result["question_text"] = result["question_text"].replace("\\n", "\n")

            return result

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(6 + attempt * 2) 
                    continue 
                else:
                    return {"question_text": "🚨 伺服器連續拒絕連線。若持續發生，代表已達「每日額度上限」，請更換 API Key！", "python_code": ""}
            return {"question_text": f"伺服器連線異常 ({error_msg})，請重試。", "python_code": ""}