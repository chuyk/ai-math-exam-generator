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
import urllib.request
from matplotlib import font_manager

# 確保基礎環境準備好字體檔案
FONT_PATH = 'NotoSansTC-Regular.ttf'
FONT_URL = 'https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansTC/NotoSansTC-Regular.ttf'

if not os.path.exists(FONT_PATH):
    try:
        print("正在下載 NotoSansTC 字體...")
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
    except Exception as e:
        print(f"⚠️ 字體下載失敗: {e}")

try:
    if os.path.exists(FONT_PATH):
        font_manager.fontManager.addfont(FONT_PATH)
        prop = font_manager.FontProperties(fname=FONT_PATH)
        plt.rcParams['font.family'] = prop.get_name()
except Exception:
    pass

plt.rcParams.update({'font.size': 16})
plt.rcParams['axes.unicode_minus'] = False
mpl.rcParams['svg.fonttype'] = 'none'

def draw_dimension(ax, p1, p2, text, offset=0.5, mode='line', invert=False):
    """給 AI 呼叫的尺寸標註專用輔助函式"""
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
    """
    🚀 三視圖專用：繪製包含淺色 3x3 底線與粗黑線實體的選項圖
    """
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
        rect_solid = patches.Rectangle((col, row), 1, 1, linewidth=2.5, edgecolor='black', facecolor='white')
        ax.add_patch(rect_solid)
        
    ax.text(1.5, -0.4, title, ha='center', va='center', fontsize=18)

def execute_ai_plot_code(python_code: str, output_filename: str) -> bool:
    if python_code is None or not isinstance(python_code, str) or python_code.strip() == "":
        return False
        
    env = {
        "plt": plt, "mpl": mpl, "patches": patches, "Rectangle": Rectangle,
        "RegularPolygon": RegularPolygon, "Wedge": Wedge, "Circle": Circle,
        "Arc": Arc, "np": np, "math": math, "draw_dimension": draw_dimension,
        "draw_grid_option": draw_grid_option
    }
    
    # 🚀 終極字體防禦：把字體載入邏輯「硬塞」進 AI 的程式碼最開頭，強迫它在自己的 scope 內執行
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