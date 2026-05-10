import matplotlib
matplotlib.use('Agg') # ⚠️ 極度重要：強制背景繪圖，防止 Streamlit 雲端崩潰
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, RegularPolygon, Wedge, Circle, Arc
import numpy as np
import math
import os

# ==========================================
# 基礎繪圖環境設定 (符合印刷規格)
# ==========================================
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
    
    # 計算垂直法向量
    n = np.array([-u[1], u[0]])
    if invert:
        n = -n
        
    # 標註線的起終點 (平移 offset 距離)
    start = p1 + n * offset
    end = p2 + n * offset
    
    # 畫雙箭頭標註線
    ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='<->', lw=1.5))
    
    # 標註文字 (確保加上 $ 讓數學符號正確渲染)
    mid = (start + end) / 2
    text_pos = mid + n * 0.3
    ax.text(text_pos[0], text_pos[1], f'${text}$', ha='center', va='center', fontsize=16)


def execute_ai_plot_code(python_code: str, output_filename: str) -> bool:
    """
    執行 AI 產生的 matplotlib 程式碼，並將結果存為指定的圖片檔案。
    """
    if not python_code or python_code.strip() == "":
        return False
        
    # 準備執行環境字典，預先注入所有需要的函式庫與物件
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
        "draw_dimension": draw_dimension # ⚠️ 注入輔助函式供 AI 呼叫
    }
    
    # 將 AI 程式碼中的預設檔名替換為我們的暫存檔名
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
        print(f"⚠️ 繪圖程式碼執行錯誤: {e}")
        plt.close('all')
        return False

def clean_up_temp_images(image_list: list):
    """清理暫存的圖片檔案"""
    for img in image_list:
        if img and os.path.exists(img):
            try:
                os.remove(img)
            except Exception:
                pass