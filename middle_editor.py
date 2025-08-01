import utils
chunk_flag = "<--chunk_boundary-->"
flags = {utils.SLICE_POINT1, utils.SLICE_POINT2, utils.SLICE_POINT3}

def make_middle_edit_file(input_path, output_path):
    '''
    生成中间编辑文件
    1.将所有SLICE_POINT1/2/3统一替换为chunk_flag，写入output_path
    '''
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        line_strip = line.strip()  # 去除首尾空白
        if line_strip in flags:
            new_lines.append(chunk_flag + '\n')
        else:
            # 也要处理行内出现的分割标记（极少数情况）
            for flag in flags:
                if flag in line:
                    line = line.replace(flag, chunk_flag)
                    print("warn")
            new_lines.append(line)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
input_path = r"F:\graph_rag_enhance\clear_markdown_search\test\test02.md"
output_path = r"F:\graph_rag_enhance\clear_markdown_search\test\makingsure.md"
make_middle_edit_file(input_path,output_path)