# 消防智能场景预案管理系统部署文档

## 1. 适用环境

本项目建议部署在 `Windows` 环境中。

原因：

- 系统使用 `pywin32 + Microsoft Word COM` 处理 `.doc`
- 如果没有安装 Microsoft Word，将无法完成 `.doc -> .docx` 转换

## 2. 环境要求

建议安装：

- Windows 10 / Windows 11
- Python 3.10 及以上
- Node.js 18 及以上
- npm
- Microsoft Word

检查版本：

```powershell
python --version
node -v
npm -v
```

## 3. 拷贝项目

将整个项目目录复制到新电脑，例如：

```text
D:\AI_workspace\智能场景-消防队\platform
```

至少需要带过去：

- `backend/`
- `frontend/`
- `README.md`
- `DEPLOYMENT.md`

如果你希望新电脑打开后直接看到现有预案数据，还需要带过去：

- `backend/data/plans.db`
- `backend/data/docx_cache/`
- `backend/static/images/`

如果还要继续导入新的预案文件，再复制：

- `预案/`

## 4. 安装后端依赖

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\backend
python -m pip install -r requirements.txt
```

如果 `pywin32` 装完后 Word COM 有问题，可以执行：

```powershell
python -m pywin32_postinstall -install
```

## 5. 安装前端依赖

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npm install
```

## 6. 启动方式

### 启动后端

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 启动前端

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npm run dev
```

浏览器访问：

```text
http://localhost:5173
```

## 7. 局域网部署

如果要让局域网其他电脑访问：

### 后端

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端

```powershell
npm run dev -- --host 0.0.0.0
```

然后通过部署机器的局域网 IP 访问，例如：

```text
http://192.168.0.66:5173
```

## 8. 数据目录说明

### 原始预案目录

```text
platform/预案/
```

### SQLite 数据库

```text
platform/backend/data/plans.db
```

### docx 缓存目录

```text
platform/backend/data/docx_cache/
```

### 图片输出目录

```text
platform/backend/static/images/
```

## 9. 导入新的 `.doc` 预案

1. 将新的 `.doc` 文件放入：

```text
platform/预案/
```

也可以按分类放入：

```text
预案/支队/
预案/支队/大队/
预案/支队/大队/中队/
```

2. 启动后端
3. 在前端点击“同步预案目录”，或直接调用接口：

```powershell
curl -X POST http://127.0.0.1:8000/api/sync
```

## 10. 常见问题

### 10.1 `.doc` 无法转换

常见原因：

- 未安装 Microsoft Word
- `pywin32` 未正确安装
- Word 首次启动需要人工初始化

建议处理：

1. 手动打开一次 Word 再关闭
2. 执行：

```powershell
python -m pywin32_postinstall -install
```

3. 再次尝试同步

### 10.2 前端打开但没有数据

先检查：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/plans
```

如果这两个接口正常，前端一般就能显示数据。

### 10.3 图片不显示

检查目录：

```text
backend/static/images/
```

如果数据库带过去了但图片目录没带过去，会出现“有数据但无图”的情况。

### 10.4 新电脑只想查看，不想重新同步

直接带过去这些目录和文件即可：

- `backend/data/plans.db`
- `backend/data/docx_cache/`
- `backend/static/images/`

## 11. 推荐部署方式

如果只是你自己在另一台 Windows 电脑上长期使用，推荐流程：

1. 安装 Python
2. 安装 Node.js
3. 安装 Microsoft Word
4. 复制项目目录
5. 安装后端依赖
6. 安装前端依赖
7. 如果只看历史数据，复制已有数据库和图片
8. 启动后端和前端

## 12. 后续可选增强

后续如果需要，我可以继续帮你补：

- `start_backend.bat`
- `start_frontend.bat`
- `sync_plans.bat`

这样在新电脑上可以双击启动，而不需要每次手输命令。
