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


# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 使用示例 ---
    input_filename = r"C:\Users\pubgc\MinerU\[OCR]_园林树木学 (陈有民主编, 陈有民主编, 陈有民) (Z-Library) - 副本_20250528_1320.layered.pdf-9bedb6dd-bd2e-40a9-9df2-9a7ae1a19cab\full.md"
    base_path=r"G:\graph_rag_enhance\short_unit_code\epub_to_markdown\output\园林树木学1"
    
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
    
    