#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版PDF处理脚本
整合了原有的PDF处理功能和新的增强功能：
1. 原有的PDF/图像解析功能
2. 生成PDF每页完整截图
3. 生成带页面信息的TXT文件

基于原有parse.py的功能，添加了后处理增强功能
"""

import os
import time
import argparse
import sys
import json
import re
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF
import torch.distributed as dist
from pdf2image import convert_from_path

# 导入原有的模块
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset, ImageDataset, MultiFileDataset
from magic_pdf.model.doc_analyze_by_custom_model_llm import doc_analyze_llm
from magic_pdf.model.custom_model import MonkeyOCR

# 任务指令定义
TASK_INSTRUCTIONS = {
    'text': 'Please output the text content from the image.',
    'formula': 'Please write out the expression of the formula in the image using LaTeX format.',
    'table': 'This is the image of a table. Please output the table in html format.'
}


class EnhancedPDFProcessor:
    """增强的PDF处理器"""
    
    def __init__(self, config_path="model_configs.yaml"):
        """
        初始化处理器
        
        Args:
            config_path: 模型配置文件路径
        """
        self.config_path = config_path
        self.MonkeyOCR_model = None
    
    def _load_model(self):
        """加载模型（懒加载）"""
        if self.MonkeyOCR_model is None:
            print("Loading model...")
            self.MonkeyOCR_model = MonkeyOCR(self.config_path)
        return self.MonkeyOCR_model
    
    def generate_page_images(self, pdf_path: str, result_dir: str, pdf_name: str) -> bool:
        """
        生成PDF每页完整截图
        
        Args:
            pdf_path: PDF文件路径
            result_dir: 结果目录
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            bool: 是否成功生成
        """
        if not os.path.exists(pdf_path):
            print(f"⚠️  PDF文件不存在，跳过页面截图生成: {pdf_path}")
            return False
        
        # 创建页面图像目录
        page_images_dir = os.path.join(result_dir, "page_images")
        os.makedirs(page_images_dir, exist_ok=True)
        
        try:
            # 打开PDF文件
            pdf_doc = fitz.open(pdf_path)
            
            print(f"🖼️  生成页面截图，共 {len(pdf_doc)} 页...")
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                
                # 生成页面图像
                mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放，提高清晰度
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # 保存图像
                image_filename = f"{pdf_name}_page_{page_num + 1}.png"
                image_path = os.path.join(page_images_dir, image_filename)
                pix.save(image_path)
                
                print(f"   ✅ 生成页面 {page_num + 1}: {image_filename}")
            
            pdf_doc.close()
            print(f"🎉 页面截图生成完成！")
            return True
            
        except Exception as e:
            print(f"❌ 生成页面截图时出错: {e}")
            return False
    
    def generate_txt_file(self, result_dir: str, pdf_name: str) -> bool:
        """
        生成带页面信息的TXT文件
        
        Args:
            result_dir: 结果目录
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            bool: 是否成功生成
        """
        # 查找Markdown文件
        md_file = os.path.join(result_dir, f"{pdf_name}.md")
        if not os.path.exists(md_file):
            print(f"⚠️  未找到Markdown文件，跳过TXT生成: {md_file}")
            return False
        
        # 查找中间JSON文件
        middle_json = os.path.join(result_dir, f"{pdf_name}_middle.json")
        
        try:
            # 读取Markdown内容
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 读取中间结果JSON（用于获取页面信息）
            page_info = self._get_page_info_from_json(middle_json)
            
            # 处理Markdown内容
            txt_content = self._process_markdown_to_txt(md_content, page_info, pdf_name)
            
            # 保存TXT文件到txt目录
            txt_filename = f"{pdf_name}.txt"
            # 确保txt目录存在
            txt_dir = "txt"
            os.makedirs(txt_dir, exist_ok=True)
            txt_path = os.path.join(txt_dir, txt_filename)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            
            print(f"📄 TXT文件生成完成: {txt_filename}")
            return True
            
        except Exception as e:
            print(f"❌ 生成TXT文件时出错: {e}")
            return False
    
    def _get_page_info_from_json(self, middle_json_path: str) -> dict:
        """从中间结果JSON中获取页面信息"""
        if not os.path.exists(middle_json_path):
            return {}
        
        try:
            with open(middle_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取页面信息
            pdf_info = data.get('pdf_info', [])
            page_info = {}
            
            for page_data in pdf_info:
                page_idx = page_data.get('page_idx', 0)
                
                # 尝试获取不同字段名的块数据
                blocks = page_data.get('para_blocks', [])
                if not blocks:
                    blocks = page_data.get('preproc_blocks', [])
                
                page_info[page_idx] = {
                    'page_num': page_idx + 1,
                    'blocks': blocks
                }
            
            return page_info
            
        except Exception as e:
            print(f"⚠️  读取页面信息时出错: {e}")
            return {}

    def _process_page_blocks(self, blocks: list, pdf_name: str) -> str:
        """
        处理页面块内容，生成文本内容
        
        Args:
            blocks: 页面块数据列表
            pdf_name: PDF文件名
            
        Returns:
            str: 处理后的页面内容
        """
        content_lines = []
        
        for block in blocks:
            block_content = self._process_single_block(block, pdf_name)
            if block_content.strip():
                content_lines.append(block_content)
        
        return "\n\n".join(content_lines)
    
    def _process_single_block(self, block: dict, pdf_name: str) -> str:
        """
        处理单个块
        
        Args:
            block: 块数据
            pdf_name: PDF文件名
            
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
            return self._process_image_block(block, pdf_name)
        elif block_type == 'list':
            return self._process_list_block(block)
        else:
            # 通用处理
            return self._extract_text_from_block(block)
    
    def _process_text_block(self, block: dict) -> str:
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
    
    def _process_title_block(self, block: dict) -> str:
        """处理标题块"""
        title_text = self._extract_text_from_block(block)
        if title_text.strip():
            # 移除Markdown格式的#号
            title_text = re.sub(r'^#+\s*', '', title_text.strip())
            return f"{title_text}\n{'-' * len(title_text)}"  # 添加下划线
        return ""
    
    def _process_equation_block(self, block: dict) -> str:
        """处理公式块"""
        latex_text = block.get('latex', '')
        if latex_text:
            return f"[公式] {latex_text}"
        return self._extract_text_from_block(block)
    
    def _process_table_block(self, block: dict) -> str:
        """处理表格块"""
        html_content = block.get('html', '')
        if html_content:
            # 简单的HTML表格转文本
            table_text = self._html_table_to_text(html_content)
            return f"[表格]\n{table_text}"
        return self._extract_text_from_block(block)
    
    def _process_image_block(self, block: dict, pdf_name: str) -> str:
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
            image_url = f"http://9bn8of823990.vicp.fun:42712/images/{pdf_name}/images/{image_path}"
            image_info.append(f"[图像] {image_url}")
        else:
            image_info.append("[图像]")
            
        if image_caption:
            image_info.append(image_caption)
        
        return "\n".join(image_info) if image_info else "[图像]"
    
    def _process_list_block(self, block: dict) -> str:
        """处理列表块"""
        lines = block.get('lines', [])
        list_items = []
        
        for line in lines:
            line_text = self._extract_text_from_line(line)
            if line_text.strip():
                list_items.append(f"• {line_text.strip()}")
        
        return "\n".join(list_items)
    
    def _extract_text_from_block(self, block: dict) -> str:
        """从块中提取文本"""
        lines = block.get('lines', [])
        text_content = []
        
        for line in lines:
            line_text = self._extract_text_from_line(line)
            if line_text.strip():
                text_content.append(line_text.strip())
        
        return "\n".join(text_content)
    
    def _extract_text_from_line(self, line: dict) -> str:
        """从行中提取文本"""
        spans = line.get('spans', [])
        line_text = ""
        
        for span in spans:
            span_text = span.get('content', '').strip()
            if span_text:
                line_text += span_text + " "
        
        return line_text.strip()
    
    def _html_table_to_text(self, html_content: str) -> str:
        """将HTML表格转换为文本格式"""
        import re
        # 简单的HTML表格解析
        try:
            # 移除HTML标签，保留内容
            text_content = re.sub(r'<[^>]+>', ' ', html_content)
            # 清理多余空格
            text_content = re.sub(r'\s+', ' ', text_content)
            return text_content.strip()
        except Exception:
            return "[表格内容]"
    
    def _process_markdown_to_txt(self, md_content: str, page_info: dict, pdf_name: str) -> str:
        """
        处理Markdown内容转换为TXT格式
        
        Args:
            md_content: Markdown内容
            page_info: 页面信息字典
            pdf_name: PDF文件名
            
        Returns:
            str: 处理后的TXT内容
        """
        # 去除Markdown格式
        txt_content = self._remove_markdown_formatting(md_content)
        
        # 如果有页面信息，按页面重新组织内容
        if page_info:
            txt_content = self._reorganize_by_pages(txt_content, page_info, pdf_name)
        else:
            # 如果没有页面信息，使用简单的页面分割
            txt_content = self._add_page_headers_simple(txt_content, pdf_name)
        
        return txt_content
    
    def _remove_markdown_formatting(self, md_content: str) -> str:
        """去除Markdown格式"""
        # 去除标题的#号
        content = re.sub(r'^#+\s*', '', md_content, flags=re.MULTILINE)
        
        # 去除其他Markdown格式
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # 粗体
        content = re.sub(r'\*(.*?)\*', r'\1', content)      # 斜体
        content = re.sub(r'`(.*?)`', r'\1', content)        # 代码
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)  # 链接
        
        return content
    
    def _reorganize_by_pages(self, content: str, page_info: dict, pdf_name: str) -> str:
        """基于页面信息重新组织内容"""
        organized_content = []
        
        for page_idx in sorted(page_info.keys()):
            page_data = page_info[page_idx]
            page_num = page_data['page_num']
            blocks = page_data.get('blocks', [])
            
            # 添加页面头部（新格式：添加#号和新的图片URL）
            page_image_url = f"http://9bn8of823990.vicp.fun:42712/images/{pdf_name}/page_images/{pdf_name}_page_{page_num}.png"
            page_header = f"#（{pdf_name}）第{page_num}页原图内容：{page_image_url}"
            
            organized_content.append(page_header)
            organized_content.append("&&页面内容...")  # 添加&&标记
            organized_content.append("")  # 空行
            
            # 处理实际的页面内容
            if blocks:
                page_content = self._process_page_blocks(blocks, pdf_name)
                if page_content.strip():
                    organized_content.append(page_content)
                else:
                    organized_content.append(f"[第{page_num}页无文本内容]")
            else:
                organized_content.append(f"[第{page_num}页无块数据]")
            
            organized_content.append("")  # 页面间空行
            organized_content.append("=" * 50)  # 页面分隔线
            organized_content.append("")
        
        return "\n".join(organized_content)
    
    def _add_page_headers_simple(self, content: str, pdf_name: str) -> str:
        """简单的页面头部添加（当没有详细页面信息时）"""
        lines = content.split('\n')
        processed_lines = []
        
        page_num = 1
        line_count = 0
        
        for line in lines:
            # 每50行作为一页（可调整）
            if line_count % 50 == 0 and line_count > 0:
                page_num += 1
            
            # 在每页开始添加页面信息（新格式：添加#号和&&）
            if line_count % 50 == 0:
                page_image_url = f"page_images/{pdf_name}_page_{page_num}.png"
                page_header = f"#（{pdf_name}）第{page_num}页原图内容：{page_image_url}"
                processed_lines.append(page_header)
                processed_lines.append("&&页面内容...")  # 添加&&标记
                processed_lines.append("")  # 空行
            
            processed_lines.append(line)
            line_count += 1
        
        return "\n".join(processed_lines)
    
    def parse_file_enhanced(self, input_file: str, output_dir: str, split_pages: bool = False, 
                           enable_enhancements: bool = True) -> str:
        """
        增强版文件解析（整合了原有功能和新功能）
        
        Args:
            input_file: 输入文件路径
            output_dir: 输出目录
            split_pages: 是否分页处理
            enable_enhancements: 是否启用增强功能
            
        Returns:
            str: 结果目录路径
        """
        print(f"🚀 开始增强版解析: {input_file}")
        
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        # 获取文件名
        name_without_suff = '.'.join(os.path.basename(input_file).split(".")[:-1])
        
        # 准备输出目录
        local_image_dir = os.path.join(output_dir, name_without_suff, "images")
        local_md_dir = os.path.join(output_dir, name_without_suff)
        image_dir = os.path.basename(local_image_dir)
        os.makedirs(local_image_dir, exist_ok=True)
        os.makedirs(local_md_dir, exist_ok=True)
        
        print(f"📁 输出目录: {local_md_dir}")
        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(local_md_dir)
        
        # 读取文件内容
        reader = FileBasedDataReader()
        file_bytes = reader.read(input_file)
        
        # 创建数据集实例
        file_extension = input_file.split(".")[-1].lower()
        if file_extension == "pdf":
            ds = PymuDocDataset(file_bytes)
        else:
            ds = ImageDataset(file_bytes)
        
        # 开始推理
        print("🔍 执行文档解析...")
        start_time = time.time()
        
        model = self._load_model()
        infer_result = ds.apply(doc_analyze_llm, MonkeyOCR_model=model, split_pages=split_pages)
        
        parsing_time = time.time() - start_time
        print(f"⏱️  解析时间: {parsing_time:.2f}s")

        # 检查推理结果是否为列表类型
        if isinstance(infer_result, list):
            print(f"📄 分别处理 {len(infer_result)} 页...")
            
            # 分别处理每页结果
            for page_idx, page_infer_result in enumerate(infer_result):
                page_dir_name = f"page_{page_idx}"
                page_local_image_dir = os.path.join(output_dir, name_without_suff, page_dir_name, "images")
                page_local_md_dir = os.path.join(output_dir, name_without_suff, page_dir_name)
                page_image_dir = os.path.basename(page_local_image_dir)
                
                # 创建页面特定目录
                os.makedirs(page_local_image_dir, exist_ok=True)
                os.makedirs(page_local_md_dir, exist_ok=True)
                
                # 创建页面特定写入器
                page_image_writer = FileBasedDataWriter(page_local_image_dir)
                page_md_writer = FileBasedDataWriter(page_local_md_dir)
                
                print(f"📄 处理第 {page_idx} 页 - 输出目录: {page_local_md_dir}")
                
                # 该页的管道处理
                page_pipe_result = page_infer_result.pipe_ocr_mode(page_image_writer, MonkeyOCR_model=model)
                
                # 保存页面特定结果
                page_infer_result.draw_model(os.path.join(page_local_md_dir, f"{name_without_suff}_page_{page_idx}_model.pdf"))
                page_pipe_result.draw_layout(os.path.join(page_local_md_dir, f"{name_without_suff}_page_{page_idx}_layout.pdf"))
                page_pipe_result.draw_span(os.path.join(page_local_md_dir, f"{name_without_suff}_page_{page_idx}_spans.pdf"))
                page_pipe_result.dump_md(page_md_writer, f"{name_without_suff}_page_{page_idx}.md", page_image_dir)
                page_pipe_result.dump_content_list(page_md_writer, f"{name_without_suff}_page_{page_idx}_content_list.json", page_image_dir)
                page_pipe_result.dump_middle_json(page_md_writer, f'{name_without_suff}_page_{page_idx}_middle.json')
            
            print(f"✅ 所有 {len(infer_result)} 页处理完成并保存在独立子目录中")
        else:
            print("📄 作为单个结果处理...")
            
            # 单个结果的管道处理
            pipe_result = infer_result.pipe_ocr_mode(image_writer, MonkeyOCR_model=model)
            
            # 保存单个结果（原有逻辑）
            infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))
            pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))
            pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))
            pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
            pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)
            pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')
        
        print("💾 原有处理结果已保存")
        
        # 执行增强功能
        if enable_enhancements:
            print("🎯 开始执行增强功能...")
            
            enhancement_success = 0
            
            # 功能1: 生成页面截图（仅对PDF文件）
            if file_extension == "pdf":
                if self.generate_page_images(input_file, local_md_dir, name_without_suff):
                    enhancement_success += 1
            else:
                print("⚠️  非PDF文件，跳过页面截图生成")
            
            # 功能2: 生成TXT文件
            if self.generate_txt_file(local_md_dir, name_without_suff):
                enhancement_success += 1
            
            print(f"✨ 增强功能完成！成功: {enhancement_success}/2")
        
        print(f"🎉 完整处理完成！结果保存到: {local_md_dir}")
        return local_md_dir


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="增强版PDF文档解析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本用法（包含增强功能）
  python parse_enhanced.py input.pdf                    # 解析PDF并生成增强功能
  python parse_enhanced.py input.pdf -o ./output        # 指定输出目录
  python parse_enhanced.py input.pdf -s                 # 分页处理
  python parse_enhanced.py image.jpg                    # 解析图像文件
  
  # 禁用增强功能（仅使用原有功能）
  python parse_enhanced.py input.pdf --no-enhancements  # 仅原有功能
  
  # 自定义配置
  python parse_enhanced.py input.pdf -c model_configs.yaml  # 自定义模型配置
  
  # 完整示例
  python parse_enhanced.py document.pdf -o ./results -s -c config.yaml
        """
    )
    
    parser.add_argument(
        "input_file",
        help="输入PDF或图像文件路径"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="输出目录 (默认: ./output)"
    )
    
    parser.add_argument(
        "-c", "--config",
        default="model_configs.yaml",
        help="配置文件路径 (默认: model_configs.yaml)"
    )
    
    parser.add_argument(
        "-s", "--split_pages",
        action='store_true',
        help="将PDF页面输出分割为独立的结果 (默认: False)"
    )
    
    parser.add_argument(
        "--no-enhancements",
        action='store_true',
        help="禁用增强功能，仅使用原有功能"
    )
    
    args = parser.parse_args()
    
    try:
        # 检查输入路径是否为文件
        if not os.path.isfile(args.input_file):
            print(f"❌ 输入必须是文件: {args.input_file}")
            sys.exit(1)
        
        # 创建增强处理器
        processor = EnhancedPDFProcessor(args.config)
        
        # 执行增强处理
        result_dir = processor.parse_file_enhanced(
            args.input_file,
            args.output,
            args.split_pages,
            not args.no_enhancements  # 取反，因为参数是no-enhancements
        )
        
        if args.no_enhancements:
            print(f"\n✅ 原有功能处理完成！结果保存在: {result_dir}")
        else:
            print(f"\n🎉 增强版处理完成！结果保存在: {result_dir}")
            print("\n📊 生成的文件:")
            print("   - *.md          - Markdown文件")
            print("   - *.txt         - 增强TXT文件")
            print("   - *_layout.pdf  - 版面标注PDF")
            print("   - *_middle.json - 中间结果JSON")
            print("   - images/       - 提取的图像")
            print("   - page_images/  - 页面完整截图")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 