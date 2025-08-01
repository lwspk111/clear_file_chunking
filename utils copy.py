import re
import logging
import time
import langid
from openai import OpenAI
import json
def basic_replace_with_clean_blank(content:str, target:str, placeholder:tuple):
    """
    替换content中的target为占位符或空行，保持行数对齐。
    placeholder: tuple, (占位符内容, 类型)；
    """
    #print(line_count,placeholder[0])
    flag = placeholder[1]
    if flag == "formula" or flag == "easy_formula":
        suffix = ""
    else:
            suffix ="\n"
    replacement = placeholder[0] + suffix  # 修复2：添加空行补足
    return content.replace(target, replacement, 1)
def replace_with_clean_blank(content:str, target:str, placeholder:tuple,mode:str):
    """
    替换content中的target为占位符或空行，保持行数对齐。
    placeholder: tuple, (占位符内容, 类型)；
    """
    if mode == "placeholder":
        return basic_replace_with_clean_blank(content, target, placeholder)
    elif mode == "delete":
        template = basic_replace_with_clean_blank(content, target,  placeholder)
        return template.replace(placeholder[0],"")
    else:
        raise TypeError("未知的模式")
def setup_logger():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def new_len(text):
    """计算文本长度，支持中英文"""
    language = langid.classify(text)[0]
  
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
def sent_to_llm(header,api_key,api_url,model_name):
    '''
    通过llm来检测header是否为标题
    header 是一个tuple,格式为 ([前n非空行的列表],"疑似小标题的行",[后n非空行的列表])
    '''
    content=""
    
    prompt = f'''
    你是一个书籍小标题判断专家,你的任务是根据上下文判断被<suspect_header><suspect_header>包裹的内容是否为小标题:
    内容: {content}
    请返回json格式的判断'''+r"{'content':<suspect_header>包裹的内容,'is_title':true/false}"
    
   

    client = OpenAI (api_key=api_key, 
                base_url=api_url)
    response = client.chat.completions.create(
    model=model_name,
    messages=[
        {'role': 'user', 
        'content': prompt}
    ],
    stream=False,
    response_format={"type": "json_object"}

    )
    '''
    for chunk in response:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content,1)
        if chunk.choices[0].delta.reasoning_content:
            print(chunk.choices[0].delta.reasoning_content,1)
    '''
    # 提取content字段并解析为字典
    content_json = response.choices[0].message.content
    content_dict = json.loads(content_json)
    print(content_dict)  # 现在content_dict就是所需的字典格式
# 常量定义
SLICE_POINT1 = "___slicepoint1___"
SLICE_POINT2 = "___slicepoint2___"
SLICE_POINT3 = "___slicepoint3___" 
if __name__ == "__main__":

    sent_to_llm((["aaa"],"bbb",["ccctest"]),api_key="sk-rkehllemffaoclgyjdsopvbzyczvbavlvgsgtekvfkydfwsr",api_url=r"https://api.siliconflow.cn/v1",model_name=r"Qwen/Qwen3-14B")
import json
