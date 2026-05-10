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
import matplotlib.font_manager as fm

# 🚀 繁體中文防呆：強制設定系統中文字體，解決字體變方塊的問題
chinese_fonts = ['Microsoft JhengHei', 'PingFang TC', 'Heiti TC', 'Taipei Sans TC Beta', 'Noto Sans CJK TC', 'SimHei', 'Arial Unicode MS']
valid_fonts = [f.name for f in fm.fontManager.ttflist]
found_fonts = [f for f in chinese_fonts if f in valid_fonts]
if found_fonts:
    plt.rcParams['font.sans-serif'] = found_fonts + plt.rcParams['font.sans-serif']
else:
    plt.rcParams['font.sans-serif'] = chinese_fonts + plt.rcParams['font.sans-serif']
plt.rcParams['axes.unicode_minus'] = False

mpl.rcParams['svg.fonttype'] = 'none'
plt.rcParams.update({'font.size': 18})

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

# 🚀 新增：內建給 AI 直接呼叫的三視圖選項繪製函式 (褚老師提供)
def draw_grid_option(ax, title, black_indices):
    ax.set_xlim(-0.2, 3.2)
    ax.set_ylim(-0.2, 3.2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 1(0,2) 2(1,2) 3(2,2)
    for i in range(1, 10):
        col = (i - 1) % 3
        row = 2 - (i - 1) // 3
        
        is_black = i in black_indices
        facecolor = 'black' if is_black else 'white'
        
        rect = patches.Rectangle((col, row), 1, 1, linewidth=1.5, edgecolor='black', facecolor=facecolor)
        ax.add_patch(rect)
        
    ax.text(1.5, -0.4, title, ha='center', va='center', fontsize=16)

def execute_ai_plot_code(python_code: str, output_filename: str) -> bool:
    if python_code is None or not isinstance(python_code, str) or python_code.strip() == "":
        return False
        
    env = {
        "plt": plt, "mpl": mpl, "patches": patches, "Rectangle": Rectangle,
        "RegularPolygon": RegularPolygon, "Wedge": Wedge, "Circle": Circle,
        "Arc": Arc, "np": np, "math": math, "draw_dimension": draw_dimension,
        "draw_grid_option": draw_grid_option # 🚀 開放新函式給 AI 使用
    }
    
    code_to_run = python_code.replace("temp_diagram.png", output_filename)
    
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