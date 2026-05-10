# 檔案 1：plot_utils.py (繪圖核心與輔助函式)
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
    """
    提供給 AI 呼叫的尺寸標註專用輔助函式。
    確保 AI 不會亂畫標註線，統一考卷的視覺風格。
    """
    p1, p2 = np.array(p1), np.array(p2)
    vec = p2 - p1
    length = np.linalg.norm(vec)
    if length == 0: return
    u = vec / length
    
    n = np.array([-u[1], u[0]])
    if invert:
        n = -n
        
    start = p1 + n * offset
    end = p2 + n * offset
    
    ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='<->', lw=1.5))
    
    mid = (start + end) / 2
    text_pos = mid + n * 0.3
    ax.text(text_pos[0], text_pos[1], f'${text}$', ha='center', va='center', fontsize=16)

def execute_ai_plot_code(python_code: str, output_filename: str) -> bool:
    """執行 AI 產生的繪圖程式碼"""
    if not python_code or python_code.strip() == "":
        return False
        
    env = {
        "plt": plt,
        "mpl": mpl,
        "patches": patches,
        "Rectangle": Rectangle,
        "RegularPolygon": RegularPolygon,
        "Wedge": Wedge,
        "Circle": Circle,
        "Arc": Arc,
        "np": np,
        "math": math,
        "draw_dimension": draw_dimension
    }
    
    code_to_run = python_code.replace("temp_diagram.png", output_filename)
    
    try:
        fig, ax = plt.subplots(figsize=(6, 6))
        env['fig'] = fig
        env['ax'] = ax
        
        exec(code_to_run, env)
        
        if not os.path.exists(output_filename):
            plt.savefig(output_filename, dpi=300, bbox_inches='tight', transparent=True)
            
        plt.close('all')
        return True
        
    except Exception as e:
        print(f"繪圖錯誤: {e}")
        plt.close('all')
        return False

def clean_up_temp_images(image_list: list):
    for img in image_list:
        if img and os.path.exists(img):
            try:
                os.remove(img)
            except Exception:
                pass