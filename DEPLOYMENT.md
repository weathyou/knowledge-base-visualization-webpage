# 消防预案管理系统部署说明

## 1. 适用环境

推荐部署在 `Windows 10 / Windows 11`。

原因：

- 项目使用 `pywin32 + Microsoft Word COM` 处理 `.doc`
- 若未安装 Microsoft Word，则无法完成 `.doc -> .docx` 转换
- 当前提供的启动脚本为 `.bat`，默认面向 Windows 使用

## 2. 环境要求

- Python 3.10 及以上
- Node.js 18 及以上
- npm
- Microsoft Word

检查命令：

```powershell
python --version
node -v
npm -v
```

## 3. 建议部署目录

```text
D:\AI_workspace\智能场景-消防队\platform
```

项目至少应包含：

- `backend/`
- `frontend/`
- `预案/`
- `README.md`
- `DEPLOYMENT.md`

如果还需要现有历史数据与缓存，请一并保留：

- `backend/data/plans.db`
- `backend/data/docx_cache/`
- `backend/static/images/`

如果需要三维模型能力，也请保留：

- `3D/`
- `frontend/public/vendor/Cesium/`

## 4. 安装后端依赖

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\backend
python -m pip install -r requirements.txt
```

若 `pywin32` 安装后仍无法正常调用 Word，可执行：

```powershell
python -m pywin32_postinstall -install
```

## 5. 安装前端依赖

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npm install
```

说明：

- `start_frontend.bat` 会在缺少 `node_modules` 时自动执行 `npm install`
- 如果你使用的是离线环境，建议先在联网环境完成依赖安装

## 6. 启动方式

### 方式一：脚本启动

项目根目录已经提供：

- `start_backend.bat`
- `start_frontend.bat`
- `start_all.bat`
- `sync_plans.bat`

推荐普通使用者直接双击：

```text
start_all.bat
```

### 方式二：命令行启动

后端：

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd D:\AI_workspace\智能场景-消防队\platform\frontend
npm run dev
```

默认访问地址：

```text
前端: http://localhost:5173
后端: http://127.0.0.1:8000
文档: http://127.0.0.1:8000/docs
```

## 7. 局域网访问

当前前端 Vite 已配置为监听 `0.0.0.0:5173`，如果后端也需要被局域网访问，请使用：

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

随后可通过部署机器 IP 访问，例如：

```text
http://192.168.0.66:5173
```

注意：

- 前端请求默认会优先尝试 `http://127.0.0.1:8000`、`http://localhost:8000` 和当前源地址
- 若客户端浏览器与后端不在同一台机器，建议统一通过部署机地址访问前后端

## 8. 数据与资源目录

### 原始预案目录

```text
platform/预案/
```

### 数据库

```text
platform/backend/data/plans.db
```

### docx 缓存

```text
platform/backend/data/docx_cache/
```

### 图片资源

```text
platform/backend/static/images/
```

### 三维模型默认源目录

```text
platform/3D/
```

### 预案资源暴露目录

后端会将整个 `预案/` 目录挂载到：

```text
/plan-assets
```

这意味着：

- 导入到预案目录中的模型、图片、文本都可被前端直接读取
- 预案目录下不要放置不希望被页面访问的敏感文件

## 9. 导入与同步预案

1. 将 `.doc` 文件放入：

```text
platform/预案/
```

也可以按分类放置：

```text
预案/支队/
预案/支队/大队/
预案/支队/大队/中队/
```

2. 启动后端
3. 使用以下任一方式触发同步：

- 前端点击“同步预案目录”
- 双击 `sync_plans.bat`
- 手动调用接口

```powershell
curl -X POST http://127.0.0.1:8000/api/sync
```

## 10. 重新导入与编辑说明

- `POST /api/plans/{id}/reimport`：从原始 Word 重新导入当前预案
- `PATCH /api/plans/{id}/document/cell`：将前端编辑结果回写数据库主存

建议：

- 若只是修正数据库中的展示内容，可直接在前端编辑表格单元格
- 若原始 Word 文件已经变更，应执行重新导入

## 11. 三维模型部署说明

- 默认模型源目录为 `platform/3D/`
- 前端点击“导入当前 OSGB 模型”时，后端会将该目录复制到当前预案同名目录下
- 复制后的路径会登记到数据库 `PlanModelAsset`
- 前端模型页会根据文件类型进行预览：

```text
tileset.json -> Cesium
glb/gltf    -> model-viewer
图片文件      -> 直接预览
json/xml/txt -> 文本预览
osgb/osg     -> 仅展示文件信息，不直接渲染
```

说明：

- 当前按钮文案为“导入当前 OSGB 模型”，但默认复制源目录实际是项目根目录 `3D/`
- 如果后续要按预案选择不同模型源目录，可以再扩展接口参数 `source_path`

## 12. 常见问题

### 12.1 `.doc` 无法转换

常见原因：

- 未安装 Microsoft Word
- `pywin32` 未正确安装
- Word 首次启动尚未完成初始化

建议处理：

1. 手动打开一次 Word 后关闭
2. 执行：

```powershell
python -m pywin32_postinstall -install
```

3. 再次尝试同步

### 12.2 前端打开但没有数据

先检查：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/plans
```

若接口正常但页面为空，通常是：

- 尚未执行 `/api/sync`
- `预案/` 目录下没有符合要求的 `.doc`
- 当前筛选条件没有命中数据

### 12.3 图片或模型不显示

检查以下目录或路径是否存在：

- `backend/static/images/`
- `预案/<分类>/<预案名>/3D/`
- `/plan-assets/...`

若数据库存在而资源目录缺失，会出现“有记录但无法预览”的情况。

### 12.4 新电脑只想查看历史数据

至少复制：

- `backend/data/plans.db`
- `backend/data/docx_cache/`
- `backend/static/images/`

如果还要查看关联模型，也应复制预案目录下对应的模型资源。

## 13. Git 同步建议

当前仓库可能包含大体积三维资源、Cesium vendor 文件和本地数据目录。推送到 GitHub 前建议先确认：

- 是否需要提交 `3D/`、`OSGB/`、Cesium 静态资源
- 是否需要排除本地数据、缓存和图片目录
- 是否只同步文档与代码，还是同时同步资源文件

如果只是更新说明文档，建议仅提交：

- `README.md`
- `DEPLOYMENT.md`
