#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除模式使用示例
"""

import os
import sys

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from all_to_markdown.content_extractor_trae import ContentExtractor

def main():
    """主函数"""
    
    # 示例内容
    content = """
# 基础生物化学

人类对生物大分子的研究经历了近两个世纪的漫长历史 (图 1-1)。由于生物大分子的结构复杂, 又易受温度、酸、碱的影响而变性, 给研究工作带来很大的困难。

## 表格示例

| 蛋白质 | 相对分子质量 | 亚基数 |
|--------|-------------|--------|
| 血红蛋白 | 64500 | 4 |
| 肌红蛋白 | 16900 | 1 |

## 公式示例

这是一个简单的公式：$E = mc^2$

这是一个复杂公式：

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

## 图片示例

![图 1-1 生物化学历史](image1.jpg)

## 代码示例

```python
def calculate_energy(mass, speed_of_light):
    return mass * speed_of_light ** 2
```

## 结论

这是结论段落。
"""

    print("原始内容：")
    print(content)
    print("\n" + "="*80 + "\n")
    
    # 使用删除模式
    print("删除模式处理后的内容：")
    result = ContentExtractor.full_process(content, "基础生物化学", delete_mode=True)
    print(result)
    
    print("\n" + "="*80 + "\n")
    print("删除模式完成！所有表格、图片、公式和代码块已被删除，但保持了行数对齐。")

if __name__ == "__main__":
    main() 