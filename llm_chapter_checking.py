import json
import os
from utils import SLICE_POINT1, SLICE_POINT2, SLICE_POINT3, SLICE_POINTLLM, new_len, sent_to_llm_ollama
import tqdm

def get_context(lines: list[str], idx: int, n: int = 3, line_content: str | None = None) -> str:
    """
    获取指定行前后n行的上下文
    """
    before_lines = []
    after_lines = []
    # 获取前面的非空行
    count = 0
    for j in range(idx-1, -1, -1):
        if lines[j].strip():
            before_lines.insert(0, lines[j].strip())
            count += 1
            if count >= n:
                break
    # 获取后面的非空行
    count = 0
    for j in range(idx+1, len(lines)):
        if lines[j].strip():
            after_lines.append(lines[j].strip())
            count += 1
            if count >= n:
                break
    # 构造上下文
    content = ""
    for before_line in before_lines:
        content += before_line + "\n"
    if line_content is not None:
        content += "<suspect_header>" + line_content + "</suspect_header>\n"
    for after_line in after_lines:
        content += after_line + "\n"
    return content

def llm_recheck_markdown(test01_path, test02_path, output_path, tooshort_level=20, api_key="", api_url="", model_name=""):
    """
    基于LLM的章节标题复查与订正主流程
    test01_path: 含占位符的完整md
    test02_path: 干净无占位符的md
    output_path: 输出最终修正后的md
    """
    with open(test01_path, "r", encoding="utf-8") as f:
        lines01 = f.readlines()
    with open(test02_path, "r", encoding="utf-8") as f:
        lines02 = f.readlines()
    assert len(lines01) == len(lines02), "两文件行数不一致，无法一一对应！"
    new_lines = []
    for i, (line1, line2) in enumerate(zip(lines01, lines02)):
        # 去除已有标记
        raw_line = line2.strip()
        flag = None
        if raw_line.startswith(SLICE_POINT1):
            flag = SLICE_POINT1
            content = raw_line[len(SLICE_POINT1):].strip()
        elif raw_line.startswith(SLICE_POINT2):
            flag = SLICE_POINT2
            content = raw_line[len(SLICE_POINT2):].strip()
        elif raw_line.startswith(SLICE_POINT3):
            flag = SLICE_POINT3
            content = raw_line[len(SLICE_POINT3):].strip()
        else:
            content = raw_line
        # 判断是否需要送入llm
        need_check = False
        if flag is not None or (content and new_len(content) <= tooshort_level):
            need_check = True
        if need_check:
            context = get_context(lines02, i, n=3, line_content=content)
            prompt = f"""
你是一个书籍小标题判断专家,你的任务是根据上下文判断被<suspect_header><suspect_header>包裹的内容是否为小标题:
内容: {context}
请返回json格式的判断{{'content':<suspect_header>包裹的内容,'is_title':true/false}}"""
            try:
                resp = sent_to_llm_ollama(prompt, api_key=api_key, api_url=api_url, model_name=model_name)
                if isinstance(resp, str):
                    resp = json.loads(resp)
                if resp is None:

                    is_title = False
                else:
                
                    is_title = resp.get("is_title", False)
                print(is_title,1)
            except Exception as e:
                is_title = False
                print("?",e)
            if is_title:
                # 标记为小标题，优先保留原有标记，否则用SLICE_POINTLLM
                if flag:
                    new_line = flag + content + "\n"
                else:
                    new_line = SLICE_POINTLLM + content + "\n"
            else:
                # 不是小标题，移除标记
                new_line = content + "\n"
        else:
            # 长正文或空行，直接用原始test01的内容
            new_line = line1
        new_lines.append(new_line)
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"已输出修正后的md到: {output_path}")

if __name__ == "__main__":
    # 读取llm.json
    config_path = r"F:\graph_rag_enhance\clear_markdown_search\all_to_markdown\test\llm.json"
    with open(config_path, "r", encoding="utf-8") as f:
        llm_config = json.load(f)
    api_key = llm_config.get("api_key", "")
    api_url = llm_config.get("api_url", "")
    model_name = llm_config.get("model_name", "")

    # 路径可自定义
    test01_path = r"F:\graph_rag_enhance\clear_markdown_search\test\test01.md"
    test02_path =  r"F:\graph_rag_enhance\clear_markdown_search\test\test02.md"
    output_path = r"F:\graph_rag_enhance\clear_markdown_search\test\final_llm_checked.md"

    llm_recheck_markdown(
        test01_path=test01_path,
        test02_path=test02_path,
        output_path=output_path,
        tooshort_level=20,
        api_key=api_key,
        api_url=api_url,
        model_name=model_name
    )

    
