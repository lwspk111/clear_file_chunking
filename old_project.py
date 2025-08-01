from ast import Slice
import base64
from dataclasses import make_dataclass
import re
import os
import shutil
# 添加在文件顶部导入区
import logging
from sqlite3 import connect
import unicodeitplus 
import json
from bs4 import BeautifulSoup
import langid
# 配置日志
import time
# 添加在文件顶部导入区

def replace_with_clean_blank(content, target, placeholder):
    """
    替换content中的target为placeholder，并去除target前后的空行
    """
    # 构造正则，匹配target前后可能的空行 确保占位符的前后都没有\n
    pattern = re.compile(r'(\n?)([ \t]*\n)*' + re.escape(target) + r'([ \t]*\n)*(\n?)')
    def repl(match):
        before = match.group(1)
        after = match.group(4)
        # 保证替换后只保留一行（不多余空行）
        return before + placeholder + after
    return pattern.sub(repl, content, count=1)
class content_exactor:
    """
    修改一下逻辑使得其 
    1.替换模式下可以 让占位符直接连接上文
    2.增加一个删除模式直接删除这个数学公式/表格/图片
    3.提取时提取和处理表格/图片数学公式前后的名称文本，使用<table_name><table_name> 如标记<table_name>表 2-5 一些蛋白质及其亚基的相对分子质量<table_name>,<image_name>图 3-4 中间复合物降低活化能<image_name>
    4. 对于()内的内容进行处理和过滤 以删除文中引用和非正文必要的注释 如(图 2- 38)(引自 López-Otin C, 2002),保留正常的()注释
    5. 合并续表的上下两个表，并移除"续表"或者(续)
    """
    def get_html_table(content,output_dir):
        """
        从HTML内容中提取表格数据并转换为CSV格式，同时在原文中进行占位替换
        
        参数:
            content (str): 包含HTML表格的字符串内容
        
        返回:
            dict: 包含处理结果和元数据的字典
        """
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            print( ("warning:HTML内容中没有找到表格"))
        
        results = []
        modified_content = content
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 用正则找到所有<table ...>...</table>的字符串
        table_pattern = re.compile(r'<table.*?>.*?</table>', re.DOTALL)
        table_matches = list(table_pattern.finditer(content))
        if len(table_matches) != len(tables):
            print("警告：表格数量不一致，可能有嵌套表格或格式问题")
        if len(table_matches) == 0:
            print("警告：没有找到表格")
            return {
                "modified_content": content,
                "tables": results
            }
        for i, (table, match) in enumerate(zip(tables, table_matches)):
            table_str = match.group(0)
            
            # 提取表头
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            
            # 提取表格数据
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                if cells:  # 跳过空行
                    rows.append(cells)
            
            # 生成CSV内容
            csv_content = []
            if headers:
                csv_content.append(','.join(headers))
            for row in rows:
                csv_content.append(','.join(row))
            
            # 生成占位符和文件名（改为使用顺序索引i）
            placeholder = f"table_html_{i}"
            csv_filename = f"{placeholder}.csv"
        
            # 写入CSV文件（添加BOM头）
            csv_path = os.path.join(output_dir, csv_filename)
            with open(csv_path, 'w', encoding='utf-8-sig') as f:
                f.write('\n'.join(csv_content))
            
            # 创建并写入JSON映射文件
            mapping = {
                "placeholder": placeholder,
                "csv_file": csv_filename,
                "headers": headers,
                "row_count": len(rows),
                "csv_path":csv_path,
                "csv_content":table_str
            }
            results.append(mapping)
        json_path = os.path.join(output_dir, "html_tables.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 只替换当前这个表格
            modified_content = replace_with_clean_blank(modified_content, table_str, f"[TABLE_PLACEHOLDER:{placeholder}]")
            
            
        return {
            "modified_content": modified_content,
            "tables": results
            }
    
    def get_markdown_table(content,output_dir):
        """
        从Markdown内容中提取表格数据并转换为CSV格式，同时在原文中进行占位替换
        
        参数:
            content (str): 包含Markdown表格的字符串内容
        
        返回:
            dict: 包含处理结果和元数据的字典
        """
        # 匹配Markdown表格
        table_pattern = re.compile(r'(\|.*\|\n)((?:\|.*\|\n)+)')
        matches = table_pattern.findall(content)
        
        if not matches:
            return {
                "modified_content": content,
                "tables": []
            }
        
        results = []
        modified_content = content
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        for i, (header_row, data_rows) in enumerate(matches):
            full_table = header_row + data_rows
            
            # 解析表头
            headers = [h.strip() for h in header_row.split('|')[1:-1]]
            
            # 解析表格数据
            rows = []
            for row in data_rows.split('\n'):
                if not row.strip():
                    continue
                cells = [c.strip() for c in row.split('|')[1:-1]]
                if cells:  # 确保数据不为空
                    rows.append(cells)
            
            # 生成CSV内容
            csv_content = []
            if headers:
                csv_content.append(','.join(headers))
            for row in rows:
                if len(row) == len(headers):  # 确保数据列数与表头一致
                    csv_content.append(','.join(row))
            
            # 生成占位符和文件名（改为使用顺序索引i）
            placeholder = f"table_md_{i}"  # 原：table_md_{i}_{hash(full_table)}
            csv_filename = f"{placeholder}.csv"
            
            
            # 写入CSV文件
            csv_path = os.path.join(output_dir, csv_filename)
            with open(csv_path, 'w', encoding='utf-8-sig') as f:
                f.write('\n'.join(csv_content))
            
            # 创建并写入JSON映射文件
            mapping = {
                "placeholder": placeholder,
                "csv_file": csv_filename,
                "csv_path":csv_path,
                "headers": headers,
                "row_count": len(rows),
                "original_content":matches
            }
            results.append(mapping)
            
        json_path = os.path.join(output_dir, "tables.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 在原文中进行占位替换
            modified_content = replace_with_clean_blank(modified_content, full_table, f"[TABLE_PLACEHOLDER:{placeholder}]")
            
            results.append({
                "csv_path": csv_path,
                "json_path": json_path,
                "placeholder": placeholder
            })
        
        return {
            "modified_content": modified_content,
            "tables": results
        }
        
    def get_markdown_image(content,output_dir):
        """
        从Markdown内容中提取图片链接并创建映射，同时在原文中进行占位替换
        
        参数:
            content (str): 包含Markdown图片链接的字符串内容
        
        返回:
            dict: 包含处理结果和元数据的字典
        """
        # 修复：正确匹配Markdown图片链接 ![alt text](url)
        image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
        matches = image_pattern.findall(content)
        
        if not matches:
            return {
                "modified_content": content,
                "images": []
            }
        
        results = []
        modified_content = content
        
        # 创建输出目录"
        os.makedirs(output_dir, exist_ok=True)
        
        for i, (alt_text, url) in enumerate(matches):
            placeholder = f"image_{i}"
            # 创建映射信息
            mapping = {
                "placeholder": placeholder,
                "image_url": url,
                "alt_text": alt_text
            }
            
            # 保存JSON映射文件
            
            
            # 替换图片链接为占位符
            image_str = f"![{alt_text}]({url})"
            modified_content = replace_with_clean_blank(modified_content, image_str, f"[IMAGE_PLACEHOLDER:{placeholder}]")
            
            results.append(mapping)
        json_path = os.path.join(output_dir, f"images.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return {
            "modified_content": modified_content,
            "images": results
        }

    def get_markdown_formula(content,output_dir):
        """
        从Markdown内容中提取数学公式并创建映射，同时在原文中进行占位替换
        
        参数:
            content (str): 包含数学公式的字符串内容
        
        返回:
            dict: 包含处理结果和元数据的字典
        """
        # 匹配行内公式 $...$
        inline_pattern = re.compile(r'\$(.*?)\$')
        # 匹配块级公式 $$...$$
        block_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
        
        results = []
        modified_content = content
        formula_count = 0
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理行内公式
        for i, formula in enumerate(inline_pattern.findall(content)):
            if not formula.strip():  # 跳过空公式
                continue
                
            # 检查是否为简单公式
            if not formular_process.is_complex_formular(formula):
                # 简单公式，直接替换为Unicode字符
                try:
                    unicode_formula = unicodeitplus.replace(formula)
                except Exception as e:
                    print(f"公式转换错误: {formula}")
                    unicode_formula = formula
                    
                
                modified_content = replace_with_clean_blank(modified_content, f"${formula}$", unicode_formula)
            else:
                placeholder = f"formula_inline_{formula_count}"
                mapping = {
                    "placeholder": placeholder,
                    "type": "inline",
                    "formula": formula
                }
                
                results.append(mapping)
                formula_count += 1
                
                # 替换公式
                modified_content = replace_with_clean_blank(modified_content, f"${formula}$", f"[FORMULA_PLACEHOLDER:{placeholder}]")
        
        # 处理块级公式
        for i, formula in enumerate(block_pattern.findall(content)):
            if not formula.strip():  # 跳过空公式
                continue
                
            # 检查是否为简单公式
            if not formular_process.is_complex_formular(formula.strip()):
                # 简单公式，直接替换为Unicode字符
                try:
                    unicode_formula = unicodeitplus.replace(formula.strip())
                except Exception as e:
                    print(f"公式转换错误: {formula}")
                    unicode_formula = formula
                modified_content = replace_with_clean_blank(modified_content, f"$${formula}$$", unicode_formula)
            else:
                placeholder = f"formula_block_{formula_count}"
                mapping = {
                    "placeholder": placeholder,
                    "type": "block",
                    "formula": formula.strip()
                }
                
                results.append(mapping)
                formula_count += 1
                
                # 替换公式
                modified_content = replace_with_clean_blank(modified_content, f"$${formula}$$", f"[FORMULA_PLACEHOLDER:{placeholder}]")
        
        # 合并所有复杂公式到一个json文件
        if formula_count > 0:
            json_path = os.path.join(output_dir, "formulas.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        
        return {
            "modified_content": modified_content,
            "formulas": results
        }

    def get_markdown_code_block(content,output_dir):
        """
        从Markdown内容中提取代码块并创建映射，同时在原文中进行占位替换
        
        参数:
            content (str): 包含代码块的字符串内容
        
        返回:
            dict: 包含处理结果和元数据的字典
        """
        # 匹配代码块 ```language\n code \n```
        code_block_pattern = re.compile(r'```(.*?)\n(.*?)```', re.DOTALL)
        matches = code_block_pattern.findall(content)
        
        if not matches:
            return {
                "modified_content": content,
                "code_blocks": []
            }
        
        results = []
        modified_content = content
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        for i, (language, code) in enumerate(matches):
            placeholder = f"code_block_{i}"
            full_block = f"```{language}\n{code}```"
            
            # 创建映射信息
            mapping = {
                "placeholder": placeholder,
                "language": language.strip(),
                "code": code.strip()
            }
            
            # 保存JSON映射文件
           
            # 替换代码块为占位符
            modified_content = replace_with_clean_blank(modified_content, full_block, f"[CODE_PLACEHOLDER:{placeholder}]")
            
            results.append({mapping})
        json_path = os.path.join(output_dir, f"codefile.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        return {
            "modified_content": modified_content,
            "code_blocks": results
        }
    def full_process(content, book_name):
        start_time = time.time()
        table_output_dir = os.path.join(r"G:\graph_rag_enhance\clear_markdown_search\table", book_name)
        code_output_dir = os.path.join(r"G:\graph_rag_enhance\clear_markdown_search\code", book_name)
        image_output_dir = os.path.join(r"G:\graph_rag_enhance\clear_markdown_search\image", book_name)
        formula_output_dir = os.path.join(r"G:\graph_rag_enhance\clear_markdown_search\formula", book_name)

        # 1. 先提取表格（此时表格内容是原始内容，写csv，正文替换为占位符）
        result = content_exactor.get_html_table(content, table_output_dir)
        content = result["modified_content"]

        # 2. 再对正文做代码块、图片、公式占位
        result = content_exactor.get_markdown_code_block(content, code_output_dir)
        content = result["modified_content"]

        result = content_exactor.get_markdown_image(content, image_output_dir)
        content = result["modified_content"]

        result = content_exactor.get_markdown_formula(content, formula_output_dir)
        content = result["modified_content"]
    
        end_time = time.time()
        print(f"[full_process] 内容处理耗时: {end_time - start_time:.2f} 秒")
        return content
def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

logger = setup_logger()
class roman_num:
    def IntToRoman(num: int) -> str:
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        symbols = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        small_symbols = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix","v","iv","i"]
        roman = ''
        small_roman = ''
        i = 0
        while num > 0:
            k = num // values[i]
            for j in range(k):
                roman += symbols[i]
                small_roman += small_symbols[i]
                num -= values[i]
            i += 1

        return [roman, small_roman]

    def generate_roman_numerals(limit: int) -> set:
        """Generates a set of Roman numerals up to a given limit."""
        roman_numerals = set()
        for i in range(1, limit + 1):
            romans = roman_num.IntToRoman(i)
            roman_numerals.add(romans[0])  # Uppercase
            roman_numerals.add(romans[1])  # Lowercase
        return roman_numerals


   
    # Unicode Roman numerals to ASCII mapping
    UNICODE_ROMAN_MAP = {
        'Ⅰ': 'I', 'Ⅱ': 'II', 'Ⅲ': 'III', 'Ⅳ': 'IV', 'Ⅴ': 'V', 'Ⅵ': 'VI', 'Ⅶ': 'VII', 'Ⅷ': 'VIII', 'Ⅸ': 'IX', 'Ⅹ': 'X', 'Ⅺ': 'XI', 'Ⅻ': 'XII',
        'ⅰ': 'i', 'ⅱ': 'ii', 'ⅲ': 'iii', 'ⅳ': 'iv', 'ⅴ': 'v', 'ⅵ': 'vi', 'ⅶ': 'vii', 'ⅷ': 'viii', 'ⅸ': 'ix', 'ⅹ': 'x', 'ⅺ': 'xi', 'ⅻ': 'xii',
        'Ⅼ': 'L', 'Ⅽ': 'C', 'Ⅾ': 'D', 'Ⅿ': 'M',
        'ⅼ': 'l', 'ⅽ': 'c', 'ⅾ': 'd', 'ⅿ': 'm'
    }



    def normalize_roman_numerals(text: str) -> str:
        """Replaces Unicode Roman numerals with their ASCII equivalents."""
        for uni, asc in roman_num.UNICODE_ROMAN_MAP.items():
            text = text.replace(uni, asc)
        return text
ROMAN_NUMERALS = roman_num.generate_roman_numerals(50)

SLICE_POINT1 = "___slicepoint1___"#
SLICE_POINT2 = "___slicepoint2___"
SLICE_POINT3 = "___slicepoint3___"
class formular_process:
    def is_complex_formular(text):
        complex_flag = {r"\frac", r"\sqrt", r"\sum", r"\int", r"\end", r"\array", r"\begin", r"\sum", r"\prod", r"\lim"}
        # 如果有这些flag，则属于复杂公式
        if any(flag in text for flag in complex_flag):
            return True
        # 也可以根据公式长度判断
        return False

    def restore_formular(formula):
        if formular_process.is_complex_formular(formula):
            return (formula,"complex")
        else: 
            formula = unicodeitplus.parse(formula)
            return(formula,"easy")
    #并把那些简单，无关紧要的数学公式变成Unicode字符
    
            
class is_chapter_header:
    """
    章节标题识别工具类
    提供多种规则判断文本行是否为章节标题，支持中英文关键词、Markdown格式、数字编号等类型
    """
  
    # 中文章节标题关键词集合(常见文献章节名称)
    TITLE_KEYWORDS_ch = {
    "前言", "序言", "序", "引言", "目录", "摘要",
    "后记", "跋", "参考文献", "附录","返回目录","索引","附表"
    }
    # 英文章节标题关键词集合(常见文献章节名称)
    TITLE_KEYWORDS_en={
    "preface", "introduction", "contents", "abstract",
    "epilogue", "afterword", "references", "appendix", "back to contents", "index", "table of contents"
    }
    is_markdown_chapter_mode0=re.compile(r'^\s*(#+)\s+.+$')
    is_markdown_chapter_mode1=re.compile(r'^\s*(#+)[^#\s].*$')
    is_text_type_header_model=re.compile(r'.*?\b(第[一二三四五六七八九十百千万\d]+\s*[章卷册篇节编回]|(C|c)hapter\s*\d+|[（(][一二三四五六七八九十百千万\d]+[）)])\b')
    is_point_type_header_model=re.compile(r'^\s*\d+(\.\d+)+.*')
    is_bracket_header_model= re.compile(r'^[\(\（][\d一二三四五六七八九十百千万][\)\）]$')
    def is_markdown_chapter(content, work_mode):
        """
        判断内容是否为Markdown格式标题

        Args:
            content (str): 待检查的文本内容
            work_mode (int): 工作模式
                            0 - 标准模式(#后必须有空格)
                            1 - 后处理模式(#后无空格)

        Returns:
            bool: 符合Markdown标题格式返回True，否则返回False
        """
        # 标准模式：# 后必须有空格
        #if work_mode == 0:
            # 修改前: pattern = r'^\s*(#+)\s+.+$'
        pattern = is_chapter_header.is_markdown_chapter_mode0  # 使用\s+匹配任何空白字符
        # 后处理模式：# 后无空格
        
        #elif work_mode == 1:
            #pattern = is_chapter_header.is_markdown_chapter_mode1
        
        #else:
        #    return False
        #print(bool(re.match(pattern, content)),content,work_mode)
        return bool(re.match(pattern, content))

    def is_text_type_header(clean_line):
        # 匹配类似第一章 chapter1等文本类型的标题   
        return bool(re.match(is_chapter_header.is_text_type_header_model,clean_line))
    def is_point_type_header(clean_line):
        # 匹配类似1.1 1.2 等点号类型的标题
        return bool(re.match(is_chapter_header.is_point_type_header_model,clean_line))
    def is_keyword_header(clean_line):
        """
        
        检查是否为关键词类型标题

        Args:
            clean_line (str): 清洗后的文本行

        Returns:
            bool: 属于关键词标题返回True，否则返回False
        """
        # 移除空字符串匹配并添加大小写不敏感检查
        return (clean_line.strip().lower() in [kw.lower() for kw in is_chapter_header.TITLE_KEYWORDS_ch] or 
                clean_line.strip().lower() in [kw.lower() for kw in is_chapter_header.TITLE_KEYWORDS_en])
    def is_roman_numeral_header(clear_line):
        if clear_line in ROMAN_NUMERALS:
            return True
        else:
             return False
    def is_bracket_header(clear_line):
        # 及括号类型的小标题 如 （一） (1)
        return bool(re.match(is_chapter_header.is_bracket_header_model, clear_line))

    def rule_based_is_chapter_header(line: str, work_mode: bool) -> tuple:
        """
        基于多规则组合判断是否为章节标题

        Args:
            line (str): 原始文本行
            work_mode (bool): Markdown检查模式

        Returns:
            tuple: (bool, int): 是否为章节标题 以及状态 
            0 为markdown类型的小标题 如 # 
            1 为 文字类型的小标题如 第一章 罗马数字小标题如 IV iv 以及括号类型的小标题 如 （一） (1)
            2 为 点类型的小标题 如 1.2.3 
            3 不是小标题
        """
        clean_line = line.strip()
        if not clean_line:
            return (False,3)

        normalized_line = roman_num.normalize_roman_numerals(clean_line)

        # 按优先级顺序检查各规则(关键词标题优先级最高)
   
        if is_chapter_header.is_markdown_chapter(clean_line,work_mode):
            return(True,0)# markdown
        elif is_chapter_header.is_text_type_header(clean_line) or is_chapter_header.is_roman_numeral_header(normalized_line) :
            return(True,1) # 文本+
        elif is_chapter_header.is_point_type_header(clean_line) or is_chapter_header.is_bracket_header(clean_line):
            return (True,2)# 点+括号
        else:
            return(False,3)
    def llm_based_is_chapter_header(input_path,output_path,tooshort_level=20):

        # 逻辑笔记 如果 new_len 显示太长 而且没有flag 这大概率是正文，或者一堆小标题堆积，往往在目录里面，可以删除目录
        # 如果 有 flag 而且很短 这几乎就是小标题 如果小标题是被 点格式标记的 那可能需要被llm核查一下，因为这可能有误判，如果正文以.开头
        #  如果没有 flag而且很短，那需要提高警惕，这很可能是那些冷门 小标题 
        # 如果是基于 # 标记的 那几乎 100% 是小标题
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"错误: 输入文件未找到 -> {input_path}")
            return
        except Exception as e:
            print(f"读取文件时发生错误: {e}","line=577")
        checking_work=[]
       
        for line in lines:
            line=line.strip()
            
            if not line:
                continue
            if "#" in line:
                line=line.replace("#","")

            # 检查是否包含图片占位符
            if "[IMAGE_PLACEHOLDER" in line or "[TABLE_PLACEHOLDER" in line:
                continue  # 跳过包含图片和表格占位符的行
            elif "[FORMULA_PLACEHOLDER" in line:
                # 找到占位符的开始和结束位置
                start = line.find("[FORMULA_PLACEHOLDER")
                end = line.find("]", start)
                if end != -1:
                    # 移除占位符
                    line = line[:start] + line[end+1:]

            flag= line[0:len(SLICE_POINT1)]
            
            if flag==SLICE_POINT1 or flag == SLICE_POINT2 or flag == SLICE_POINT3:
                line_content=line[len(SLICE_POINT1):]
                # 被规则判定为小标题
                if flag == SLICE_POINT3 and new_len(line_content) <= tooshort_level:
                # 点和括号有可能误判 其他的 通常是100%正确
                    checking_work.append(line_content)#发送llm
            else:
                if new_len(line)<=tooshort_level:
                    checking_work.append(line)#发送llm
        print(checking_work,len(checking_work))

def new_len(text):
    language=langid.classify(text)[0]
  
    # 1. 判断语言
    if language == "zh":
        return len(text)
    elif language == "en":
        words = text.split()
        return len(words)
    # 进行分词
    else:
        print(f"unsupported language, translate it to Chinese or English or send email to us,your language is {language}, text= {text}")
        return 0
def process_text_file(input_path: str, output_path: str,work_mode:bool,log_version):
    start_time = time.time()
    """
    读取输入文件，标记章节，并写入输出文件。

    Args:
        input_path (str): 输入文件的路径。
        output_path (str): 输出文件的路径。
    work_mode 设置为0 时，为SLICE_POINT换行模型 设置为1时，为不换行标记模式
    """
 
    if log_version=="0":
        print(f"正在处理文件: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}","line=568")
        return
    content = content_exactor.full_process(content,book_name="基础生物化学")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}","line=568")
        return
    
    end1_time= time.time()
    print("标记数学公式等用时",end1_time-start_time)
    marking_title(input_path,output_path,work_mode,log_version)
    end2_time= time.time()
    print("标记标题等用时",end2_time-end1_time)
def marking_title(input_path,output_path,work_mode,log_version):
    if work_mode:
        suffix = ""
    else:
        suffix = "\n"
    processed_lines = []
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}","line=577")
        return
    # 逐行处理
    for line in lines:
        # 去除行尾的换行符以便处理
        line_content = line.rstrip('\n')

        # 检查是否已被标记，防止重复标记
        if line_content.strip() == SLICE_POINT1 or line_content.strip() == SLICE_POINT2 or line_content.strip() == SLICE_POINT3:
            processed_lines.append(line)
            continue

        # 判断是否为章节标题
        
        if is_chapter_header.rule_based_is_chapter_header(line_content,work_mode)[0]:
            # 添加标记，并保留原行
            # \n 确保标记和原标题在不同行
            code=is_chapter_header.rule_based_is_chapter_header(line_content,work_mode)[1]
            if code == 0:
                flag = SLICE_POINT1
            elif code ==1:
                flag = SLICE_POINT2
            elif code == 2:
                flag = SLICE_POINT3

            processed_lines.append(f"{flag}{suffix}")
            processed_lines.append(line)
            
            if log_version:
                print(f"  [匹配成功] -> {line_content}")
        else:
            # 如果不是标题，直接保留原行
            processed_lines.append(line)

    # 将处理后的内容写入输出文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)
        print(f"\n处理完成！结果已保存到: {output_path}")
    except Exception as e:
        print(f"写入文件时发生错误: {e}","line=609")
 



def test0(input_path,output_path):
    total_start = time.time()
    process_text_file(input_path,output_path,1,log_version=0)
    total_end = time.time()
    print(f"[main] 程序总耗时: {total_end - total_start:.2f} 秒")
# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 使用示例 ---
    
    

    input_path = r"G:\graph_rag_enhance\short_unit_code\epub_to_markdown\output\中华民国专题史（套装书共18册，两岸四地70位专家学者首次合作，十八个专题，重构民国历史，南京大学出版社巨匠之作） (中华民国专题史) (Z-Library)\markdown\part0065.md"
    output_path = r"G:\graph_rag_enhance\clear_markdown_search\test\test02.md"
    test0(input_path,output_path)
  
    is_chapter_header.llm_based_is_chapter_header(output_path,output_path="")
    #print(new_len('下面以大肠杆菌乳糖操纵子来说明酶合成的诱导作用机制 。'))