import os
import pypandoc
import re
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docxcompose.composer import Composer

def clean_latex_spacing(text: str) -> str:
    """自動清除 $ 與數學式之間的空白，避免 Word 渲染失敗"""
    cleaned = re.sub(r'\$\s+(.*?)\s+\$', r'$\1$', text)
    cleaned = re.sub(r'\$\s+', r'$', cleaned)
    cleaned = re.sub(r'\s+\$', r'$', cleaned)
    return cleaned

def force_kai_font(doc, font_size=12):
    """強制統一標楷體與字級大小"""
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(font_size)
            run.font.name = 'Times New Roman'
            r = run._element
            rPr = r.get_or_add_rPr()
            rFonts = rPr.find(qn('w:rFonts'))
            if rFonts is None:
                rFonts = OxmlElement('w:rFonts')
                rPr.insert(0, rFonts)
            rFonts.set(qn('w:ascii'), 'Times New Roman')
            rFonts.set(qn('w:eastAsia'), '標楷體')

def generate_word_documents(questions_data: list, template_path: str = None) -> tuple:
    """
    回傳 (Word檔路徑, Markdown純文字)
    """
    word_md = ""
    download_md = "# 阿凱數學出卷系統 - 測驗卷原始碼\n\n"
    
    for idx, q in enumerate(questions_data, 1):
        clean_text = clean_latex_spacing(q['text'])
        
        # 供 Word 轉換的版本 (只有純題目與圖片)
        word_md += f"**{idx}.** {clean_text}\n\n"
        # 供下載的 MD 版本
        download_md += f"### 第 {idx} 題\n\n{clean_text}\n\n"
        
        if q.get('img') and os.path.exists(q['img']):
            word_md += f"![圖示]({q['img']}){{width=\"3.2in\"}}\n\n"
            download_md += f"![圖示]({q['img']})\n\n"
            
            # 在下載版 Markdown 加入 Python 原始碼，折疊顯示
            if q.get('code'):
                download_md += "<details><summary>🖼️ 點擊展開：繪圖 Python 原始碼</summary>\n\n"
                bt = "`" * 3
                download_md += f"{bt}python\n" + q['code'] + f"\n{bt}\n\n</details>\n\n"
                
        word_md += "<br><br>\n\n"
        download_md += "---\n\n"
        
    temp_teacher_docx = "temp_teacher.docx"
    pypandoc.convert_text(word_md, 'docx', format='md', outputfile=temp_teacher_docx)
    
    output_teacher = "教師用解答本.docx"
    
    if template_path and os.path.exists(template_path):
        master_doc = Document(template_path)
        composer = Composer(master_doc)
        temp_doc = Document(temp_teacher_docx)
        force_kai_font(temp_doc)
        temp_doc.save(temp_teacher_docx)
        
        composer.append(Document(temp_teacher_docx))
        force_kai_font(master_doc)
        master_doc.save(output_teacher)
    else:
        doc = Document(temp_teacher_docx)
        force_kai_font(doc)
        doc.save(output_teacher)
        
    if os.path.exists(temp_teacher_docx):
        os.remove(temp_teacher_docx)

    return output_teacher, download_md