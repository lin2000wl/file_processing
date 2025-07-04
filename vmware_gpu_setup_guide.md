# VMware GPU直通配置指南

## 🎯 前提条件检查

### 1. 硬件要求
- **CPU**: 支持VT-x/VT-d的Intel CPU 或 AMD-V/AMD-Vi的AMD CPU
- **GPU**: NVIDIA GTX/RTX系列或专业卡
- **内存**: 建议16GB以上
- **VMware版本**: VMware Workstation Pro 15.5+ 或 VMware Player 15.5+

### 2. 宿主机检查
在Windows宿主机上运行：
```powershell
# 检查CPU虚拟化支持
Get-ComputerInfo | Select-Object HyperVRequirementVirtualizationFirmwareEnabled

# 检查GPU信息
Get-WmiObject Win32_VideoController | Select-Object Name, DriverVersion

# 检查NVIDIA驱动
nvidia-smi
```

## 🔧 VMware配置步骤

### 步骤1：启用虚拟化功能
1. **关闭虚拟机**
2. **编辑虚拟机设置**：
   - 右键虚拟机 → 设置
   - 处理器 → 勾选"虚拟化Intel VT-x/EPT或AMD-V/RVI"
   - 处理器 → 勾选"虚拟化IOMMU"

### 步骤2：添加GPU设备
1. **添加硬件**：
   - 虚拟机设置 → 添加 → PCI设备
   - 选择你的NVIDIA GPU
   - 如果没有看到GPU，需要启用直通模式

### 步骤3：修改VMX配置文件
关闭虚拟机，编辑 `.vmx` 文件，添加：
```
hypervisor.cpuid.v0 = "FALSE"
mce.enable = "TRUE"
vhv.enable = "TRUE"
vvtd.enable = "TRUE"
```

### 步骤4：VMware高级设置
1. **启用3D加速**：
   - 显示器 → 勾选"加速3D图形"
   - 图形内存：最大值

2. **内存设置**：
   - 内存：建议8GB以上
   - 勾选"将所有客户机内存映射为可执行内存"

## 🐧 Linux虚拟机配置

### 步骤1：检查硬件识别
```bash
# 检查PCI设备
lspci | grep -i nvidia

# 检查内核模块
lsmod | grep nouveau

# 检查IOMMU
dmesg | grep -i iommu
```

### 步骤2：禁用Nouveau驱动
```bash
# 创建黑名单文件
sudo nano /etc/modprobe.d/blacklist-nouveau.conf

# 添加内容：
blacklist nouveau
options nouveau modeset=0

# 更新initramfs
sudo update-initramfs -u

# 重启
sudo reboot
```

### 步骤3：安装NVIDIA驱动
```bash
# 添加NVIDIA PPA
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update

# 查看可用驱动
ubuntu-drivers devices

# 安装推荐驱动
sudo ubuntu-drivers autoinstall

# 或手动安装特定版本
sudo apt install nvidia-driver-535

# 重启
sudo reboot
```

### 步骤4：验证安装
```bash
# 检查驱动
nvidia-smi

# 检查CUDA
nvcc --version
```

## 🚀 替代方案

### 方案1：VMware vSphere vGPU
如果有企业环境，可以使用vSphere的vGPU功能。

### 方案2：Docker GPU支持
在虚拟机中使用Docker GPU支持：
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update && sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# 测试GPU访问
sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 方案3：云GPU实例
考虑使用云服务：
- **阿里云**: GPU实例（ECS）
- **腾讯云**: GPU云服务器
- **百度云**: GPU云服务器
- **Google Colab**: 免费GPU环境

### 方案4：WSL2 + CUDA
在Windows上使用WSL2：
```bash
# 在WSL2中安装CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda-repo-wsl-ubuntu-12-0-local_12.0.0-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-0-local_12.0.0-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-0-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

## 🔍 故障排除

### 常见问题1：GPU不显示
**解决方案**：
1. 确认宿主机GPU驱动最新
2. 检查VMware版本支持
3. 启用BIOS中的VT-d/AMD-Vi

### 常见问题2：性能较差
**解决方案**：
1. 增加虚拟机内存
2. 启用所有虚拟化功能
3. 关闭不必要的视觉效果

### 常见问题3：驱动冲突
**解决方案**：
1. 完全卸载旧驱动
2. 使用DDU清理驱动残留
3. 重新安装最新驱动

## 📝 注意事项

1. **性能损失**: 虚拟化会有10-30%的性能损失
2. **兼容性**: 不是所有GPU都支持直通
3. **稳定性**: 可能影响系统稳定性
4. **许可证**: 确保VMware许可证支持GPU功能

## 🎯 推荐配置

对于深度学习开发，推荐配置：
- **CPU**: 8核以上
- **内存**: 16GB以上
- **GPU**: RTX 3060以上
- **存储**: SSD 500GB以上
- **VMware**: Workstation Pro最新版 