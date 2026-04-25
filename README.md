# 消防预案管理系统

一个面向消防救援场景的本地化预案管理与可视化项目，当前项目由 `FastAPI + Vue 3 + Cesium` 组成，支持 Word 预案解析、分类管理、数据库主存展示、表格内容回写，以及三维模型资源关联预览。

## 当前能力

- 扫描 `预案/` 目录中的 `.doc` 文件并写入 SQLite
- 依赖本机 Microsoft Word 将 `.doc` 转换为 `.docx`
- 解析预案中的章节、表格、图片并在前端展示
- 按 `支队 / 大队 / 中队` 目录层级自动生成分类
- 支持重新导入单个预案，使用原始 Word 内容覆盖数据库主存
- 支持对可编辑表格单元格进行前端修改并回写数据库
- 支持为当前预案导入 `3D/` 目录下的三维模型资源
- 支持通过 Cesium 预览 `3D Tiles`，通过 `model-viewer` 预览 `glb/gltf`

## 项目结构

```text
platform/
  backend/                     # FastAPI 后端
  frontend/                    # Vue3 + Vite 前端
  预案/                        # 原始消防预案目录
  3D/                          # 默认三维模型源目录
  OSGB/                        # 原始 OSGB 资源目录（如有）
  start_backend.bat            # 启动后端
  start_frontend.bat           # 启动前端
  start_all.bat                # 一键启动前后端
  sync_plans.bat               # 手动触发预案同步
  README.md
  DEPLOYMENT.md
```

## 技术栈

- 后端：Python 3.10+、FastAPI、SQLAlchemy、SQLite、pywin32、python-docx
- 前端：Vue 3、Vite、Axios、Cesium、`@google/model-viewer`
- 运行环境：推荐 Windows 10 / 11

## 关键目录

- `预案/`：原始 `.doc` 预案目录，支持多级分类
- `backend/data/plans.db`：SQLite 主数据库
- `backend/data/docx_cache/`：Word 转换后的缓存目录
- `backend/static/images/`：解析出的图片资源
- `3D/`：默认模型导入源目录
- `frontend/public/vendor/Cesium/`：本地 Cesium 运行资源

## 主要接口

- `GET /health`：健康检查
- `GET /api/plans`：预案列表
- `GET /api/plans/{id}`：预案详情
- `GET /api/plans/{id}/document`：预案结构化文档内容
- `POST /api/sync`：扫描并同步 `预案/`
- `POST /api/plans/{id}/reimport`：重新导入单个预案
- `PATCH /api/plans/{id}/document/cell`：更新表格单元格
- `GET /api/categories`：获取分类树
- `POST /api/categories`：创建分类目录
- `POST /api/plans/{id}/move`：移动预案到指定分类
- `GET /api/plans/{id}/model`：读取关联模型
- `POST /api/plans/{id}/model/import`：为当前预案导入模型

## 本地运行

### 方式一：直接双击脚本

推荐在 Windows 下直接使用：

- `start_all.bat`
- `start_backend.bat`
- `start_frontend.bat`
- `sync_plans.bat`

默认前端地址：

```text
http://localhost:5173
```

默认后端地址：

```text
http://127.0.0.1:8000
```

### 方式二：手动启动

后端：

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

## 预案目录约定

预案支持以下目录形式：

- `预案/`
- `预案/支队/`
- `预案/支队/大队/`
- `预案/支队/大队/中队/`

系统会根据文件所在路径自动生成 `brigade / battalion / station` 分类信息。

## 三维模型说明

- 点击前端“导入当前 OSGB 模型”会调用 `POST /api/plans/{id}/model/import`
- 未传参时，后端默认从项目根目录 `3D/` 复制资源
- 复制后的模型会放入当前预案同名目录下，并通过 `/plan-assets` 暴露给前端
- 若模型目录中包含 `tileset.json`，前端会使用 Cesium 进行预览
- 若文件为 `glb` 或 `gltf`，前端会使用 `model-viewer` 进行预览

## 注意事项

- `.doc -> .docx` 转换必须依赖本机安装 Microsoft Word
- 首次使用前建议手动打开一次 Word，避免 COM 初始化异常
- 当前后端默认将 `预案/` 目录通过 `/plan-assets` 暴露为静态资源
- 前端开发服务器默认监听 `0.0.0.0:5173`
- 仓库中可能包含较大的三维资源与 Cesium 静态文件，同步 Git 前建议先确认需要提交的范围

## 更多说明

部署与迁移请查看 [DEPLOYMENT.md](./DEPLOYMENT.md)。
