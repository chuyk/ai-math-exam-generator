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
import platform
import urllib.request
from matplotlib import font_manager

# 🚀 終極中文字體防禦機制 (自動下載 NotoSansTC 或掃描本機字體)
plt.rcParams.update({'font.size': 16})
plt.rcParams['axes.unicode_minus'] = False

def setup_chinese_font():
    font_url = 'https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansTC/NotoSansTC-Regular.ttf'
    font_path = 'NotoSansTC-Regular.ttf'
    success = False
    
    # 1. 嘗試下載雲端字體
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(font_url, font_path)
            success = True
        except:
            pass
    else:
        success = True

    # 2. 下載成功則直接套用
    if success:
        try:
            font_manager.fontManager.addfont(font_path)
            plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
            return
        except:
            pass

    # 3. 若下載失敗，啟動動態硬碟掃描
    sys_os = platform.system()
    search_dirs = ['C:/Windows/Fonts'] if sys_os == 'Windows' else ['/System/Library/Fonts', '/Library/Fonts', os.path.expanduser('~/Library/Fonts')]
    target_files = ['msjh.ttc', 'msjh.ttf', 'pingfang.ttc']
    
    for d in search_dirs:
        if not os.path.exists(d): continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower() in target_files:
                    try:
                        f_path = os.path.join(root, f)
                        font_manager.fontManager.addfont(f_path)
                        plt.rcParams['font.family'] = font_manager.FontProperties(fname=f_path).get_name()
                        return
                    except:
                        pass
                        
    # 4. 最終備案
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] if sys_os == 'Windows' else ['PingFang TC', 'Noto Sans CJK TC']

# 執行字體初始化
setup_chinese_font()
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
    
    # 1. 先畫出底部的 3x3 淺灰色格線 (完美九宮格)
    for i in range(1, 10):
        col = (i - 1) % 3
        row = 2 - (i - 1) // 3
        rect_bg = patches.Rectangle((col, row), 1, 1, linewidth=0.5, edgecolor='lightgray', facecolor='none')
        ax.add_patch(rect_bg)
        
    # 2. 畫出實體方塊 (純白底色，加上粗黑邊框突顯)
    for i in active_indices:
        col = (i - 1) % 3
        row = 2 - (i - 1) // 3
        rect_solid = patches.Rectangle((col, row), 1, 1, linewidth=2.5, edgecolor='black', facecolor='white')
        ax.add_patch(rect_solid)
        
    # 加上選項標題 (A), (B) 等
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