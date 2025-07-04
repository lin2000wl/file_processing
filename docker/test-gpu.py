#!/usr/bin/env python3
"""
GPU测试脚本
用于验证Docker容器中的GPU支持
"""

import sys
import os

def test_gpu_support():
    """测试GPU支持"""
    print("🔍 GPU支持测试开始...")
    print("=" * 50)
    
    # 测试1: 检查CUDA环境变量
    print("1. 检查CUDA环境变量:")
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set')
    nvidia_visible = os.environ.get('NVIDIA_VISIBLE_DEVICES', 'Not set')
    print(f"   CUDA_VISIBLE_DEVICES: {cuda_visible}")
    print(f"   NVIDIA_VISIBLE_DEVICES: {nvidia_visible}")
    print()
    
    # 测试2: 检查PyTorch
    try:
        import torch
        print("2. PyTorch信息:")
        print(f"   版本: {torch.__version__}")
        print(f"   CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA版本: {torch.version.cuda}")
            print(f"   GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        print()
    except ImportError as e:
        print(f"2. PyTorch导入失败: {e}")
        print()
    
    # 测试3: 简单的GPU计算测试
    try:
        import torch
        if torch.cuda.is_available():
            print("3. GPU计算测试:")
            device = torch.device('cuda')
            x = torch.randn(1000, 1000).to(device)
            y = torch.randn(1000, 1000).to(device)
            z = torch.matmul(x, y)
            print(f"   矩阵乘法测试成功: {z.shape}")
            print(f"   计算设备: {z.device}")
            print()
        else:
            print("3. GPU不可用，跳过计算测试")
            print()
    except Exception as e:
        print(f"3. GPU计算测试失败: {e}")
        print()
    
    # 测试4: 检查NVIDIA-SMI
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("4. NVIDIA-SMI输出:")
            print(result.stdout)
        else:
            print("4. NVIDIA-SMI不可用")
            print(f"   错误: {result.stderr}")
    except Exception as e:
        print(f"4. NVIDIA-SMI检查失败: {e}")
    
    print("=" * 50)
    print("🏁 GPU支持测试完成")

if __name__ == "__main__":
    test_gpu_support() 