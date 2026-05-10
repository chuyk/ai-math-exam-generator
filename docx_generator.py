import os
import pypandoc
import zipfile
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docxcompose.composer import Composer

def force_kai_font(doc, font_size=12):
    """
    熨平整份文件的字體，強制中文字體為標楷體，英文字體為 Times New Roman，並統一字級。
    """
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

def generate_word_documents(questions_data: list, template_path: str = None, generate_student_version: bool = False) -> str:
    """
    根據生成的題目資料與範本，轉換出正式的 Word 考卷。
    
    Args:
        questions_data (list): 包含 [{'text': '...', 'img': '...'}, ...] 的列表。
        template_path (str): 老師上傳的範本路徑，若無則為 None。
        generate_student_version (bool): 是否要額外產出一份無解答的學生卷。
    
    Returns:
        str: 產出的單一 .docx 檔案路徑，或打包的 .zip 檔案路徑。
    """
    # 建立教師版內容
    teacher_md = ""
    for idx, q in enumerate(questions_data, 1):
        teacher_md += f"**{idx}.** {q['text']}\n\n"
        if q.get('img') and os.path.exists(q['img']):
            # 插入圖片並鎖定寬度避免跑版
            teacher_md += f"![圖示]({q['img']}){{width=\"3.2in\"}}\n\n"
        # 加上適當的排版間距
        teacher_md += "<br><br>\n\n"
        
    # 加入版權宣告
    teacher_md += "---\n\n**宜蘭縣中華國中 - 褚煜凱老師設計**\n"

    # 先轉為暫存檔
    temp_teacher_docx = "temp_teacher.docx"
    pypandoc.convert_text(teacher_md, 'docx', format='md', outputfile=temp_teacher_docx)
    
    # 若有提供學校範本，執行無縫縫合
    if template_path and os.path.exists(template_path):
        master_doc = Document(template_path)
        composer = Composer(master_doc)
        
        temp_doc = Document(temp_teacher_docx)
        force_kai_font(temp_doc)
        temp_doc.save(temp_teacher_docx)
        
        composer.append(Document(temp_teacher_docx))
        force_kai_font(master_doc)
        
        output_teacher = "教師用解答本.docx"
        master_doc.save(output_teacher)
    else:
        # 若無範本，直接設定暫存檔字體並存檔
        doc = Document(temp_teacher_docx)
        force_kai_font(doc)
        output_teacher = "教師用解答本.docx"
        doc.save(output_teacher)
        
    # 清理暫存檔
    if os.path.exists(temp_teacher_docx):
        os.remove(temp_teacher_docx)

    # 如果只需要教師版，直接回傳 Word 檔名
    if not generate_student_version:
        return output_teacher
        
    # ==========================================
    # 若需產生學生版，可以擴充以下邏輯 (去除解答與解析字眼)
    # 並打包為 ZIP 回傳。此處為保持代碼精簡，先建立 Zip 框架：
    # ==========================================
    zip_filename = "智慧命題考卷包.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        zipf.write(output_teacher)
        # 如果未來加上了學生卷生成邏輯，可以在這裡加入 zipf.write(output_student)
    
    return zip_filename