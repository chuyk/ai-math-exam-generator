# 檔案 1：plot_utils.py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, RegularPolygon, Wedge, Circle, Arc
import matplotlib.ticker as ticker  # 🚀 新增 ticker 用來清洗醜醜的刻度
import numpy as np
import math
import os
from matplotlib import font_manager

# 🚀 終極中文字體防禦：強制綁定專案目錄下的 font.ttf
FONT_PATH = 'font.ttf'

def setup_chinese_font():
    if os.path.exists(FONT_PATH):
        try:
            font_manager.fontManager.addfont(FONT_PATH)
            prop = font_manager.FontProperties(fname=FONT_PATH)
            plt.rcParams['font.family'] = prop.get_name()
            print("✅ 成功載入本地字體: font.ttf")
        except Exception as e:
            print(f"⚠️ 載入 font.ttf 失敗: {e}")
    else:
        print("⚠️ 找不到 font.ttf，請確認已上傳至 app.py 同目錄！")
        
    plt.rcParams['axes.unicode_minus'] = False

# 執行字體初始化
setup_chinese_font()
plt.rcParams.update({'font.size': 16})
mpl.rcParams['svg.fonttype'] = 'none'

def draw_dimension(ax, p1, p2, text, offset=0.5, mode='line', invert=False):
    p1, p2 = np.array(p1), np.array(p2)
    vec = p2 - p1
    length = np.linalg.norm(vec)
    if length == 0: return
    u = vec / length
    n = np.array([-u[1], u[0]])
    if invert: n = -n
    start = p1 + n * offset
    end = p2 + n * offset
    ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='<->', lw=1.5))
    mid = (start + end) / 2
    text_pos = mid + n * 0.3
    ax.text(text_pos[0], text_pos[1], f'${text}$', ha='center', va='center', fontsize=16)

def draw_grid_option(ax, title, active_indices):
    ax.set_xlim(-0.2, 3.2)
    ax.set_ylim(-0.2, 3.2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    for i in range(1, 10):
        col = (i - 1) % 3
        row = 2 - (i - 1) // 3
        rect_bg = patches.Rectangle((col, row), 1, 1, linewidth=0.5, edgecolor='lightgray', facecolor='none')
        ax.add_patch(rect_bg)
        
    for i in active_indices:
        col = (i - 1) % 3
        row = 2 - (i - 1) // 3
        rect_solid = patches.Rectangle((col, row), 1, 1, linewidth=2.0, edgecolor='black', facecolor='white', hatch='////')
        ax.add_patch(rect_solid)
        
    ax.text(1.5, -0.4, title, ha='center', va='center', fontsize=18)

def draw_math_axes(ax):
    """
    提供給 AI 呼叫的基礎設定。
    注意：我們不在這裡畫箭頭，而是交給後處理 (post-processing) 來確保箭頭永遠在最終邊界！
    """
    ax.set_axis_on() 
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(True)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_position('zero')
    ax.spines['bottom'].set_position('zero')
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.spines['left'].set_color('black')
    ax.spines['bottom'].set_color('black')

def execute_ai_plot_code(python_code: str, output_filename: str) -> bool:
    if python_code is None or not isinstance(python_code, str) or python_code.strip() == "":
        return False
        
    env = {
        "plt": plt, "mpl": mpl, "patches": patches, "Rectangle": Rectangle,
        "RegularPolygon": RegularPolygon, "Wedge": Wedge, "Circle": Circle,
        "Arc": Arc, "np": np, "math": math, "draw_dimension": draw_dimension,
        "draw_grid_option": draw_grid_option,
        "draw_math_axes": draw_math_axes
    }
    
    font_injection = f"""
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os
font_file = r'{os.path.abspath(FONT_PATH)}'
if os.path.exists(font_file):
    try:
        fm.fontManager.addfont(font_file)
        prop = fm.FontProperties(fname=font_file)
        plt.rcParams['font.family'] = prop.get_name()
    except: pass
plt.rcParams['axes.unicode_minus'] = False
"""
    code_to_run = font_injection + python_code.replace("temp_diagram.png", output_filename)
    
    try:
        fig, ax = plt.subplots(figsize=(6, 6))
        env['fig'] = fig
        env['ax'] = ax
        
        exec(code_to_run, env)
        
        # 🚀 終極後處理魔法：等 AI 畫完後，系統強制接管畫布收尾！
        is_math_axes = False
        try:
            pos_b = ax.spines['bottom'].get_position()
            pos_l = ax.spines['left'].get_position()
            if pos_b in ['zero', ('data', 0)] or pos_l in ['zero', ('data', 0)]:
                is_math_axes = True
        except: pass
        
        if is_math_axes:
            # 1. 消除原點重疊的 0 魔法：自訂刻度格式
            def clean_ticks(x, pos):
                if abs(x) < 1e-7: return '' # 遇到 0 絕對隱藏！
                if float(x).is_integer(): return str(int(x)) # 把 2.0 變 2
                return str(x)
                
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(clean_ticks))
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(clean_ticks))
            
            # 2. 獲取「AI 畫完所有幾何圖形後」的最終邊界
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            
            # 強制向外延伸一點點 (5%)，讓箭頭有空間，不會跟最後一個數字擠在一起
            x_margin = (xmax - xmin) * 0.05
            y_margin = (ymax - ymin) * 0.05
            ax.set_xlim(xmin, xmax + x_margin)
            ax.set_ylim(ymin, ymax + y_margin)
            
            # 重新獲取延伸後的邊界
            xmax_new = ax.get_xlim()[1]
            ymax_new = ax.get_ylim()[1]
            
            # 3. 釘死箭頭：在最最末端畫上完美的實體箭頭 (zorder=100 保證在最上層)
            ax.plot(xmax_new, 0, marker='>', color='black', markersize=8, clip_on=False, zorder=100)
            ax.plot(0, ymax_new, marker='^', color='black', markersize=8, clip_on=False, zorder=100)
            
            # 4. 釘死標籤：在箭頭旁邊補上斜體的 x 與 y
            ax.text(xmax_new + x_margin*0.5, 0, '$x$', ha='left', va='center', fontsize=18)
            ax.text(0, ymax_new + y_margin*0.5, '$y$', ha='center', va='bottom', fontsize=18)
            
            # 5. 補上完美的斜體 O (Origin) 於原點左下方
            ax.annotate('$O$', xy=(0, 0), xytext=(-12, -12), textcoords='offset points', fontsize=18, ha='right', va='top')

        if not os.path.exists(output_filename):
            for artist in ax.get_children():
                artist.set_clip_on(False)
            plt.savefig(output_filename, dpi=300, bbox_inches='tight', pad_inches=0.25, transparent=True)
            
        plt.close('all')
        return True
    except Exception as e:
        print(f"⚠️ 繪圖程式碼執行錯誤: {e}")
        plt.close('all')
        return False

def clean_up_temp_images(image_list: list):
    for img in image_list:
        if img and os.path.exists(img):
            try: os.remove(img)
            except Exception: pass