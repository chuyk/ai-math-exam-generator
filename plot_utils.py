import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, RegularPolygon, Wedge, Circle
import numpy as np
import math
import os

# ==========================================
# 基礎繪圖環境設定 (符合印刷規格)
# ==========================================
mpl.rcParams['svg.fonttype'] = 'none'
plt.rcParams.update({'font.size': 18})

def execute_ai_plot_code(python_code: str, output_filename: str) -> bool:
    """
    執行 AI 產生的 matplotlib 程式碼，並將結果存為指定的圖片檔案。
    
    Args:
        python_code (str): AI 產生的 Python 程式碼字串。
        output_filename (str): 要儲存的目標圖片檔名 (例如 temp_diagram_1.png)。
        
    Returns:
        bool: 繪圖是否成功。
    """
    if not python_code or python_code.strip() == "":
        return False
        
    # 準備執行環境字典，預先注入所有需要的函式庫與物件
    # 這樣 AI 即使忘記 import 也不會報錯
    env = {
        "plt": plt,
        "mpl": mpl,
        "patches": patches,
        "Rectangle": Rectangle,
        "RegularPolygon": RegularPolygon,
        "Wedge": Wedge,
        "Circle": Circle,
        "np": np,
        "math": math
    }
    
    # 將 AI 程式碼中的預設檔名 'temp_diagram.png' 動態替換為我們指派的題號檔名
    code_to_run = python_code.replace("temp_diagram.png", output_filename)
    
    try:
        # 每次繪圖前建立一個乾淨的新畫布
        fig, ax = plt.subplots(figsize=(6, 6))
        env['fig'] = fig
        env['ax'] = ax
        
        # 動態執行 AI 程式碼
        exec(code_to_run, env)
        
        # 防呆機制：如果 AI 的程式碼中漏掉了 savefig，系統強制幫忙存檔
        if not os.path.exists(output_filename):
            plt.savefig(output_filename, dpi=300, bbox_inches='tight', transparent=True)
            
        plt.close('all') # 釋放記憶體
        return True
        
    except Exception as e:
        print(f"⚠️ 繪圖程式碼執行錯誤: {e}")
        plt.close('all')
        return False

def clean_up_temp_images(image_list: list):
    """
    清理暫存的圖片檔案，避免佔用伺服器空間。
    """
    for img in image_list:
        if img and os.path.exists(img):
            try:
                os.remove(img)
            except Exception as e:
                pass