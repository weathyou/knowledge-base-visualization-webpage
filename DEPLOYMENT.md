# 消防智能场景预案管理系统部署文档

## 1. 部署前说明

这套系统目前适合部署在 `Windows` 电脑上，原因是：

- 后端使用了 `pywin32 + Microsoft Word COM` 来把 `.doc` 转成 `.docx`
- 如果没有安装 `Microsoft Word`，系统无法自动转换老式 `.doc` 文件

如果你的新电脑只需要“查看已经导入好的数据”，可以不放新的 `.doc` 文件；  
如果你还要继续导入新的 `.doc` 预案，必须安装 `Microsoft Word`

## 2. 新电脑需要准备的环境

建议环境：

- Windows 10 或 Windows 11
- Python 3.10 及以上
- Node.js 18 及以上
- npm
- Microsoft Word

建议先检查版本：

```powershell
python --version
node -v
npm -v
```

## 3. 拷贝项目

把整个项目目录完整复制到新电脑，例如：

```text
D:\AI_workspace\智能场景-消防队\platform
```

必须一并带过去的目录和文件：

- `backend/`
- `frontend/`
- `预案/`
- `README.md`
- `DEPLOYMENT.md`

如果你希望把当前已经同步好的数据库和图片也带过去，请同时复制：

- `backend/data/plans.db`
- `backend/data/docx_cache/`
- `backend/static/images/`

这样新电脑上打开后就能直接看到已有数据，不必重新全量同步。

## 4. 安装后端依赖

进入后端目录：

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\backend
```

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

如果安装 `pywin32` 后第一次使用 Word COM 失败，可以执行：

```powershell
python -m pywin32_postinstall -install
```

## 5. 安装前端依赖

进入前端目录：

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
```

安装依赖：

```powershell
npm install
```

## 6. 运行方式

### 6.1 启动后端

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

如果你希望局域网内其他电脑也能访问，把 `127.0.0.1` 改成 `0.0.0.0`：

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6.2 启动前端开发模式

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

## 7. 生产环境建议启动方式

如果你不想每次都跑前端开发服务，建议在新电脑上直接打包前端：

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npm run build
```

打包后会生成：

```text
frontend/dist/
```

你可以用任意静态服务器托管它，例如：

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npx vite preview --host 0.0.0.0 --port 4173
```

或使用 nginx、IIS 等静态服务托管 `dist/`

## 8. 数据目录说明

### 8.1 原始预案目录

系统默认扫描目录：

```text
D:\AI_workspace\智能场景-消防队\platform\预案
```

如果你把项目放在别的盘符，只要保持目录结构不变即可。

### 8.2 SQLite 数据库

数据库位置：

```text
backend/data/plans.db
```

### 8.3 docx 缓存

`.doc` 转换后的缓存目录：

```text
backend/data/docx_cache
```

### 8.4 图片提取目录

提取出的图片目录：

```text
backend/static/images
```

## 9. 导入新的 .doc 预案

### 9.1 导入步骤

1. 把新的 `.doc` 文件复制到：

```text
预案/
```

2. 启动后端

3. 打开前端，点击“同步预案目录”

或者直接调用接口：

```powershell
curl -X POST http://127.0.0.1:8000/api/sync
```

### 9.2 同步逻辑

系统会自动：

- 扫描 `.doc`
- 调用 Word 转 `.docx`
- 解析表格
- 提取图片
- 写入 SQLite
- 对未修改的旧文件自动跳过

## 10. 局域网访问部署

如果你想让同一局域网内其他电脑访问：

### 10.1 后端

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 10.2 前端

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npm run dev -- --host 0.0.0.0
```

然后用部署电脑的局域网 IP 访问，例如：

```text
http://192.168.1.20:5173
```

如果前端需要访问后端，也要确保：

- 防火墙放行 `8000` 和 `5173`
- 局域网电脑能访问部署机 IP

## 11. 常见问题

### 11.1 `.doc` 无法转换

常见原因：

- 新电脑没有安装 Microsoft Word
- `pywin32` 没安装完整
- Word 首次启动需要人工初始化

建议处理：

1. 手动打开一次 Word 再关闭
2. 执行：

```powershell
python -m pywin32_postinstall -install
```

3. 再次尝试同步

### 11.2 前端打开但没有数据

先检查：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/plans
```

如果这两个接口正常，前端一般就能显示数据。

### 11.3 图片不显示

检查目录是否存在：

```text
backend/static/images
```

如果数据库带过去了但图片目录没带过去，页面会有数据但没有图。

### 11.4 另一台电脑只想看，不想重新导入

最简单方式：

直接复制这几项：

- `backend/data/plans.db`
- `backend/data/docx_cache/`
- `backend/static/images/`

这样不用重新同步历史预案。

## 12. 推荐的最稳部署方式

如果是你自己在另一台 Windows 电脑上长期使用，我建议这样做：

1. 安装 Python
2. 安装 Node.js
3. 安装 Microsoft Word
4. 复制整个项目目录
5. 安装后端依赖
6. 安装前端依赖
7. 如果只是查看历史数据，直接复制已有 `plans.db` 和 `images/`
8. 启动后端和前端

## 13. 一键启动建议

后续如果你愿意，我可以继续帮你补：

- `start_backend.bat`
- `start_frontend.bat`
- `sync_plans.bat`

这样你在新电脑上基本双击就能启动，不需要每次手输命令。
