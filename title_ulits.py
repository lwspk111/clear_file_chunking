import base64
import re
import os
import shutil
# 添加在文件顶部导入区
import logging

# 配置日志
def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

logger = setup_logger()
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
        romans = IntToRoman(i)
        roman_numerals.add(romans[0])  # Uppercase
        roman_numerals.add(romans[1])  # Lowercase
    return roman_numerals

# Generate Roman numerals up to 50, which should be sufficient for most books.
ROMAN_NUMERALS = generate_roman_numerals(50)

# Unicode Roman numerals to ASCII mapping
UNICODE_ROMAN_MAP = {
    'Ⅰ': 'I', 'Ⅱ': 'II', 'Ⅲ': 'III', 'Ⅳ': 'IV', 'Ⅴ': 'V', 'Ⅵ': 'VI', 'Ⅶ': 'VII', 'Ⅷ': 'VIII', 'Ⅸ': 'IX', 'Ⅹ': 'X', 'Ⅺ': 'XI', 'Ⅻ': 'XII',
    'ⅰ': 'i', 'ⅱ': 'ii', 'ⅲ': 'iii', 'ⅳ': 'iv', 'ⅴ': 'v', 'ⅵ': 'vi', 'ⅶ': 'vii', 'ⅷ': 'viii', 'ⅸ': 'ix', 'ⅹ': 'x', 'ⅺ': 'xi', 'ⅻ': 'xii',
    'Ⅼ': 'L', 'Ⅽ': 'C', 'Ⅾ': 'D', 'Ⅿ': 'M',
    'ⅼ': 'l', 'ⅽ': 'c', 'ⅾ': 'd', 'ⅿ': 'm'
}

def normalize_roman_numerals(text: str) -> str:
    """Replaces Unicode Roman numerals with their ASCII equivalents."""
    for uni, asc in UNICODE_ROMAN_MAP.items():
        text = text.replace(uni, asc)
    return text

# 定义章节分割标记
SLICE_POINT = "___slicepoint___"

# 定义匹配章节标题的规则
# 规则2：关键词列表
# 使用集合(set)以便快速查找
TITLE_KEYWORDS = {
    "前言", "序言", "序", "引言", "目录", "摘要",
    "后记", "跋", "参考文献", "附录","返回目录","索引","附表",""
}

# 预编译正则表达式以提高性能
# 将多个正则表达式规则放入一个列表
REGEX_PATTERNS = [
  
    # 规则4: 常见的章节特征
    # (第[一二三...]+章 | Chapter \d+ | (一) | （一）)
    re.compile(r'^\s*(第[一二三四五六七八九十百千万\d]+\s*[章卷篇节编回]|(C|c)hapter\s*\d+|[（(][一二三四五六七八九十百千万\d]+[）)])'),

    # 规则5: 多级数字序列号 (e.g., 1.2, 1.2.3)
    # 匹配至少含有一个点号的数字序列
    re.compile(r'^\s*\d+(\.\d+)+.*')
    # 更多章节特征
]
def is_markdown_chapter(content, work_mode):
    """
    判断markdown格式的标题
    content 为内容
    workmode==1 意味着处于后处理#后无空鼓情况
    workmode==0 意味着处于标准情况#后有空格
    """
    # 标准模式：# 后必须有空格
    if work_mode == 0:
        pattern = r'^\s*(#+) +.+$'
    # 后处理模式：# 后无空格
    elif work_mode == 1:
        pattern = r'^\s*(#+)[^#\s].*$'
    else:
        return False
    
    return bool(re.match(pattern, content))
def is_offical_header(clean_line):
    for pattern in REGEX_PATTERNS:
        if pattern.match(clean_line):
            return True
    return False
def is_chapter_header(line: str,work_mode:bool) -> bool:
    """
    判断给定行是否为章节标题。
    
    Args:
        line (str): 要检查的文本行。

    Returns:
        bool: 如果是章节标题则返回 True，否则返回 False。
    """
    # 去除行首尾的空白字符
    clean_line = line.strip()

    # 如果是空行，则不是标题
    if not clean_line:
        return False

    # 规则2: 检查是否为关键词标题
    if clean_line in TITLE_KEYWORDS:
        return True
    
    # Normalize for Roman numeral check
    normalized_line = normalize_roman_numerals(clean_line)

    # 新增规则：检查是否为有效的罗马数字（替换了原有的正则匹配）
    if normalized_line in ROMAN_NUMERALS:
        return True

    # 检查所有正则表达式规则
    if is_offical_header(clean_line):
        return True
    if is_markdown_chapter(clean_line,work_mode):
        return True
    return False

def process_text_file(input_path: str, output_path: str,work_mode:bool,log_version):
    """
    读取输入文件，标记章节，并写入输出文件。

    Args:
        input_path (str): 输入文件的路径。
        output_path (str): 输出文件的路径。
    work_mode 设置为0 时，为SLICE_POINT换行模型 设置为1时，为不换行标记模式
    """
    if work_mode:
        suffix = ""
    else:
        suffix = "\n"
    if log_version=="0":
        print(f"正在处理文件: {input_path}")
     
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return

    processed_lines = []
    # 逐行处理
    for line in lines:
        # 去除行尾的换行符以便处理
        line_content = line.rstrip('\n')

        # 检查是否已被标记，防止重复标记
        if line_content.strip() == SLICE_POINT:
            processed_lines.append(line)
            continue

        # 判断是否为章节标题
        if is_chapter_header(line_content,work_mode):
            # 添加标记，并保留原行
            # \n 确保标记和原标题在不同行
            processed_lines.append(f"{SLICE_POINT}{suffix}")
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
        print(f"写入文件时发生错误: {e}")
# 添加文件行范围删除函数
def remove_lines_between(file_path: str, start_line: int, end_line: int, output_path: str = None) -> bool:
    print(start_line,end_line,"a")
    """
    删除文件中指定行号范围（包含起止行）的内容
    Args:
        file_path: 输入文件路径
        start_line: 起始行号（0-based）
        end_line: 结束行号（0-based）
        output_path: 输出文件路径，None表示覆盖原文件
    Returns:
        操作是否成功
    """
        
    if (start_line < 0 or end_line < start_line) and end_line != -2:
        logger.error(f"无效的行号范围: start_line={start_line}, end_line={end_line}")
        return False
    elif end_line == -2:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(" ")
            logger.error(f"检测到全部为目录，返回空文件")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return False

    if end_line >= len(lines):
        logger.warning(f"结束行号超出文件总行数，将删除到文件末尾")
        end_line = len(lines) - 1

    # 保留不在删除范围内的行
    new_lines = lines[:start_line] + lines[end_line+1:]

    # 确定输出路径
    output_path = output_path or file_path

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        logger.info(f"成功删除行 {start_line}-{end_line}，结果已保存到: {output_path}")
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return False

def find_directory_section(file_path: str,log_version) -> tuple:

    """
    定位目录区间的起止行号并删除目录行之前的所有内容
    Args:
        file_path: 待处理文件路径
    Returns:
        (start_line, end_line) 元组
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            stripped_lines = [line.strip() for line in f.readlines()]
    except Exception as e:
        logger.error(f"文件读取失败: {e}")
        return (-1, -1)

    start_line = -1
    first_title_line_data = -1
    deleted_lines = 0  # 累计删除的行数
    # step1：查找目录起始行
    for meum_line_numer, line in enumerate(stripped_lines):
        if line.startswith(f"{SLICE_POINT}#目录"):
            start_line = meum_line_numer
            break

    # 如果找到目录行，则删除该目录行及其之前的所有内容
    if start_line != -1:
        # 使用通用工具函数删除行范围
        remove_lines_between(file_path, 0, start_line)
        deleted_lines += start_line + 1  # 累加删除的行数
    else:
        logger.warning("未找到目录行，不执行删除操作")
    
    # step2 在 # 目录 或者 目录 后继续寻找第一个正文小标题
    first_title_line_temp = -1  # 初始化变量
    first_title_flag = None
    first_title_line_data = -1
  
    with open(file_path, "r", encoding='utf-8') as f:
        stripped_lines = [line.strip() for line in f.readlines()]
        for first_title_line_line_number, line in enumerate(stripped_lines):
            
            # 动态获取标记后的内容，避免硬编码偏移量
            slice_index = line.find(SLICE_POINT)
            if slice_index != -1:
                content_after_slice = line[slice_index + len(SLICE_POINT):].strip()
                cleaned_content = content_after_slice.replace("#", "")
                if is_offical_header(cleaned_content):
                
                # 第一个目录中的小标题
                
                    first_title_flag = line
                    first_title_line_data = first_title_line_line_number + start_line
                    first_title_line_temp = first_title_line_line_number
                    break
    
    # 修复逻辑判断和警告位置
    if start_line != -1 and first_title_line_temp != -1:
        remove_lines_between(file_path, 0, first_title_line_temp)
        deleted_lines += first_title_line_temp + 1  # 累加删除的行数
    elif start_line != -1:
        logger.warning("未找到第一个小标题，不执行删除操作")
    final_title_line_data = -1
    if first_title_flag is not None:
        with open(file_path, "r", encoding='utf-8') as f:
            stripped_lines = [line.strip() for line in f.readlines()]
            
            for final_title_line_line_number, line in enumerate(stripped_lines):
                # 提取标记后的内容进行比较
                slice_index_flag = first_title_flag.find(SLICE_POINT)
                content_flag = first_title_flag[slice_index_flag + len(SLICE_POINT):].strip().replace("#", "")
                slice_index_line = line.find(SLICE_POINT)
                content_line = line[slice_index_line + len(SLICE_POINT):].strip().replace("#", "").strip() if slice_index_line != -1 else line.strip().replace("#", "")
                if log_version:
                    print(content_line,content_flag)    
                if (content_flag == content_line or 
                    content_flag in content_line or 
                    content_line in content_flag)and not len(content_line)==0:
                    # 第一个正文中的小标题，意味着发生了正文重现
                    # 修正行号计算，考虑所有删除操作的累积影响
                    final_title_line_data = final_title_line_line_number + deleted_lines
                    break
                
                    
    else:
        logger.warning("未找到正文小标题，不执行删除操作")
     
    return (start_line, final_title_line_data)
def all_page_is_directoru():
    pass

def preprocess_file(input_path: str, output_path: str):
    """
    对文件进行预处理，删除行内数学公式和所有空格
    
    Args:
        input_path (str): 输入文件路径
        output_path (str): 输出文件路径
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 删除行内数学公式（$...$格式）
        content = re.sub(r'\$.*?\$', '', content)
        
        # 删除所有空格
        content = content.replace(' ', '')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"预处理完成: {output_path}")
    except Exception as e:
        print(f"预处理文件时发生错误: {e}")

# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 使用示例 ---


  
    input_filename = r"C:\Users\pubgc\MinerU\[OCR]_园林树木学 (陈有民主编, 陈有民主编, 陈有民) (Z-Library) - 副本_20250528_1320.layered.pdf-9bedb6dd-bd2e-40a9-9df2-9a7ae1a19cab\full.md"
    base_path=r"G:\graph_rag_enhance\short_unit_code\epub_to_markdown\output\园林树木学1"
    '''
    # 复制文件生成A.md和B.md
    a_md_path = os.path.join(base_path,"A.md")
    b_md_path = os.path.join(base_path,"B.md")
    os.makedirs(base_path, exist_ok=True)
    shutil.copy2(input_filename, a_md_path)
    shutil.copy2(input_filename, b_md_path)
    print(f"已创建文件副本: {a_md_path}, {b_md_path}")
    
    # 对A.md进行预处理
    preprocess_file(a_md_path,os.path.join(base_path,a_md_path))  # 直接覆盖原A.md文件
    process_text_file(a_md_path,a_md_path,1,log_version=0)
    print("1")
    directory_range=find_directory_section(a_md_path,log_version=1)
    # 完成最终处理,移除目录
    print(directory_range,"f")
    remove_lines_between(b_md_path,directory_range[0],directory_range[1],b_md_path)
    # 完成切块工作
    
    input_path = r"G:\MinerU_1.3.5\MinerU\output\思想道德与法治_2023年版_(高等教育出版社)_(Z-Library)\auto\思想道德与法治_2023年版_(高等教育出版社)_(Z-Library).md"
    output_path = r"G:\graph_rag_enhance\short_unit_code\epub_to_markdown\output\思想道德与法治"
    # 未来衔接预览接口
    process_text_file(input_path,output_path,0,log_version=0)
   '''
print(162.25/611544)
