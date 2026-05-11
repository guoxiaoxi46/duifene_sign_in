# 本项目在开发过程中参考并借鉴了仓库 https://github.com/liuzhijie443/duifene_auto_sign 的部分实现与思路，特此致谢。
# duidenyi

对分易自动签到工具（桌面 GUI）。

官网：
https://www.duifene.com/

支持能力：
- 登录后监听课程签到
- 签到码签到
- 二维码签到（建议使用微信链接登录）
- 位置签到

## 1. 使用前说明

- 本项目为 Python 程序，推荐 Python 3.10 及以上。
- 建议使用虚拟环境，避免污染系统 Python 包。
- 首次登录后会在项目目录生成 `duifenyi.ini` 保存 Cookie（登录态）。

## 2. Windows 从零开始完整教程（每一步命令）

下面命令默认在 PowerShell 中执行。

### 2.1 打开 PowerShell

在项目目标目录打开终端，例如要放在 `D:\duifenyi`。

### 2.2 准备并解压项目压缩包

```powershell
cd D:\duifenyi
```

把你收到的项目压缩包（例如 `duifene_auto_sign.zip`）放到 `D:\duifenyi`，然后解压。

可以用资源管理器右键解压，或用 PowerShell 命令解压：

```powershell
Expand-Archive -Path .\duifene_auto_sign.zip -DestinationPath .\duifene_auto_sign
```

### 2.3 检查 Python

```powershell
python --version
```

如果上面不可用，再试：

```powershell
py --version
```

### 2.4 进入项目目录

```powershell
cd .\duifene_auto_sign
```

### 2.5 创建虚拟环境

```powershell
python -m venv .venv
```

如果你是用 `py` 命令：

```powershell
py -m venv .venv
```

### 2.6 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

激活后，命令行前面会出现 `(.venv)`。

如果 PowerShell 拒绝执行脚本，先执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

再重新执行激活命令：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2.7 升级 pip（推荐）

```powershell
python -m pip install --upgrade pip
```

### 2.8 安装依赖

```powershell
pip install -r requirements.txt
```

### 2.9 启动程序

```powershell
python main.py
```

## 3. 程序内如何操作（非终端）

### 3.1 选择登录方式

- 微信链接登录（推荐）：支持二维码/签到码等。
- 账号密码登录：不支持二维码签到。

### 3.2 选择课程

登录成功后，课程会出现在下拉框中，选择要监听的课程。

### 3.3 设置延迟签到秒数

界面中有“开始后延迟X秒”输入框。
- 例如填 15，表示检测到签到开始后，等待 15 秒再尝试签到。

### 3.4 开始监听

点击“开始监听签到”。

## 4. 每次下次怎么启动（最简命令）

以后每次使用，只要按下面 4 条命令：

```powershell
cd D:\duifenyi\duifene_auto_sign
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

说明：
- 第 3 条可选。只在你更新了依赖时再执行也可以。

## 5. 更新项目代码（可选）

你发给别人新版本时，建议直接重新解压覆盖旧目录（先备份 `duifenyi.ini`）。

覆盖后建议重新安装一次依赖：

```powershell
pip install -r requirements.txt
```

## 6. 常见问题排查（带命令）

### 6.1 运行时报缺少模块

先确认虚拟环境已激活，再执行：

```powershell
pip install -r requirements.txt
```

### 6.2 想确认当前 Python 是否来自虚拟环境

```powershell
where python
python --version
pip --version
```

### 6.3 快速检查代码语法

```powershell
python -m py_compile main.py
```

没有输出通常代表语法通过。

### 6.4 退出虚拟环境

```powershell
deactivate
```

## 7. 一键复制版（首次安装）

如果你已经装好 Python，并且压缩包已经放在 `D:\duifenyi`，可以按顺序直接粘贴执行：

```powershell
cd D:\duifenyi
Expand-Archive -Path .\duifene_auto_sign.zip -DestinationPath .\duifene_auto_sign
cd .\duifene_auto_sign
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## 8. 免责声明

- 本项目仅供学习与技术研究。
- 请遵守学校、课堂与平台规则，使用风险由使用者自行承担。

## 9. 打包为 exe

如果你要在 Windows 上生成可执行文件，可以直接运行仓库中的 `build_exe.ps1`，生成结果会输出到 `dist\duidenyi.exe`。
