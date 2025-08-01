from ast import Slice
import re
import logging
import time
import langid
from openai import OpenAI

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
def sent_to_llm(content:str,api_key:str,api_url:str,model_name:str):
    '''
    通过llm来检测header是否为标题
    header 是一个tuple,格式为 ([前n非空行的列表],"疑似小标题的行",[后n非空行的列表])
    '''
    client = OpenAI(api_key=api_key, base_url=api_url)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {'role': 'user', 
            'content': content}
        ],
        stream=False,
        response_format={"type": "json_object"}
    )
    
    # 非流式响应的正确处理方式
    return response.choices[0].message.content
def sent_to_llm_ollama(content: str, api_key: str, api_url: str, model_name: str):
    '''
    通过 Ollama 来检测 header 是否为标题
    返回格式: {"content": "原文内容", "is_title": true/false}
    '''
    from ollama import chat
    from pydantic import BaseModel
    import json

    class TitleDetection(BaseModel):
        content: str  # 疑似标题的内容
        is_title: bool  # 是否为标题

    try:
        response = chat(
            messages=[
                {
                    'role': 'user',
                    'content': content,
                }
            ],
            model=model_name,
            format=TitleDetection.model_json_schema(),
        )
        
        # 解析响应
        result = TitleDetection.model_validate_json(response.message.content)
        
        # 转换为字典格式，保持与原有代码的兼容性
        return {
            "content": result.content,
            "is_title": result.is_title
        }
        
    except Exception as e:
        print(f"Ollama 调用失败: {e}")
        return {
            "content": "",
            "is_title": False
        }

         
# 常量定义
SLICE_POINT1 = "___slicepoint1___"
SLICE_POINT2 = "___slicepoint2___"
SLICE_POINT3 = "___slicepoint3___" 
SLICE_POINTLLM="___slicepointM___"
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
if __name__ == "__main__":
    import ollama