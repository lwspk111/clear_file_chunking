import time
from utils import setup_logger, SLICE_POINT1, SLICE_POINT2, SLICE_POINT3
from content_extractor import ContentExtractor
from chapter_header import ChapterHeader

logger = setup_logger()

def process_text_file(input_path: str, output_path: str, work_mode: bool, log_version):
    """
    读取输入文件，标记章节，并写入输出文件。

    Args:
        input_path (str): 输入文件的路径。
        output_path (str): 输出文件的路径。
        work_mode: 设置为0 时，为SLICE_POINT换行模型 设置为1时，为不换行标记模式
        log_version: 日志版本
    """
    start_time = time.time()
 
    if log_version == "0":
        print(f"正在处理文件: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}", "line=568")
        return
    
    content = ContentExtractor.full_process(content, book_name="基础生物化学")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}", "line=568")
        return
    
    end1_time = time.time()
    print("标记数学公式等用时", end1_time - start_time)
    marking_title(input_path, output_path, work_mode, log_version)
    end2_time = time.time()
    print("标记标题等用时", end2_time - end1_time)

def marking_title(input_path, output_path, work_mode, log_version):
    """标记标题功能"""
    if work_mode:
        suffix = ""
    else:
        suffix = "\n"
    
    processed_lines = []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}", "line=577")
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
        if ChapterHeader.rule_based_is_chapter_header(line_content, work_mode)[0]:
            # 添加标记，并保留原行
            # \n 确保标记和原标题在不同行
            code = ChapterHeader.rule_based_is_chapter_header(line_content, work_mode)[1]
            if code == 0:
                flag = SLICE_POINT1
            elif code == 1:
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
        print(f"写入文件时发生错误: {e}", "line=609")

def test0(input_path, output_path):
    """测试函数"""
    total_start = time.time()
    process_text_file(input_path, output_path, 0, log_version=0)
    total_end = time.time()
    print(f"[main] 程序总耗时: {total_end - total_start:.2f} 秒") 

if __name__ == "__main__":
    # --- 使用示例 ---
    
    input_path = r"E:\Mybook_libaray\植物生理学_(王小菁)_(Z-Library)_2025-07-29 20_13_13\植物生理学_王小菁_Z-Library_.md"
    output_path1 = r"F:\graph_rag_enhance\clear_markdown_search\test\test01.md"
    output_path2 =r"F:\graph_rag_enhance\clear_markdown_search\test\test02.md"
    output_path3 =r"F:\graph_rag_enhance\clear_markdown_search\test\test03.md"
    
    marking_title(input_path,output_path3,1,0)    
    with open(file=output_path3,mode="r",encoding="utf-8") as f:
        content = f.read()
    content1=ContentExtractor.full_process(content,book_name="基础生物化学",delete_mode="placeholder")
    content2 =ContentExtractor.full_process(content,book_name="基础生物化学",delete_mode="delete")

    with open(file = output_path1,mode="w",encoding="utf-8")as f:
        f.write(content1)
    with open(file = output_path2,mode="w",encoding="utf-8")as f:
        f.write(content2)

    
     