# 消防智能场景预案管理系统

## 项目结构

```text
platform/
  backend/
  frontend/
  预案/
```

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

接口:

- `POST /api/sync`: 扫描 `../预案` 下的 `.doc` 文件，转换、解析并写入 SQLite。
- `GET /api/plans`: 获取预案列表。
- `GET /api/plans/{id}`: 获取结构化键值对和图片路径。

说明:

- `.doc -> .docx` 依赖本机安装的 Microsoft Word 和 `pywin32`。
- 图片会保存到 `backend/static/images/`。
- SQLite 数据库保存在 `backend/data/plans.db`。

## Frontend

```bash
cd frontend
npm install
npm run dev
```

默认读取 `http://127.0.0.1:8000`。
