# 檔案 1：plot_utils.py (已加回：強制裁切留白、draw_dimension)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, RegularPolygon, Wedge, Circle, Arc
import numpy as np
import math
import os

mpl.rcParams['svg.fonttype'] = 'none'
plt.rcParams.update({'font.size': 18})

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

def execute_ai_plot_code(python_code: str, output_filename: str) -> bool:
    if not python_code or python_code.strip() == "":
        return False
        
    env = {
        "plt": plt, "mpl": mpl, "patches": patches, "Rectangle": Rectangle,
        "RegularPolygon": RegularPolygon, "Wedge": Wedge, "Circle": Circle,
        "Arc": Arc, "np": np, "math": math, "draw_dimension": draw_dimension
    }
    
    code_to_run = python_code.replace("temp_diagram.png", output_filename)
    
    try:
        fig, ax = plt.subplots(figsize=(6, 6))
        env['fig'] = fig
        env['ax'] = ax
        
        exec(code_to_run, env)
        
        if not os.path.exists(output_filename):
            # 🚀 強制攔截：不管 AI 怎麼設極限，系統強制重新貼合邊界裁切，解決畫布留白過大
            ax.autoscale(enable=True, axis='both', tight=True)
            ax.relim()
            ax.autoscale_view()
            ax.margins(0.1) # 給予 10% 舒適留白
            
            plt.savefig(output_filename, dpi=300, bbox_inches='tight', pad_inches=0.1, transparent=True)
            
        plt.close('all')
        return True
        
    except Exception as e:
        print(f"繪圖錯誤: {e}")
        plt.close('all')
        return False

def clean_up_temp_images(image_list: list):
    for img in image_list:
        if img and os.path.exists(img):
            try: os.remove(img)
            except Exception: pass