#!/usr/bin/env python3
"""
测试当前MonkeyOCR设置
"""

import sys
import os
import subprocess

def test_current_setup():
    """测试当前设置"""
    print("🔍 测试当前MonkeyOCR设置...")
    print("=" * 60)
    
    # 1. 检查系统GPU状态
    print("1. 🖥️  系统GPU状态:")
    try:
        result = subprocess.run(['lspci', '|', 'grep', '-i', 'vga'], 
                              shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   显卡: {result.stdout.strip()}")
        else:
            print("   显卡: 未检测到专用显卡")
    except:
        print("   显卡: 检测失败")
    
    # 2. 检查NVIDIA驱动
    print("\n2. 🚀 NVIDIA驱动状态:")
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ NVIDIA驱动已安装")
            print(f"   输出: {result.stdout[:200]}...")
        else:
            print("   ❌ NVIDIA驱动未安装或不可用")
    except FileNotFoundError:
        print("   ❌ nvidia-smi命令不存在")
    
    # 3. 检查Docker状态
    print("\n3. 🐳 Docker状态:")
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Docker版本: {result.stdout.strip()}")
        else:
            print("   ❌ Docker不可用")
    except FileNotFoundError:
        print("   ❌ Docker未安装")
    
    # 4. 检查Docker GPU支持
    print("\n4. 🎯 Docker GPU支持:")
    try:
        result = subprocess.run(['which', 'nvidia-ctk'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ NVIDIA Container Toolkit已安装")
        else:
            print("   ❌ NVIDIA Container Toolkit未安装")
    except:
        print("   ❌ 检查失败")
    
    # 5. 检查虚拟环境
    print("\n5. 🐍 Python环境:")
    venv_path = "file_processing_website/backend/.venv"
    if os.path.exists(venv_path):
        print(f"   ✅ 虚拟环境存在: {venv_path}")
        
        # 检查虚拟环境中的PyTorch
        try:
            activate_script = f"{venv_path}/bin/activate"
            if os.path.exists(activate_script):
                cmd = f"source {activate_script} && python -c \"import torch; print('PyTorch:', torch.__version__, 'CUDA:', torch.cuda.is_available())\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   PyTorch状态: {result.stdout.strip()}")
                else:
                    print(f"   PyTorch检查失败: {result.stderr.strip()}")
        except Exception as e:
            print(f"   PyTorch检查异常: {e}")
    else:
        print(f"   ❌ 虚拟环境不存在: {venv_path}")
    
    # 6. 检查MonkeyOCR配置
    print("\n6. 🔧 MonkeyOCR配置:")
    config_file = "model_configs.yaml"
    if os.path.exists(config_file):
        print(f"   ✅ 配置文件存在: {config_file}")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'device: cuda' in content:
                    print("   ⚠️  当前配置: device=cuda (需要GPU)")
                elif 'device: cpu' in content:
                    print("   ✅ 当前配置: device=cpu (CPU模式)")
                else:
                    print("   ❓ 设备配置不明确")
        except Exception as e:
            print(f"   ❌ 配置文件读取失败: {e}")
    else:
        print(f"   ❌ 配置文件不存在: {config_file}")
    
    # 7. 推荐方案
    print("\n7. 💡 推荐方案:")
    print("   基于当前环境分析:")
    print("   - 系统: VMware虚拟机")
    print("   - 显卡: 虚拟显卡 (VMware SVGA)")
    print("   - NVIDIA驱动: 未安装")
    print("   - Docker: 已安装")
    print("   - GPU支持: 已配置但无物理GPU")
    print()
    print("   🎯 建议使用方案:")
    print("   1. ✅ Docker CPU版本 (推荐)")
    print("      - 稳定可靠")
    print("      - 功能完整")
    print("      - 适合开发测试")
    print("   2. ⚠️  修改配置使用CPU模式")
    print("      - 修改model_configs.yaml中device: cpu")
    print("      - 直接在宿主机运行")
    print("   3. 🌐 使用云GPU实例")
    print("      - 性能最佳")
    print("      - 适合生产环境")
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")
    print("💡 建议: 使用Docker CPU版本开始体验MonkeyOCR功能")

if __name__ == "__main__":
    test_current_setup() 