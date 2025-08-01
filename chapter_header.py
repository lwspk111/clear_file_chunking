from ast import main
import re
from roman_utils import RomanNum, ROMAN_NUMERALS
from utils import SLICE_POINT1, SLICE_POINT2, SLICE_POINT3,new_len
import utils

class ChapterHeader:
    """
    章节标题识别工具类
    提供多种规则判断文本行是否为章节标题，支持中英文关键词、Markdown格式、数字编号等类型
    """
  
    # 中文章节标题关键词集合(常见文献章节名称)
    TITLE_KEYWORDS_ch = {
        "前言", "序言", "序", "引言", "目录", "摘要",
        "后记", "跋", "参考文献", "附录","返回目录","索引","附表","习题","思考题"
    }
    
    # 英文章节标题关键词集合(常见文献章节名称)
    TITLE_KEYWORDS_en = {
        "preface", "introduction", "contents", "abstract",
        "epilogue", "afterword", "references", "appendix", "back to contents", "index", "table of contents"
    }
    
    is_markdown_chapter_mode0 = re.compile(r'^\s*(#+)\s+.+$')
    is_markdown_chapter_mode1 = re.compile(r'^\s*(#+)[^#\s].*$')
    is_text_type_header_model = re.compile(r'.*?\b(第[一二三四五六七八九十百千万\d]+\s*[章卷册篇节编回]|(C|c)hapter\s*\d+|[（(][一二三四五六七八九十百千万\d]+[）)])\b')
    is_point_type_header_model = re.compile(r'^\s*\d+(?:\.\d+)*\.?\s+.*')
    is_bracket_header_model = re.compile(r'^[\(\（][\d一二三四五六七八九十百千万][\)\）]')
# 移除结尾的$，允许括号后有任意内容
    # 在类定义中添加新属性
    is_chinese_number_header_model = re.compile(r'^\s*[一二三四五六七八九十百千万]+、.*')

# 添加新的方法来检查这些标题类型
    def line_remove(line):
        """移除行中的中文数字+顿号"""
        
        count = 0
        for i, char in enumerate(line):
            if char.isdigit():
                count += 1
            else:
                count=i  # 从第一个非数字字符开始返回
                break
        temple= line[count:]  # 如果所有字符都是数字，则返回空字符串
        count = 0
        flag={".","-","_",'…'}
        for i in range(len(temple) - 1, -1, -1):  # 从后往前遍历
            if (temple[i].isdigit() or temple[i] in flag):
                count += 1
            else:
                break  # 遇到非数字字符或已移除足够数量的数字
        return temple[:len(temple) - count]  # 返回截取后的字符串 # 如果所有字符都是数字，则返回空字符串
    def is_chinese_number_header(clean_line):
        """匹配中文数字+顿号的标题"""
        return bool(re.match(ChapterHeader.is_chinese_number_header_model, clean_line))
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
        pattern = ChapterHeader.is_markdown_chapter_mode0
        return bool(re.match(pattern, content))

    def is_text_type_header(clean_line):
        """匹配类似第一章 chapter1等文本类型的标题"""
        return bool(re.match(ChapterHeader.is_text_type_header_model, clean_line))
    
    def is_point_type_header(clean_line):
        """匹配类似1.1 1.2 等点号类型的标题"""
        return bool(re.match(ChapterHeader.is_point_type_header_model, clean_line))
    
    def is_keyword_header(clean_line):
        """
        检查是否为关键词类型标题

        Args:
            clean_line (str): 清洗后的文本行

        Returns:
            bool: 属于关键词标题返回True，否则返回False
        """
        # 移除空字符串匹配并添加大小写不敏感检查
        return (clean_line.strip().lower() in [kw.lower() for kw in ChapterHeader.TITLE_KEYWORDS_ch] or 
                clean_line.strip().lower() in [kw.lower() for kw in ChapterHeader.TITLE_KEYWORDS_en])
    
    def is_roman_numeral_header(clear_line):
        """检查是否为罗马数字标题"""
        if clear_line in ROMAN_NUMERALS:
            return True
        else:
             return False
    
    def is_bracket_header(clear_line):
        """检查括号类型的小标题 如 （一） (1)"""
        return bool(re.match(ChapterHeader.is_bracket_header_model, clear_line))

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
            return (False, 3)

        normalized_line = RomanNum.normalize_roman_numerals(clean_line)

        # 按优先级顺序检查各规则(关键词标题优先级最高)
   
        if ChapterHeader.is_markdown_chapter(clean_line, work_mode):
            return (True, 0)  # markdown
        elif (
        ChapterHeader.is_text_type_header(clean_line) or
        ChapterHeader.is_roman_numeral_header(normalized_line) or 
        ChapterHeader.is_chinese_number_header(clean_line) or
        ChapterHeader.is_chinese_number_header(utils.line_remove(clean_line)) or
        ChapterHeader.is_keyword_header(clean_line) or 
        ChapterHeader.is_keyword_header(utils.line_remove(clean_line))  or
        ChapterHeader.is_text_type_header(utils.line_remove(clean_line))
        ):
            return (True, 1)  # 文本+
        elif (ChapterHeader.is_point_type_header(clean_line) or 
        ChapterHeader.is_bracket_header(clean_line) or ChapterHeader.is_bracket_header(utils.line_remove(clean_line))
        ):
            return (True, 2)  # 点+括号
        else:
            return (False, 3)
       

if __name__ == "__main__":
    print(ChapterHeader.line_remove(r"1.1.3 第四节 ${\mathrm{C}}_{3}\text{、}{\mathrm{C}}_{4}$ 与 CAM 植物的光合特性比较"))