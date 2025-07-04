#!/usr/bin/env python3
"""
CPU版本测试脚本
用于验证Docker容器中的CPU版本配置
"""

import sys
import os

def test_cpu_setup():
    """测试CPU设置"""
    print("🔍 CPU版本测试开始...")
    print("=" * 50)
    
    # 测试1: 检查Python环境
    print("1. Python环境:")
    print(f"   Python版本: {sys.version}")
    print(f"   Python路径: {sys.executable}")
    print()
    
    # 测试2: 检查PyTorch
    try:
        import torch
        print("2. PyTorch信息:")
        print(f"   版本: {torch.__version__}")
        print(f"   CUDA可用: {torch.cuda.is_available()}")
        print(f"   CPU线程数: {torch.get_num_threads()}")
        
        # 简单的CPU计算测试
        x = torch.randn(100, 100)
        y = torch.randn(100, 100)
        z = torch.matmul(x, y)
        print(f"   矩阵乘法测试: {z.shape}")
        print()
    except ImportError as e:
        print(f"2. PyTorch导入失败: {e}")
        print()
    
    # 测试3: 检查其他依赖
    dependencies = [
        'numpy', 'PIL', 'cv2', 'fitz', 'transformers', 
        'loguru', 'yaml', 'pydantic'
    ]
    
    print("3. 依赖包检查:")
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}: 可用")
        except ImportError:
            print(f"   ❌ {dep}: 不可用")
    print()
    
    # 测试4: 检查工作目录
    print("4. 工作目录检查:")
    print(f"   当前目录: {os.getcwd()}")
    
    required_dirs = ['storage', 'model_weight']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}: 存在")
        else:
            print(f"   ❌ {dir_name}: 不存在")
    
    required_files = ['parse.py', 'model_configs.yaml']
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"   ✅ {file_name}: 存在")
        else:
            print(f"   ❌ {file_name}: 不存在")
    print()
    
    # 测试5: 检查配置文件
    try:
        import yaml
        print("5. 配置文件检查:")
        
        config_files = ['model_configs.yaml', 'model_configs_cpu.yaml']
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    device = config.get('device', 'unknown')
                    print(f"   ✅ {config_file}: device={device}")
            else:
                print(f"   ❌ {config_file}: 不存在")
        print()
    except Exception as e:
        print(f"5. 配置文件检查失败: {e}")
        print()
    
    print("=" * 50)
    print("🏁 CPU版本测试完成")
    print("💡 建议: 如果所有测试通过，可以开始使用MonkeyOCR进行文档处理")

if __name__ == "__main__":
    test_cpu_setup() 