import re
import os
import json
from bs4 import BeautifulSoup
import unicodeitplus
from utils import replace_with_clean_blank
from formula_processor import FormulaProcessor
#20250725
class ContentExtractor:
    """
    内容提取器类
    3.提取时提取和处理表格/图片前后的名称文本，使用<table_name><table_name> 如标记<table_name>表 2-5 一些蛋白质及其亚基的相对分子质量<table_name>,<image_name>图 3-4 中间复合物降低活化能<image_name>，由于数学公式的名称不太稳定，不在此处识别
    4. 对于()内的内容进行处理和过滤 以删除文中引用和非正文必要的注释 如(图 2- 38)(引自 López-Otin C, 2002),保留正常的()注释
    """
    def merge_continued_tables(content):
        """
        合并续表的上下两个表格，并移除"续表"或"(续)"等标记
        
        参数:
            content (str): 包含HTML表格的字符串内容
            
        返回:
            str: 合并后的内容
        """
        # 匹配所有表格及其位置
        table_pattern = re.compile(r'<table.*?>.*?</table>', re.DOTALL)
        table_matches = list(table_pattern.finditer(content))
        
        if len(table_matches) < 2:
            return content
        
        # 从后往前处理，避免位置偏移问题
        for i in range(len(table_matches) - 1, 0, -1):
            current_match = table_matches[i]
            previous_match = table_matches[i-1]
            
            # 获取两个表格之间的文本
            between_text = content[previous_match.end():current_match.start()]
            
            # 检查是否包含续表标记
            if re.search(r'(续表|（续）|\(续\)|续)', between_text):
                print(f"发现续表，正在合并第{i-1}和第{i}个表格...")
                
                # 解析两个表格
                soup1 = BeautifulSoup(previous_match.group(), 'html.parser')
                soup2 = BeautifulSoup(current_match.group(), 'html.parser')
                
                # 提取表头和数据行
                rows1 = soup1.find_all('tr')
                rows2 = soup2.find_all('tr')
                
                if not rows1 or not rows2:
                    continue
                
                # 检查表头是否相同
                headers1 = [th.get_text(strip=True) for th in rows1[0].find_all(['th', 'td'])]
                headers2 = [th.get_text(strip=True) for th in rows2[0].find_all(['th', 'td'])]
                
                # 如果表头相同，合并表格
                if headers1 == headers2:
                    print("表头相同，正在合并...")
                    
                    # 合并所有行（跳过第二个表格的表头）
                    merged_rows = rows1 + rows2[1:]
                    
                    # 构建合并后的表格
                    merged_table = '<table>'
                    for row in merged_rows:
                        merged_table += str(row)
                    merged_table += '</table>'
                    
                    # 替换原文中的两个表格和续表标记
                    start_pos = previous_match.start()
                    end_pos = current_match.end()
                    
                    # 移除续表标记
                    content_before = content[:start_pos]
                    content_after = content[end_pos:]
                    
                    # 重新组合内容
                    content = content_before + merged_table + content_after
                    
                    print(f"成功合并表格，从位置{start_pos}到{end_pos}")
                else:
                    print("表头不同，跳过合并")
        
        # 最后移除所有剩余的续表标记
        content = re.sub(r'(续表|（续）|\(续\)|续)', '', content)
        
        return content
    def get_html_table(content, output_dir, mode):
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
            print(("warning:HTML内容中没有找到表格"))
        
        results = []
        modified_content = content
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 用正则找到所有<table ...>...</table>的字符串
        table_pattern = re.compile(r'<table.*?>.*?</table>', re.DOTALL)
        table_matches = list(table_pattern.finditer(content))
        if len(table_matches) != len(tables):
            print("警告：表格数量不一致，可能有嵌套表格或格式问题，将使用BeautifulSoup解析的表格")
        if len(tables) == 0:
            print("警告：没有找到表格")
            return {
                "modified_content": content,
                "tables": results
            }

        #占位符模式   
        # 以tables为主，遍历所有表格
        for i, table in enumerate(tables):
            # 尝试用正则找到原始字符串，否则用str(table)
            table_str = None
            if i < len(table_matches):
                table_str = table_matches[i].group(0)
            else:
                table_str = str(table)
            # 生成占位符和文件名（改为使用顺序索引i）
            placeholder = f"table_html_{i}"
            csv_filename = f"{placeholder}.csv"
            
            if mode == "placeholder":
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
                
                # 写入CSV文件（添加BOM头）
                csv_path = os.path.join(output_dir, csv_filename)
                with open(csv_path, 'w', encoding='utf-8-sig') as f:
                    f.write('\n'.join(csv_content))
                
                # 创建映射信息
                mapping = {
                    "placeholder": placeholder,
                    "csv_file": csv_filename,
                    "headers": headers,
                    "row_count": len(rows),
                    "csv_path": csv_path,
                    "csv_content": table_str
                }
                results.append(mapping)
                
            # 在每次循环内替换当前表格
            modified_content = replace_with_clean_blank(modified_content, table_str, (f"[TABLE_PLACEHOLDER:{placeholder}]","table"), mode)
        
        # 将所有表格信息写入一个JSON文件
        if mode == "placeholder":
            json_path = os.path.join(output_dir, "html_tables.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 将return语句移到循环外部
        return {
            "modified_content": modified_content,
            "tables": results
        }
                    
    def get_markdown_table(content, output_dir,mode):
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
            if mode == "placeholder":
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
                    "csv_path": csv_path,
                    "headers": headers,
                    "row_count": len(rows),
                    "original_content": matches
                }
                results.append(mapping)
                
            json_path = os.path.join(output_dir, "tables.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            # 在原文中进行占位替换
            modified_content = replace_with_clean_blank(modified_content, full_table, (f"[TABLE_PLACEHOLDER:{placeholder}]","table"))
                
            results.append({
                "csv_path": csv_path,
                "json_path": json_path,
                "placeholder": placeholder
            })
        else:
            modified_content = replace_with_clean_blank(modified_content, full_table, (f"[TABLE_PLACEHOLDER:{placeholder}]","table"))
            json_path = os.path.join(output_dir, "html_tables.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)     
        return {
            "modified_content": modified_content,
            "tables": results
        }
        
    def get_markdown_image(content, output_dir,mode):
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
            
            # 替换图片链接为占位符
            image_str = f"![{alt_text}]({url})"
            modified_content = replace_with_clean_blank(modified_content, image_str, (f"[IMAGE_PLACEHOLDER:{placeholder}]","image"),mode)
            
            results.append(mapping)
        
        json_path = os.path.join(output_dir, f"images.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return {
            "modified_content": modified_content,
            "images": results
        }

    def get_markdown_formula(content, output_dir,mode):
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
        easy_formula_count = 0
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        ########################行内公式#######################################
        # 处理行内公式
        for i, formula in enumerate(inline_pattern.findall(content)):
            if not formula.strip():  # 跳过空公式
                continue
                
            # 检查是否为简单公式
            if not FormulaProcessor.is_complex_formular(formula):
                # 简单公式，直接替换为Unicode字符
                try:
                    unicode_formula = unicodeitplus.replace(formula)
                except Exception as e:
                    print(f"公式转换错误: {formula}")
                    unicode_formula = formula
                if mode == "placeholder":
                    modified_content = replace_with_clean_blank(modified_content, f"${formula}$", (unicode_formula,"easy_formula"),mode)
                else:
                    modified_content = replace_with_clean_blank(modified_content, f"${formula}$", (f"[EASY_FORMULA_PLACEHOLDER:{easy_formula_count}]","easy_formula"),mode)
                    easy_formula_count += 1
            else:
                #复杂公式
                placeholder = f"formula_inline_{formula_count}"
                mapping = {
                    "placeholder": placeholder,
                    "type": "inline",
                    "formula": formula
                }
                
                results.append(mapping)
                formula_count += 1
                
                # 替换公式
                modified_content = replace_with_clean_blank(modified_content, f"${formula}$",(f"[FORMULA_PLACEHOLDER:{placeholder}]","complex_formular"),mode)
                
        
        # 处理块级公式
        for i, formula in enumerate(block_pattern.findall(content)):
            if not formula.strip():  # 跳过空公式
                continue
                
            # 检查是否为简单公式
            if not FormulaProcessor.is_complex_formular(formula.strip()):
                # 简单公式，直接替换为Unicode字符
                try:
                    unicode_formula = unicodeitplus.replace(formula.strip())
                except Exception as e:
                    print(f"公式转换错误: {formula}")
                    unicode_formula = formula
                if mode == "placeholder":
                    modified_content = replace_with_clean_blank(modified_content, f"$${formula}$$",(unicode_formula,"easy_formula"),mode)
                else:
                    modified_content = replace_with_clean_blank(modified_content, f"$${formula}$$",(f"[EASY_FORMULA_PLACEHOLDER:{easy_formula_count}]","easy_formula"),mode)
                    easy_formula_count += 1
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
                modified_content = replace_with_clean_blank(modified_content, f"$${formula}$$",( f"[FORMULA_PLACEHOLDER:{placeholder}]","complex_formula"),mode)
        
        # 合并所有复杂公式到一个json文件
        if formula_count > 0 and mode == "placeholder":
            json_path = os.path.join(output_dir, "formulas.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        
        return {
            "modified_content": modified_content,
            "formulas": results
        }

    def get_markdown_code_block(content, output_dir,mode):
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
            
            # 替换代码块为占位符
            modified_content = replace_with_clean_blank(modified_content, full_block, (f"[CODE_PLACEHOLDER:{placeholder}]","code"),mode)
            
            results.append(mapping)
        
        json_path = os.path.join(output_dir, f"codefile.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        return {
            "modified_content": modified_content,
            "code_blocks": results
        }
    def full_process(content, book_name, delete_mode=False,base_path=r"f:\graph_rag_enhance\clear_markdown_search"):
        """完整的内容处理流程"""
        import time
        start_time = time.time()
        
        if delete_mode:
            print("启用删除模式：将直接删除表格、图片、公式和代码块")
        
        table_output_dir = os.path.join(base_path,"table", book_name)
        code_output_dir = os.path.join(base_path,"code", book_name)
        image_output_dir = os.path.join(base_path,"image",book_name)
        formula_output_dir = os.path.join(base_path,"formula", book_name)

        # 0. 预处理：合并续表
        print("开始合并续表...")
        content = ContentExtractor.merge_continued_tables(content)
        print("续表合并完成")

        # 1. 先提取表格（此时表格内容是原始内容，写csv，正文替换为占位符）
        result = ContentExtractor.get_html_table(content, table_output_dir , delete_mode)
        content = result["modified_content"]

        # 2. 再对正文做代码块、图片、公式占位
        result = ContentExtractor.get_markdown_code_block(content, code_output_dir , delete_mode)
        content = result["modified_content"]

        result = ContentExtractor.get_markdown_image(content, image_output_dir , delete_mode)
        content = result["modified_content"]

        result = ContentExtractor.get_markdown_formula(content, formula_output_dir, delete_mode)
        content = result["modified_content"]
    
        end_time = time.time()
        print(f"[full_process] 内容处理耗时: {end_time - start_time:.2f} 秒")
        return content