# 消防智能场景预案管理系统

一个基于 `FastAPI + Vue3` 的本地化消防预案管理与可视化系统。

本项目面向消防救援预案场景，支持：

- 批量扫描本地 `.doc` 预案文件
- 使用本机 Microsoft Word 将 `.doc` 转换为 `.docx`
- 解析预案中的表格与图像资料
- 以大屏可视化方式展示预案内容
- 按 `支队 / 大队 / 中队` 层级分类检索预案

## 项目结构

```text
platform/
  backend/          # FastAPI 后端
  frontend/         # Vue3 前端
  预案/             # 本地预案目录（默认不上传）
  README.md
  DEPLOYMENT.md
```

## 技术栈

### 后端

- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite
- pywin32
- python-docx

### 前端

- Vue 3
- Vite
- TailwindCSS
- Axios

## 核心功能

### 1. 预案扫描与同步

后端支持扫描本地 `预案/` 目录中的 `.doc` 文件，并自动：

- 转换为 `.docx`
- 解析表格内容
- 提取图片资源
- 写入 SQLite

接口：

- `POST /api/sync`

### 2. 预案列表与详情

接口：

- `GET /api/plans`
- `GET /api/plans/{id}`
- `GET /api/plans/{id}/document`

其中 `/document` 接口用于前端大屏展示原始章节内容、表格和图片。

### 3. 分类管理

预案文件支持放置在如下任意层级：

- `预案/`
- `预案/支队/`
- `预案/支队/大队/`
- `预案/支队/大队/中队/`

前端会根据文件所在目录自动构建 `支队 / 大队 / 中队` 层级分类。

## 本地运行

### 启动后端

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 启动前端

```powershell
cd frontend
npm install
npm run dev
```

打开浏览器访问：

```text
http://localhost:5173
```

## 注意事项

- `.doc -> .docx` 转换依赖本机安装的 **Microsoft Word**
- `预案/`、`backend/data/`、`backend/static/images/` 默认不纳入 Git
- 当前系统优先保证本地使用与展示稳定性

## 部署说明

详见：

[DEPLOYMENT.md](D:\AI_workspace\智能场景-消防队\platform\DEPLOYMENT.md)
