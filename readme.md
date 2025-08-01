# Markdown内容处理工具包

这个工具包用于处理Markdown文档，包括内容提取、标题识别、公式处理等功能。


### 模块结构

```
all_to_markdown/
├── __init__.py              # 包初始化文件
├── main.py                  # 主程序入口
├── utils.py                 # 工具函数模块 (约50行)
├── roman_utils.py           # 罗马数字处理模块 (约50行)
├── formula_processor.py     # 数学公式处理模块 (约20行)
├── chapter_header.py        # 章节标题识别模块 (约150行)
├── content_extractor.py     # 内容提取器模块 (约400行)
├── text_processor.py        # 文本处理模块 (约100行)
├── README.md 
├── chunker.py               # 
  # 说明文档
```

### 各模块功能

1. **utils.py** - 通用工具函数
   - `replace_with_clean_blank()` - 替换内容并清理空行
   - `setup_logger()` - 配置日志
   - `new_len()` - 计算文本长度（支持中英文）
   - 常量定义（SLICE_POINT1, SLICE_POINT2, SLICE_POINT3）

2. **roman_utils.py** - 罗马数字处理
   - `RomanNum.IntToRoman()` - 整数转罗马数字
   - `RomanNum.generate_roman_numerals()` - 生成罗马数字集合
   - `RomanNum.normalize_roman_numerals()` - 标准化罗马数字

3. **formula_processor.py** - 数学公式处理
   - `FormulaProcessor.is_complex_formular()` - 判断复杂公式
   - `FormulaProcessor.restore_formular()` - 恢复公式格式

4. **chapter_header.py** - 章节标题识别
   - 多种标题识别规则（Markdown、文本、点号、括号等）
   - `ChapterHeader.rule_based_is_chapter_header()` - 基于规则的标题识别
   - `ChapterHeader.llm_based_is_chapter_header()` - 基于LLM的标题识别

5. **content_extractor.py** - 内容提取器
   - `ContentExtractor.get_html_table()` - 提取HTML表格
   - `ContentExtractor.get_markdown_table()` - 提取Markdown表格
   - `ContentExtractor.get_markdown_image()` - 提取图片
   - `ContentExtractor.get_markdown_formula()` - 提取数学公式
   - `ContentExtractor.get_markdown_code_block()` - 提取代码块
   - `ContentExtractor.full_process()` - 完整处理流程

6. **text_processor.py** - 文本处理
   - `process_text_file()` - 处理文本文件
   - `marking_title()` - 标记标题
   - `test0()` - 测试函数

7. **main.py** - 主程序入口
   - 提供使用示例

## 使用方法

### 方法1：使用包导入
```python
from all_to_markdown import test0, ChapterHeader

# 处理文件
input_path = "input.md"
output_path = "output.md"
test0(input_path, output_path)

# 章节标题识别
ChapterHeader.llm_based_is_chapter_header(output_path, "")
```

### 方法2：直接运行主程序
```bash
python main.py
```

### 方法3：使用原始方式（已废弃）
```python
# 原来的方式仍然可用，但建议使用新的模块化结构
from all_to_markdown import process_text_file
process_text_file("input.md", "output.md", True, "0")
```
### 工作流程
1. 输入文档
2. 标记小标题
3. 提取目录（代办）
4. 提取和保护数学公式，标准代码块，表格，图片
5. 切片
6，导出(代办)
## 优势

1. **模块化** - 每个模块职责单一，易于理解和维护
2. **可重用性** - 各个功能模块可以独立使用
3. **可测试性** - 每个模块都可以单独测试
4. **可扩展性** - 新增功能时只需要修改相应的模块
5. **代码清晰** - 从784行的大文件拆分成多个小文件，代码结构更清晰
# 未来更新记录
- 1. 对 chunker.py 增强切片逻辑
- 2. 使用简易的 人工标记模块
   - 1.输出一个机器友好且用户友好的分块后文档 以小标题标记为参考，输出chunk边界和识别出的目录边界，以及过滤器边界 ，以模拟为未来gui的 chunk边界手动添加删除和移动
- 3.为提取模块加入一个删除功能，在删除模式下删除数学公式，表格和图片不保留占位符，以避免latex数学公式 和非文本Unicode字符干扰 语言识别和小标题识别
- 4. 增强对于[1]文中引用，(引用) 图片/表格名称和的标注 使用<image_name><image_name>等方式，以避免其干扰字符识别和小标题机器-llm复查
- 5. 适配 epub和 markdown逐页处理模式， 对于不完整的页或者封面页以及版权页进行单独转储存先尝试自动模式，否则指定页码或者手动标记
- 6. 适配epub 和 markdown 的逐页处理模式，识别整页（文档）和跨页（文档）的目录 不误伤临近的前言和正文
- 7. 分析小标题，建立书籍的树章节结构和chunk位置（可以手动编辑，现在使用markdown列表，未来集成ui）
- 8. 切片后支持输出/ui导出 适配cherrystuido等传统切片功能不精的精修切片文档，把每个切片输出为单独markdown 在第一行添加其在书籍内的位置信息，方便llm定位
- 9. 开发 elctron ui 集成之前的文件功能
- 10. 集成
---
原始文件.md--> maintest.markingtitle()根据规初步小标题 标记直接衔接疑似小标题的行 --> test03.md（已实现）
test03.md 移除数学公式，表格，小标题，图片代码块 content_eatractpr.all_process删除模式--> test02.md（已实现）
test03.md 使用占位符数学公式，表格，小标题，图片代码块content_eatractpr.all_process占位符模式 --> test01.md
test01.md 和 test02.md 行数对齐（已实现）
test02.md 提供上下文，对哪些不确定的逐个行处理，重新进行订正 与占位符文件进行对照，得到llm校验过的文段(占位符)，--> test04.md （实现中）
> 检查是否是含目录的整书，如果是则根据过滤标准，标记为 filter chunk，在最终版本中移除被 chunk标记和 filter chunk标记包围的chunk，导出到额外的文件（未实现）
恢复占位符，统一小标题标记为单边界chunk标记 --> makingsure.md（未实现）
对 makingsure.md 提取所有的章节名称，chunk边界第一个\n\n 前的内容，作为一个章节小标题，按顺序输入到 contents.md（未实现）
发送 contents.md 到 llm 进行章节结构分析，由llm输出json，界定书籍的最终目录列表和层级（（未实现）），导出每个chunk单独的md文件以及其在书籍中的位置（未实现） 