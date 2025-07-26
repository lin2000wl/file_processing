#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的TXT生成器
专门用于从中间JSON数据生成高质量的TXT文件
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


class EnhancedTxtGenerator:
    """增强的TXT生成器"""
    
    def __init__(self, middle_json_path: str, pdf_name: str):
        """
        初始化TXT生成器
        
        Args:
            middle_json_path: 中间JSON文件路径
            pdf_name: PDF文件名（不含扩展名）
        """
        self.middle_json_path = Path(middle_json_path)
        self.pdf_name = pdf_name
        self.pdf_data = self._load_json_data()
    
    def _load_json_data(self) -> Dict:
        """加载JSON数据"""
        try:
            with open(self.middle_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载JSON数据失败: {e}")
            return {}
    
    def generate_txt_content(self) -> str:
        """
        生成TXT内容
        
        Returns:
            str: 生成的TXT内容
        """
        if not self.pdf_data:
            return ""
        
        pdf_info = self.pdf_data.get('pdf_info', [])
        txt_lines = []
        
        for page_data in pdf_info:
            page_idx = page_data.get('page_idx', 0)
            page_num = page_idx + 1
            
            # 添加页面头部信息（修改格式：添加#号和新的图片URL）
            page_image_url = f"http://9bn8of823990.vicp.fun:42712/images/{self.pdf_name}/page_images/{self.pdf_name}_page_{page_num}.png"
            page_header = f"#（{self.pdf_name}）第{page_num}页原图内容：{page_image_url}"
            
            txt_lines.append(page_header)
            txt_lines.append("&&页面内容...")  # 添加&&标记
            txt_lines.append("")  # 空行
            
            # 处理页面内容
            # 修复：使用正确的字段名 preproc_blocks 而不是 para_blocks
            preproc_blocks = page_data.get('preproc_blocks', [])
            page_content = self._process_page_blocks(preproc_blocks)
            
            if page_content.strip():
                txt_lines.append(page_content)
            else:
                txt_lines.append(f"[第{page_num}页无文本内容]")
            
            txt_lines.append("")  # 页面间空行
            txt_lines.append("=" * 50)  # 页面分隔线
            txt_lines.append("")
        
        return "\n".join(txt_lines)
    
    def _process_page_blocks(self, preproc_blocks: List[Dict]) -> str:
        """
        处理页面块内容
        
        Args:
            preproc_blocks: 预处理块数据（从middle.json的preproc_blocks字段）
            
        Returns:
            str: 处理后的页面内容
        """
        content_lines = []
        
        for block in preproc_blocks:
            block_content = self._process_single_block(block)
            if block_content.strip():
                content_lines.append(block_content)
        
        return "\n\n".join(content_lines)
    
    def _process_single_block(self, block: Dict) -> str:
        """
        处理单个块
        
        Args:
            block: 块数据
            
        Returns:
            str: 处理后的块内容
        """
        block_type = block.get('type', '')
        
        if block_type == 'text':
            return self._process_text_block(block)
        elif block_type == 'title':
            return self._process_title_block(block)
        elif block_type == 'inter_line_equation':
            return self._process_equation_block(block)
        elif block_type == 'table':
            return self._process_table_block(block)
        elif block_type == 'image':
            return self._process_image_block(block)
        elif block_type == 'list':
            return self._process_list_block(block)
        else:
            # 通用处理
            return self._extract_text_from_block(block)
    
    def _process_text_block(self, block: Dict) -> str:
        """处理文本块"""
        lines = block.get('lines', [])
        text_content = []
        
        for line in lines:
            spans = line.get('spans', [])
            line_text = ""
            
            for span in spans:
                span_text = span.get('content', '').strip()
                if span_text:
                    line_text += span_text + " "
            
            if line_text.strip():
                text_content.append(line_text.strip())
        
        return "\n".join(text_content)
    
    def _process_title_block(self, block: Dict) -> str:
        """处理标题块"""
        title_text = self._extract_text_from_block(block)
        if title_text.strip():
            # 移除Markdown格式的#号
            title_text = re.sub(r'^#+\s*', '', title_text.strip())
            return f"{title_text}\n{'-' * len(title_text)}"  # 添加下划线
        return ""
    
    def _process_equation_block(self, block: Dict) -> str:
        """处理公式块"""
        latex_text = block.get('latex', '')
        if latex_text:
            return f"[公式] {latex_text}"
        return self._extract_text_from_block(block)
    
    def _process_table_block(self, block: Dict) -> str:
        """处理表格块"""
        # 首先检查block级别的html字段
        html_content = block.get('html', '')
        if html_content:
            table_text = self._html_table_to_text(html_content)
            return f"[表格]\n{table_text}"
        
        # 如果block级别没有html，则深入搜索spans中的html
        html_content = self._extract_html_from_spans(block)
        if html_content:
            table_text = self._html_table_to_text(html_content)
            return f"[表格]\n{table_text}"
        
        return self._extract_text_from_block(block)
    
    def _process_image_block(self, block: Dict) -> str:
        """处理图像块"""
        image_info = []
        image_path = None
        image_caption = None
        
        # 从blocks中提取图片信息
        blocks = block.get('blocks', [])
        for sub_block in blocks:
            block_type = sub_block.get('type', '')
            
            if block_type == 'image_body':
                # 提取图片路径
                lines = sub_block.get('lines', [])
                for line in lines:
                    spans = line.get('spans', [])
                    for span in spans:
                        if span.get('type') == 'image':
                            image_path = span.get('image_path', '')
                            break
                    if image_path:
                        break
                        
            elif block_type == 'image_caption':
                # 提取图片标题
                lines = sub_block.get('lines', [])
                for line in lines:
                    spans = line.get('spans', [])
                    for span in spans:
                        caption_text = span.get('content', '').strip()
                        if caption_text:
                            image_caption = caption_text
                            break
                    if image_caption:
                        break
        
        # 构建图片信息，使用新的URL格式
        if image_path:
            # 新的图片URL格式：http://9bn8of823990.vicp.fun:42712/images/文件名/images/相对图片路径
            image_url = f"http://9bn8of823990.vicp.fun:42712/images/{self.pdf_name}/images/{image_path}"
            image_info.append(f"[图像] {image_url}")
        else:
            image_info.append("[图像]")
            
        if image_caption:
            image_info.append(image_caption)
        
        return "\n".join(image_info) if image_info else "[图像]"
    
    def _process_list_block(self, block: Dict) -> str:
        """处理列表块"""
        lines = block.get('lines', [])
        list_items = []
        
        for line in lines:
            line_text = self._extract_text_from_line(line)
            if line_text.strip():
                list_items.append(f"• {line_text.strip()}")
        
        return "\n".join(list_items)
    
    def _extract_text_from_block(self, block: Dict) -> str:
        """从块中提取文本"""
        lines = block.get('lines', [])
        text_content = []
        
        for line in lines:
            line_text = self._extract_text_from_line(line)
            if line_text.strip():
                text_content.append(line_text.strip())
        
        return "\n".join(text_content)
    
    def _extract_text_from_line(self, line: Dict) -> str:
        """从行中提取文本"""
        spans = line.get('spans', [])
        line_text = ""
        
        for span in spans:
            span_text = span.get('content', '').strip()
            if span_text:
                line_text += span_text + " "
        
        return line_text.strip()
    
    def _extract_html_from_spans(self, block: Dict) -> str:
        """从spans中提取HTML内容"""
        def search_html_in_obj(obj):
            if isinstance(obj, dict):
                # 如果直接有html字段，返回它
                if 'html' in obj and isinstance(obj['html'], str):
                    return obj['html']
                # 递归搜索所有字段
                for value in obj.values():
                    result = search_html_in_obj(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                # 递归搜索列表中的每个元素
                for item in obj:
                    result = search_html_in_obj(item)
                    if result:
                        return result
            return None
        
        return search_html_in_obj(block) or ""
    
    def _html_table_to_text(self, html_content: str) -> str:
        """将HTML表格转换为文本格式，保留所有HTML标签字符"""
        # 直接返回原始HTML内容，保留所有<tr><td>等标签字符
        try:
            return html_content
        except Exception:
            return "[表格内容]"
    
    def save_txt_file(self, output_path: str) -> bool:
        """
        保存TXT文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功保存
        """
        try:
            txt_content = self.generate_txt_content()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            
            print(f"📄 TXT文件已保存: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 保存TXT文件失败: {e}")
            return False


def main():
    """测试函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="增强TXT生成器")
    parser.add_argument("json_file", help="中间JSON文件路径")
    parser.add_argument("pdf_name", help="PDF文件名（不含扩展名）")
    parser.add_argument("-o", "--output", help="输出TXT文件路径")
    
    args = parser.parse_args()
    
    generator = EnhancedTxtGenerator(args.json_file, args.pdf_name)
    
    if args.output:
        output_path = args.output
    else:
        # 默认保存到txt目录下
        import os
        os.makedirs("txt", exist_ok=True)
        output_path = f"txt/{args.pdf_name}.txt"
    
    generator.save_txt_file(output_path)


if __name__ == "__main__":
    main() 