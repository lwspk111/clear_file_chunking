import re
import json
import os
import middle_editor
# 只以___slicepoint___为切割点 修改
SLICE_POINT = middle_editor.chunk_flag

class MarkdownChunker:
    """
    A class to chunk a Markdown document based on the SLICE_POINT marker only.
    """
    def __init__(self):
        pass
    @staticmethod
    def split_title(text):
        """
        从文本中提取第一个'\n\n'之前的内容作为标题，并返回剩余字符串
        输入: text - 包含标题和内容的原始字符串
        输出: (chunk_title, remaining) - 提取的标题和剩余文本组成的元组
        """
        index = text.find("\n\n")  # 查找第一个换行符的位置
        if index == -1:
            # 如果没有找到\n\n，整个文本作为标题
            return (text, "")
        else:
            # 提取第一个\n\n之前的内容作为标题
            chunk_title = text[:index]
            # 获取第一个\n\n之后的内容（+2跳过两个换行符）
            remaining = text[index + 2:]
            return (chunk_title, remaining)    
    '''
    def merge_toc_chunks(self, chunks: list) -> list:
        """
        合并目录chunks.
        
        Args:
            chunks: 原始chunks列表
            
        Returns:
            list: 合并后的chunks列表
        """
        merged_chunks = []
        # title_list = [] # 移除此行
        in_toc = False
        toc_content = []
        
        for chunk in chunks:
            content = chunk['content'].strip()
            
            # 检测到"目录"chunk时开始合并
            if content == "目录":
                # 如果之前有未合并的目录内容，先合并
                if in_toc and toc_content:
                    merged_chunks.append({
                        "chunk_id": f"chunk_toc_{len(merged_chunks)+1}",
                        "headings": [],
                        "content": "\n".join(toc_content)
                    })
                    toc_content = [] # 重置
                in_toc = True
                toc_content.append(chunk['content']) # 包含原始的"目录"内容
                continue
                
            # 在目录区域内进行合并
            if in_toc:
                # 使用get_title2的is_chapter_header检测是否是标题
                if is_chapter_header(content):
                    toc_content.append(chunk['content'])
                    
                    # 添加到title_json
                    # title_list.append({ # 移除此行
                    #     "book_name": "",
                    #     "title_id": len(title_list) + 1,
                    #     "title_content": content,
                    #     "title_level": [],  # 留空待未来更新
                    #     "depth": None       # 留空待未来更新
                    # }) # 移除此行
                else:
                    # 遇到非标题内容，结束目录合并，并添加已合并的目录chunk
                    in_toc = False
                    if toc_content: # 确保有内容才添加
                        merged_chunks.append({
                            "chunk_id": f"chunk_toc_{len(merged_chunks)+1}",
                            "headings": [],
                            "content": "\n".join(toc_content)
                        })
                        toc_content = [] # 重置
                    merged_chunks.append(chunk) # 添加当前的非目录chunk
            else:
                merged_chunks.append(chunk)
        
        # 处理循环结束后，如果还在目录区域内，则合并剩余的目录内容
        if in_toc and toc_content:
            merged_chunks.append({
                "chunk_id": f"chunk_toc_{len(merged_chunks)+1}",
                "headings": [],
                "content": "\n".join(toc_content)
            })
            
        return merged_chunks
'''
    def chunk(self, markdown_content: str) -> list:
        """
        Splits the markdown content by SLICE_POINT marker only.

        Args:
            markdown_content: A string containing the full Markdown document.

        Returns:
            A list of chunk dictionaries. Each dictionary contains:
            - chunk_id: A unique identifier for the chunk.
            - headings: An empty list (no heading detection).
            - content: The text content of the chunk.
        """
        # 以SLICE_POINT为分割点
        parts = markdown_content.split(SLICE_POINT)
        all_chunks = []
        chunk_id_counter = 0
        for part in parts:
            content = part.strip('\n')
            if not content:
                continue
            chunk_id_counter += 1
#            检查 split_title 是类方法，应使用类名调用或转换为实例方法，这里假设使用类名调用
            heading = MarkdownChunker.split_title(content)[0]
            content=  MarkdownChunker.split_title(content)[1]

            all_chunks.append({
                "chunk_id": f"chunk_{chunk_id_counter}",
                "headings": [heading],  # 修复：直接存储字符串列表
                "content": content
            })
        
        # 合并目录chunks并生成title_json
        return all_chunks # 移除 title_list

if __name__ == '__main__':
    # This assumes epub_to_markdown.py and get_title2.py have been run and its output is available.
    # The output path needs to match the one from the other script.

    
    # 推荐用get_title2.py处理后的文件
    markdown_file_path = r"F:\graph_rag_enhance\clear_markdown_search\test\makingsure.md"
    # os.path.join(base_output_dir, book_name, "marked.md")
    chunks_output_path = r"F:\graph_rag_enhance\clear_markdown_search\test\test02.json"
    # os.path.join(base_output_dir, book_name, "chunks.json")
    if not os.path.exists(markdown_file_path):
        print(f"错误: Markdown文件未找到: {markdown_file_path}")
        print("请先运行 get_title2.py 来生成该文件。")
    else:
        print(f"正在读取Markdown文件: {markdown_file_path}")
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chunker = MarkdownChunker()
        print("开始切分文档...")
        final_chunks = chunker.chunk(content)  # 不再接收 title_list
        print(f"切分完成，共得到 {len(final_chunks)} 个文本块。")
        
        # Save the chunks to a JSON file
        with open(chunks_output_path, 'w', encoding='utf-8') as f:
            # 在json.dump之前添加类型转换 # 移除下面所有 final_chunks 的处理
            # final_chunks = [
            #     {k: list(v) if isinstance(v, set) else v for k, v in chunk.items()}
            #     for chunk in final_chunks
            # ]
            # import pprint
            # pprint.pprint([type(v) for chunk in final_chunks for v in chunk.values()])
            # from collections.abc import Iterable
            
            # def deep_check(obj):
            #     if isinstance(obj, dict):
            #         for k, v in obj.items():
            #             print(f'Key:{k} Type:{type(v)}')
            #             deep_check(v)
            #     elif isinstance(obj, Iterable) and not isinstance(obj, str):
            #         for item in obj:
            #             print(f'Item Type:{type(item)}')
            #             deep_check(item)
            
        
            json.dump(final_chunks, f, indent=2, ensure_ascii=False)
        
        print(f"切分结果已保存到: {chunks_output_path}")

        # You can print a sample chunk to inspect

    # 保存title_json
    '''
    title_json_path = os.path.join(base_output_dir, book_name, "title.json")
    with open(title_json_path, 'w', encoding='utf-8') as f:
        json.dump({"title_list": title_list}, f, indent=2, ensure_
        '''
    """
    其他内容如chunk合并，文本连贯性检验，等待为了添加
    
    """