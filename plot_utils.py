# 檔案 1：plot_utils.py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, RegularPolygon, Wedge, Circle, Arc
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
    🚀 給 AI 呼叫的標記函式。
    一旦 AI 呼叫了這個，系統就會在最後接管畫布，執行「無刻度完美坐標系」的後處理。
    """
    ax._is_math_axes = True

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
        
        # 🚀 終極後處理：接管數學坐標系的繪製
        if hasattr(ax, '_is_math_axes') and ax._is_math_axes:
            # 1. 強制喚醒坐標軸 (以防 AI 把它關了)，並隱藏上與右框線
            ax.set_axis_on()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(True)
            ax.spines['bottom'].set_visible(True)
            ax.spines['left'].set_position('zero')
            ax.spines['bottom'].set_position('zero')
            ax.spines['left'].set_linewidth(1.5)
            ax.spines['bottom'].set_linewidth(1.5)
            
            # 2. 🚀 徹底清除所有刻度與數字 (符合數學考卷標準)
            ax.set_xticks([])
            ax.set_yticks([])
            
            # 3. 獲取 AI 畫完圖形後的「最終邊界」
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            
            # 防呆：確保原點一定在畫面內
            if xmin >= 0: xmin = -1
            if xmax <= 0: xmax = 1
            if ymin >= 0: ymin = -1
            if ymax <= 0: ymax = 1
            
            # 4. 強制向外延伸 10%，預留箭頭與文字的完美空間
            x_margin = (xmax - xmin) * 0.1
            y_margin = (ymax - ymin) * 0.1
            ax.set_xlim(xmin - x_margin*0.2, xmax + x_margin)
            ax.set_ylim(ymin - y_margin*0.2, ymax + y_margin)
            
            xmax_new = ax.get_xlim()[1]
            ymax_new = ax.get_ylim()[1]
            
            # 5. 釘死箭頭：在真正的最邊界使用 plot 畫出標準黑箭頭
            ax.plot(xmax_new, 0, marker='>', color='black', markersize=8, clip_on=False, zorder=100)
            ax.plot(0, ymax_new, marker='^', color='black', markersize=8, clip_on=False, zorder=100)
            
            # 6. 釘死標籤：精準放置斜體的 x, y, O
            ax.text(xmax_new, -y_margin*0.2, '$x$', ha='center', va='top', fontsize=18, clip_on=False)
            ax.text(-x_margin*0.2, ymax_new, '$y$', ha='right', va='center', fontsize=18, clip_on=False)
            ax.text(-x_margin*0.2, -y_margin*0.2, '$O$', ha='right', va='top', fontsize=18, clip_on=False)

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