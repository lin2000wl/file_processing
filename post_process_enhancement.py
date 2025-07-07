#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF处理结果增强脚本
基于现有的PDF处理输出结果，生成额外的功能：
1. 生成PDF每页完整截图
2. 生成带页面信息的TXT文件
"""

import os
import json
import argparse
import re
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF
from typing import Dict, List, Optional


class PDFEnhancementProcessor:
    """PDF处理结果增强器"""
    
    def __init__(self, result_dir: str):
        """
        初始化增强处理器
        
        Args:
            result_dir: 现有处理结果目录
        """
        self.result_dir = Path(result_dir)
        self.pdf_name = self.result_dir.name
        
        # 检查必要文件是否存在
        self.md_file = self._find_md_file()
        self.middle_json = self._find_middle_json()
        self.original_pdf = self._find_original_pdf()
        
    def _find_md_file(self) -> Optional[Path]:
        """查找Markdown文件"""
        md_files = list(self.result_dir.glob("*.md"))
        return md_files[0] if md_files else None
    
    def _find_middle_json(self) -> Optional[Path]:
        """查找中间结果JSON文件"""
        json_files = list(self.result_dir.glob("*_middle.json"))
        return json_files[0] if json_files else None
    
    def _find_original_pdf(self) -> Optional[Path]:
        """查找原始PDF文件（如果存在）"""
        # 尝试从上级目录或其他位置查找原始PDF
        pdf_files = list(self.result_dir.parent.glob(f"{self.pdf_name}.pdf"))
        if not pdf_files:
            pdf_files = list(self.result_dir.glob("*.pdf"))
        return pdf_files[0] if pdf_files else None
    
    def generate_page_images(self, pdf_path: str = None) -> bool:
        """
        生成PDF每页完整截图
        
        Args:
            pdf_path: PDF文件路径，如果不提供则尝试自动查找
            
        Returns:
            bool: 是否成功生成
        """
        if pdf_path is None:
            pdf_path = self.original_pdf
        
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"❌ 未找到PDF文件: {pdf_path}")
            return False
        
        # 创建页面图像目录
        page_images_dir = self.result_dir / "page_images"
        page_images_dir.mkdir(exist_ok=True)
        
        try:
            # 打开PDF文件
            pdf_doc = fitz.open(str(pdf_path))
            
            print(f"🖼️  开始生成页面截图，共 {len(pdf_doc)} 页...")
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                
                # 生成页面图像
                mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放，提高清晰度
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # 保存图像
                image_filename = f"{self.pdf_name}_page_{page_num + 1}.png"
                image_path = page_images_dir / image_filename
                pix.save(str(image_path))
                
                print(f"   ✅ 生成页面 {page_num + 1}: {image_filename}")
            
            pdf_doc.close()
            print(f"🎉 页面截图生成完成！保存位置: {page_images_dir}")
            return True
            
        except Exception as e:
            print(f"❌ 生成页面截图时出错: {e}")
            return False
    
    def generate_txt_file(self) -> bool:
        """
        生成带页面信息的TXT文件
        
        Returns:
            bool: 是否成功生成
        """
        if not self.md_file or not self.md_file.exists():
            print(f"❌ 未找到Markdown文件: {self.md_file}")
            return False
        
        try:
            # 读取Markdown内容
            with open(self.md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 读取中间结果JSON（用于获取页面信息）
            page_info = self._get_page_info_from_json()
            
            # 处理Markdown内容
            txt_content = self._process_markdown_to_txt(md_content, page_info)
            
            # 保存TXT文件到txt目录
            txt_filename = f"{self.pdf_name}.txt"
            # 确保txt目录存在
            txt_dir = Path("txt")
            txt_dir.mkdir(exist_ok=True)
            txt_path = txt_dir / txt_filename
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            
            print(f"📄 TXT文件生成完成: {txt_filename}")
            return True
            
        except Exception as e:
            print(f"❌ 生成TXT文件时出错: {e}")
            return False
    
    def _get_page_info_from_json(self) -> Dict:
        """从中间结果JSON中获取页面信息"""
        if not self.middle_json or not self.middle_json.exists():
            return {}
        
        try:
            with open(self.middle_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取页面信息
            pdf_info = data.get('pdf_info', [])
            page_info = {}
            
            for page_data in pdf_info:
                page_idx = page_data.get('page_idx', 0)
                page_info[page_idx] = {
                    'page_num': page_idx + 1,
                    'blocks': page_data.get('para_blocks', [])
                }
            
            return page_info
            
        except Exception as e:
            print(f"⚠️  读取页面信息时出错: {e}")
            return {}
    
    def _process_markdown_to_txt(self, md_content: str, page_info: Dict) -> str:
        """
        处理Markdown内容转换为TXT格式
        
        Args:
            md_content: Markdown内容
            page_info: 页面信息字典
            
        Returns:
            str: 处理后的TXT内容
        """
        # 去除Markdown格式
        txt_content = self._remove_markdown_formatting(md_content)
        
        # 如果有页面信息，按页面重新组织内容
        if page_info:
            txt_content = self._reorganize_by_pages(txt_content, page_info)
        else:
            # 如果没有页面信息，使用简单的页面分割
            txt_content = self._add_page_headers_simple(txt_content)
        
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
    
    def _reorganize_by_pages(self, content: str, page_info: Dict) -> str:
        """基于页面信息重新组织内容"""
        organized_content = []
        
        for page_idx in sorted(page_info.keys()):
            page_data = page_info[page_idx]
            page_num = page_data['page_num']
            
            # 添加页面头部（修改格式：添加#号和新的图片URL）
            page_image_url = f"http://9bn8of823990.vicp.fun:42712/images/{self.pdf_name}/page_images/{self.pdf_name}_page_{page_num}.png"
            page_header = f"#（{self.pdf_name}）第{page_num}页原图内容：{page_image_url}"
            
            organized_content.append(page_header)
            organized_content.append("&&页面内容...")  # 添加&&标记
            organized_content.append("")  # 空行
            
            # 这里可以根据实际的块信息来组织内容
            # 暂时使用简单的方式
            organized_content.append(f"第{page_num}页内容")
            organized_content.append("")
        
        return "\n".join(organized_content)
    
    def _add_page_headers_simple(self, content: str) -> str:
        """简单的页面头部添加（当没有详细页面信息时）"""
        lines = content.split('\n')
        processed_lines = []
        
        page_num = 1
        line_count = 0
        
        for line in lines:
            # 每50行作为一页（可调整）
            if line_count % 50 == 0 and line_count > 0:
                page_num += 1
            
            # 在每页开始添加页面信息（修改格式：添加#号和&&）
            if line_count % 50 == 0:
                page_image_url = f"page_images/{self.pdf_name}_page_{page_num}.png"
                page_header = f"#（{self.pdf_name}）第{page_num}页原图内容：{page_image_url}"
                processed_lines.append(page_header)
                processed_lines.append("&&页面内容...")  # 添加&&标记
                processed_lines.append("")  # 空行
            
            processed_lines.append(line)
            line_count += 1
        
        return "\n".join(processed_lines)
    
    def process_all(self, pdf_path: str = None) -> bool:
        """
        执行所有增强处理
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            bool: 是否全部成功
        """
        print(f"🚀 开始处理: {self.result_dir}")
        
        success_count = 0
        
        # 生成页面截图
        if self.generate_page_images(pdf_path):
            success_count += 1
        
        # 生成TXT文件
        if self.generate_txt_file():
            success_count += 1
        
        print(f"✨ 处理完成！成功: {success_count}/2")
        return success_count == 2


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF处理结果增强工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 处理单个结果目录
  python post_process_enhancement.py /path/to/result/dir
  
  # 处理单个结果目录并指定PDF文件
  python post_process_enhancement.py /path/to/result/dir -p /path/to/original.pdf
  
  # 批量处理输出目录下的所有结果
  python post_process_enhancement.py /path/to/output --batch
        """
    )
    
    parser.add_argument(
        "result_path",
        help="处理结果目录路径"
    )
    
    parser.add_argument(
        "-p", "--pdf",
        help="原始PDF文件路径（可选）"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量处理模式"
    )
    
    args = parser.parse_args()
    
    result_path = Path(args.result_path)
    
    if not result_path.exists():
        print(f"❌ 路径不存在: {result_path}")
        return
    
    if args.batch:
        # 批量处理模式
        if not result_path.is_dir():
            print(f"❌ 批量模式需要提供目录路径")
            return
        
        # 查找所有子目录
        subdirs = [d for d in result_path.iterdir() if d.is_dir()]
        
        if not subdirs:
            print(f"❌ 未找到任何子目录")
            return
        
        print(f"🔄 批量处理模式，找到 {len(subdirs)} 个目录")
        
        success_count = 0
        for subdir in subdirs:
            try:
                processor = PDFEnhancementProcessor(str(subdir))
                if processor.process_all(args.pdf):
                    success_count += 1
            except Exception as e:
                print(f"❌ 处理 {subdir} 时出错: {e}")
        
        print(f"🎉 批量处理完成！成功: {success_count}/{len(subdirs)}")
    
    else:
        # 单个处理模式
        try:
            processor = PDFEnhancementProcessor(str(result_path))
            processor.process_all(args.pdf)
        except Exception as e:
            print(f"❌ 处理失败: {e}")


if __name__ == "__main__":
    main() 