# 输入 epub 输出 markdown 并处理图片和数学公式  
# 然后 ocr 图片 如果是数学公式和表格就插入进去 否则跳过
# ocr 模型： miner-u  
import os
import re
import zipfile
import shutil
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from PIL import Image  # 添加Pillow库导入

def epub_to_markdown(epub_path, output_dir,contex_n=2):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    md_dir = os.path.join(output_dir, "markdown")
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    
    image_counter = 1
    image_mapping = {}
    
    # 创建临时解压目录（使用绝对路径）
    temp_dir = os.path.join(os.path.abspath(output_dir), "temp_epub")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 解压EPUB文件（绝对路径处理）
    with zipfile.ZipFile(os.path.abspath(epub_path), 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # 定位OPF文件（处理不同的EPUB结构）
    opf_path = find_opf_file(temp_dir)
    if not opf_path or not os.path.exists(opf_path):
        raise FileNotFoundError("无法找到EPUB的OPF内容描述文件")
    
    print(f"找到OPF文件: {opf_path}")
    content_dir = os.path.dirname(opf_path)
    
    # 解析OPF获取内容顺序
    content_order = parse_opf_contents(opf_path)
    if not content_order:
        raise ValueError("EPUB内容清单为空")
    
    print(f"解析到 {len(content_order)} 个内容文件")
    
    all_md_content = []
    # 处理所有内容文件
    for i, content_file in enumerate(content_order):
        # 构建内容文件的绝对路径
        content_path = os.path.normpath(content_file)
        if not os.path.exists(content_path):
            print(f"警告: 文件未找到, 跳过: {content_path}")
            continue
            
        print(f"处理文件 ({i+1}/{len(content_order)}): {os.path.basename(content_path)}")
        
        # 读取并解析HTML内容
        with open(content_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 转换当前文件内容
        md_content, img_counter = convert_html_to_markdown(
            html_content, 
            content_path,
            img_dir,
            md_dir,
            image_counter,
            image_mapping
        )
        
        image_counter = img_counter  # 更新全局图片计数器
        all_md_content.append(md_content)

    # 保存为单一的Markdown文件
    output_md_path = os.path.join(output_dir, "output.md")
    with open(output_md_path, 'w', encoding='utf-8') as md_file:
        md_file.write("\n\n---\n\n".join(all_md_content))
    print(f"所有内容已合并到: {output_md_path}")

    # 保存图片映射关系
    mapping_path = os.path.join(output_dir, 'image_mapping.json')
    with open(mapping_path, 'w', encoding='utf-8') as map_file:
        json.dump(image_mapping, map_file, indent=2)
    
    print(f"图片映射已保存到: {mapping_path}")
    print({temp_dir})
    
    # 清理临时文件
    try:
        shutil.rmtree(temp_dir)
        print(f"清理临时目录: {temp_dir}")
    except Exception as e:
        print(f"清理临时目录失败: {str(e)}")
    
    return f"转换完成: 处理了 {len(content_order)} 个文件, {len(image_mapping)} 张图片"

def is_heading(element):
    """
    Heuristically checks if an element is a heading.
    Returns heading level (1-6) or 0 if not a heading.
    """
    if element.name in [f'h{i}' for i in range(1, 7)]:
        return int(element.name[1])

    # Check for style-based headings in <p> or <div> tags
    if element.name in ['p', 'div']:
        # 1. Check class names
        class_names = element.get('class', [])
        for c in class_names:
            c_lower = c.lower()
            if 'heading' in c_lower or 'title' in c_lower:
                # Try to extract a level number from the class name
                level_match = re.search(r'(\d+)$', c_lower)
                if level_match:
                    level = int(level_match.group(1))
                    return min(level, 6) # cap at level 6
                return 2 # Default to level 2 for generic "heading" or "title" class

        # 2. Check style attributes
        style = element.get('style', '').lower().replace(' ', '')
        
        is_bold = 'font-weight:bold' in style or 'font-weight:700' in style
        is_centered = 'text-align:center' in style
        
        # Check for large font size
        font_size_match = re.search(r'font-size:(\d+(\.\d+)?)(pt|px|em)', style)
        is_large_font = False
        if font_size_match:
            size = float(font_size_match.group(1))
            unit = font_size_match.group(3)
            # Define "large" based on unit. These are arbitrary thresholds.
            if (unit == 'pt' and size > 14) or \
               (unit == 'px' and size > 18) or \
               (unit == 'em' and size > 1.2):
                is_large_font = True

        if is_large_font and is_bold:
            return 2 # Large and bold is a strong indicator
        if is_centered and is_bold:
            return 2 # Centered and bold is also a strong indicator
        if is_large_font:
            return 3 # Just large font
        if is_bold:
            return 3 # Just bold
            
    return 0 # Not a heading

def recursive_process_element(element, md_lines_collector, img_dir, md_dir, img_mapping, current_img_counter, content_path):
    """Recursively processes HTML elements to convert to Markdown, handling text and images."""
    new_img_counter = current_img_counter

    if element.name is None:  # NavigableString (text node)
        text = element.string.strip() if element.string else ""
        if text:
            # Append text, ensuring space separation if needed
            if md_lines_collector and md_lines_collector[-1] and not md_lines_collector[-1].endswith(('\n', ' ')):
                md_lines_collector.append(' ')
            md_lines_collector.append(text)
        return new_img_counter

    # Handle specific element types
    if element.name == 'img' and 'src' in element.attrs:
        img_src = element['src']
        img_abs_path = resolve_image_path(content_path, img_src)

        if os.path.exists(img_abs_path):
            # 移除原图片扩展名获取代码，直接使用.png
            # img_ext = os.path.splitext(img_abs_path)[1].lower()
            img_filename = f"image_{current_img_counter:04d}.png"
            img_dest = os.path.join(img_dir, img_filename)
            try:
                # 使用Pillow转换图片为PNG
                with Image.open(img_abs_path) as img:
                    # 处理透明背景
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else img.info['transparency'])
                        background.save(img_dest, 'PNG')
                    else:
                        img.convert('RGB').save(img_dest, 'PNG')
                print(f"  转换并保存图片: {os.path.basename(img_abs_path)} -> {img_filename}")
                rel_path = os.path.relpath(img_dest, md_dir)
                img_mapping[current_img_counter] = {
                    "orig_path": img_abs_path,
                    "new_path": img_dest,
                    "rel_path": rel_path
                }
                # Ensure proper newlines around image tags
                if md_lines_collector and md_lines_collector[-1] and not md_lines_collector[-1].endswith('\n\n'):
                    if not md_lines_collector[-1].endswith('\n'):
                        md_lines_collector.append('\n')
                    md_lines_collector.append('\n')
                md_lines_collector.append(f"![Image {current_img_counter}]({rel_path})\n\n")
                new_img_counter = current_img_counter + 1  # Increment counter for the next image
            except Exception as e:
                print(f"  图片转换失败，使用原始图片: {img_abs_path} -> {img_filename}: {str(e)}")
                shutil.copy2(img_abs_path, img_dest)  # 转换失败时回退到复制原始图片
        else:
            print(f"  图片文件不存在: {img_abs_path}")
            md_lines_collector.append(f"<!-- 丢失图片: {img_src} -->\n\n")
        return new_img_counter # Images don't have children to process for text

    heading_level = is_heading(element)
    if heading_level > 0:
        text = element.get_text(strip=True) # Extracts all text, including from children like <span>
        if text:
            if md_lines_collector and md_lines_collector[-1] and not md_lines_collector[-1].endswith('\n\n'):
                if not md_lines_collector[-1].endswith('\n'):
                    md_lines_collector.append('\n')
                md_lines_collector.append('\n')
            md_lines_collector.append(f"{'#' * heading_level} {text}\n\n")
        return new_img_counter # Text handled, no further recursion needed for children's text content

    elif element.name == 'table':
        # Simple table conversion to Markdown
        if md_lines_collector and md_lines_collector[-1] and not md_lines_collector[-1].endswith('\n\n'):
            md_lines_collector.append('\n')

        header = True
        for row in element.find_all('tr'):
            cols = [col.get_text(strip=True).replace('|', '\|') for col in row.find_all(['th', 'td'])]
            md_lines_collector.append(f"| {' | '.join(cols)} |\n")
            if header and element.find('th'):
                md_lines_collector.append(f"|{'|'.join(['---'] * len(cols))}|\n")
                header = False
        md_lines_collector.append('\n')
        return new_img_counter

    elif element.name == 'hr':
        if md_lines_collector and md_lines_collector[-1] and not md_lines_collector[-1].endswith('\n\n'):
            if not md_lines_collector[-1].endswith('\n'):
                md_lines_collector.append('\n')
            md_lines_collector.append('\n')
        md_lines_collector.append("---\n\n")
        return new_img_counter

    # Default: Recurse for other elements (div, span, b, i, a, etc.)
    if hasattr(element, 'children'):
        is_block_container = element.name in ['p', 'div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main', 'body']
        content_added_by_children = False
        initial_len = len(md_lines_collector)

        for child in element.children:
            new_img_counter = recursive_process_element(child, md_lines_collector, img_dir, md_dir, img_mapping, new_img_counter, content_path)
        
        if len(md_lines_collector) > initial_len:
            content_added_by_children = True

        # After processing children of a block-like container, ensure a blank line if it generated content
        if is_block_container and content_added_by_children and md_lines_collector and md_lines_collector[-1] and not md_lines_collector[-1].endswith('\n\n'):
            if not md_lines_collector[-1].endswith('\n'):
                md_lines_collector.append('\n')
            md_lines_collector.append('\n')
            
    return new_img_counter

def convert_html_to_markdown(html_content, content_path, img_dir, md_dir, img_start_index, img_mapping):
    """Converts HTML content to Markdown using a recursive approach, handling images and text correctly."""
    soup = BeautifulSoup(html_content, 'html.parser')
    md_lines_collector = []
    
    # Remove script and style tags first
    for script_or_style in soup.find_all(['script', 'style']):
        script_or_style.decompose()
    
    current_img_counter = img_start_index
    if soup.body:
        for element in soup.body.children: # Iterate over direct children of body
            current_img_counter = recursive_process_element(element, md_lines_collector, img_dir, md_dir, img_mapping, current_img_counter, content_path)
            
    # Join collected parts and clean up
    final_md_content = "".join(md_lines_collector)
    # Consolidate multiple newlines (3 or more) into two, and strip leading/trailing whitespace
    final_md_content = re.sub(r'\n{3,}', '\n\n', final_md_content).strip()
    
    return final_md_content + '\n' if final_md_content else '', current_img_counter

def resolve_image_path(content_path, img_src):
    """解析图片绝对路径"""
    # 处理不同操作系统中的路径分隔符
    img_src = img_src.replace('\\', '/').replace('/', os.sep)
    
    # 去除URL查询参数
    img_src = img_src.split('?', 1)[0]
    
    # 构建绝对路径
    content_dir = os.path.dirname(content_path)
    return os.path.normpath(os.path.join(content_dir, img_src))

def find_opf_file(temp_dir):
    """查找OPF文件路径（处理不同的EPUB结构）"""
    # 检查META-INF/container.xml
    container_path = os.path.join(temp_dir, 'META-INF', 'container.xml')
    if os.path.exists(container_path):
        try:
            tree = ET.parse(container_path)
            root = tree.getroot()
            # 多种可能的命名空间
            namespaces = {
                'ns': 'urn:oasis:names:tc:opendocument:xmlns:container',
                '': 'urn:oasis:names:tc:opendocument:xmlns:container'
            }
            
            # 尝试不同命名空间
            for ns in namespaces.values():
                try:
                    rootfile = root.find(f'.//{{{ns}}}rootfile')
                    if rootfile is not None:
                        opf_path = os.path.join(temp_dir, rootfile.get('full-path'))
                        if os.path.exists(opf_path):
                            return opf_path
                except SyntaxError:
                    continue
    
        except Exception as e:
            print(f"解析container.xml失败: {str(e)}")
    
    # 备用方案：搜索所有opf文件
    print("尝试搜索OPF文件...")
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.lower().endswith('.opf'):
                return os.path.join(root, file)
    
    return None

def parse_opf_contents(opf_path):
    """解析OPF文件获取内容顺序（增强兼容性）"""
    content_dir = os.path.dirname(opf_path)
    content_items = []
    
    try:
        with open(opf_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 处理各种XML命名空间问题
        content = re.sub(r'<(\?xml[^>]+|!DOCTYPE\s*[^>]+)>', '', content, flags=re.IGNORECASE)
        
        # 解析XML
        root = ET.fromstring(content)
        
        # 构建ID到文件路径的映射
        id_to_file = {}
        namespaces = {'opf': 'http://www.idpf.org/2007/opf'}
        
        manifest = root.find('opf:manifest', namespaces) or root.find('manifest')
        if manifest:
            items = manifest.findall('opf:item', namespaces) or manifest.findall('item')
            for item in items:
                item_id = item.get('id')
                href = item.get('href')
                if item_id and href:
                    # 对特殊字符进行URI解码
                    href = re.sub(r'%([0-9a-fA-F]{2})', 
                                 lambda m: chr(int(m.group(1), 16)), href)
                    id_to_file[item_id] = href
        
        # 获取阅读顺序
        spine = root.find('opf:spine', namespaces) or root.find('spine')
        if spine:
            itemrefs = spine.findall('opf:itemref', namespaces) or spine.findall('itemref')
            for itemref in itemrefs:
                content_id = itemref.get('idref')
                if content_id in id_to_file:
                    # 构建内容文件的绝对路径
                    item_path = os.path.normpath(os.path.join(content_dir, id_to_file[content_id]))
                    # no need to check for existence here, will be checked in the main loop
                    content_items.append(item_path)
    
    except Exception as e:
        print(f"解析OPF文件失败: {str(e)}")
        # 备用方法：添加所有HTML/XML文件
        print("尝试添加所有HTML/XML文件...")
        for root, dirs, files in os.walk(content_dir):
            for file in files:
                if file.lower().endswith(('.html', '.htm', '.xhtml', '.xml')):
                    content_items.append(os.path.join(root, file))
    
    return content_items

# 使用示例
if __name__ == "__main__":
    epub_file=r"F:\apks\就业, 利息和货币通论 (John Maynard Keynes) (Z-Library).epub"
    # 获取完整文件名（含扩展名）
    full_filename = os.path.basename(epub_file)
    # 分割文件名和扩展名
    filename_without_ext = os.path.splitext(full_filename)[0]

    output_directory = os.path.join(r"G:\graph_rag_enhance\short_unit_code\epub_to_markdown\output", filename_without_ext)
    print(f"开始转换: {epub_file}")
    result = epub_to_markdown(epub_file, output_directory)
    print(result)
