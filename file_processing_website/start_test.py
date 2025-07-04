#!/usr/bin/env python3
"""
简单的启动测试脚本
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"
    except Exception as e:
        return False, "", str(e)

def main():
    print("文件处理网站启动测试")
    print("=" * 50)
    
    # 检查当前目录
    current_dir = Path.cwd()
    print(f"当前目录: {current_dir}")
    
    # 检查项目结构
    project_dir = current_dir / "file_processing_website"
    backend_dir = project_dir / "backend"
    
    print(f"项目目录: {project_dir} - {'存在' if project_dir.exists() else '不存在'}")
    print(f"后端目录: {backend_dir} - {'存在' if backend_dir.exists() else '不存在'}")
    
    if not backend_dir.exists():
        print("错误：后端目录不存在")
        return
    
    # 检查虚拟环境
    venv_dir = backend_dir / ".venv"
    python_exe = venv_dir / "bin" / "python"
    
    print(f"虚拟环境: {venv_dir} - {'存在' if venv_dir.exists() else '不存在'}")
    print(f"Python解释器: {python_exe} - {'存在' if python_exe.exists() else '不存在'}")
    
    if not python_exe.exists():
        print("错误：虚拟环境未找到")
        return
    
    # 检查Redis
    print("\n检查Redis...")
    success, stdout, stderr = run_command("docker ps | grep redis")
    if success and "redis" in stdout:
        print("✓ Redis容器正在运行")
    else:
        print("启动Redis容器...")
        success, _, _ = run_command("docker run -d --name redis-test -p 6379:6379 redis:7-alpine")
        if success:
            print("✓ Redis容器启动成功")
            time.sleep(3)  # 等待Redis启动
        else:
            print("✗ Redis容器启动失败")
    
    # 测试Redis连接
    success, _, _ = run_command("docker exec redis-test redis-cli ping")
    if success:
        print("✓ Redis连接正常")
    else:
        print("✗ Redis连接失败")
    
    # 运行测试脚本
    print("\n运行文件服务测试...")
    test_script = project_dir / "test_file_service.py"
    if test_script.exists():
        success, stdout, stderr = run_command(f"{python_exe} {test_script}", cwd=str(project_dir))
        if success:
            print("✓ 文件服务测试通过")
            print(stdout)
        else:
            print("✗ 文件服务测试失败")
            print(f"错误: {stderr}")
    else:
        print("✗ 测试脚本不存在")
    
    # 启动后端服务器
    print("\n启动后端服务器...")
    try:
        # 使用subprocess.Popen启动服务器
        env = os.environ.copy()
        env['PYTHONPATH'] = str(backend_dir)
        
        process = subprocess.Popen(
            [str(python_exe), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(backend_dir),
            env=env
        )
        
        print(f"✓ 后端服务器已启动 (PID: {process.pid})")
        print("服务器地址: http://127.0.0.1:8000")
        print("API文档: http://127.0.0.1:8000/docs")
        print("\n按 Ctrl+C 停止服务器")
        
        # 等待服务器启动
        time.sleep(3)
        
        # 测试健康检查
        success, stdout, stderr = run_command("curl -s http://127.0.0.1:8000/health")
        if success:
            print("✓ 健康检查通过")
            print(f"响应: {stdout}")
        else:
            print("✗ 健康检查失败")
        
        # 等待用户中断
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n正在停止服务器...")
            process.terminate()
            process.wait()
            print("✓ 服务器已停止")
            
    except Exception as e:
        print(f"✗ 启动服务器失败: {str(e)}")

if __name__ == "__main__":
    main() 