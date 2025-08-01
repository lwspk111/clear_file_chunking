#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的删除模式测试
"""

import re

def delete_with_line_preservation(content, target, element_type):
    """
    删除模式：删除目标内容但保持行数对齐
    
    参数:
        content (str): 原始内容
        target (str): 要删除的目标内容
        element_type (str): 元素类型（table, image, formula, code）
        
    返回:
        str: 删除后的内容
    """
    # 构造正则，匹配target前后可能的空行，确保删除后保持行数对齐
    pattern = re.compile(r'(\n?)([ \t]*\n)*' + re.escape(target) + r'([ \t]*\n)*(\n?)')
    
    def repl(match):
        before = match.group(1)
        after = match.group(4)
        # 删除模式：只保留前后的换行符，删除中间内容
        return before + after
    
    return pattern.sub(repl, content, count=1)

def test_delete_mode():
    """测试删除模式"""
    
    # 测试内容
    content = """# 测试文档

这是一个测试段落。

## 表格测试

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |

## 图片测试

![测试图片](test_image.jpg)

## 公式测试

这是一个行内公式：$E = mc^2$

这是一个块级公式：

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

## 代码块测试

```python
def hello_world():
    print("Hello, World!")
```

## 另一个段落

这是另一个测试段落。"""

    print("原始内容：")
    print(content)
    print("\n" + "="*50 + "\n")
    
    # 测试删除表格
    table_pattern = re.compile(r'(\|.*\|\n)((?:\|.*\|\n)+)')
    matches = table_pattern.findall(content)
    
    modified_content = content
    for i, (header_row, data_rows) in enumerate(matches):
        full_table = header_row + data_rows
        print(f"删除表格 {i+1}:")
        print(full_table)
        modified_content = delete_with_line_preservation(modified_content, full_table, "table")
    
    # 测试删除图片
    image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
    matches = image_pattern.findall(content)
    
    for i, (alt_text, url) in enumerate(matches):
        image_str = f"![{alt_text}]({url})"
        print(f"删除图片 {i+1}: {image_str}")
        modified_content = delete_with_line_preservation(modified_content, image_str, "image")
    
    # 测试删除公式
    inline_pattern = re.compile(r'\$(.*?)\$')
    block_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    
    for i, formula in enumerate(inline_pattern.findall(content)):
        formula_str = f"${formula}$"
        print(f"删除行内公式 {i+1}: {formula_str}")
        modified_content = delete_with_line_preservation(modified_content, formula_str, "formula")
    
    for i, formula in enumerate(block_pattern.findall(content)):
        formula_str = f"$${formula}$$"
        print(f"删除块级公式 {i+1}: {formula_str}")
        modified_content = delete_with_line_preservation(modified_content, formula_str, "formula")
    
    # 测试删除代码块
    code_block_pattern = re.compile(r'```(.*?)\n(.*?)```', re.DOTALL)
    matches = code_block_pattern.findall(content)
    
    for i, (language, code) in enumerate(matches):
        full_block = f"```{language}\n{code}```"
        print(f"删除代码块 {i+1}:")
        print(full_block)
        modified_content = delete_with_line_preservation(modified_content, full_block, "code")
    
    print("\n" + "="*50 + "\n")
    print("删除模式处理后的内容：")
    print(modified_content)

if __name__ == "__main__":
    test_delete_mode() 