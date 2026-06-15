# SmsForwarder Server

Webhook 设备挂载与 SmsForwarder HTTP API 查询网关。

## 功能

- FastAPI 后端服务
- JWT 登录与权限校验
- 设备管理
- Webhook token 创建、轮换、接收
- Webhook 事件入库与数据库唯一约束去重
- SmsForwarder 实时查询 Adapter
- `mode=cache` 本地事件缓存查询
- SQLite 开发数据库，可通过 `DATABASE_URL` 切换 PostgreSQL

## 本地开发

```bash
uv sync --extra dev
cp .env.example .env
uv run alembic upgrade head
uv run python -m app.cli.create_admin admin secret123
uv run uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://localhost:8000/api/v1/healthz
```

## 基本流程

登录：

```bash
TOKEN=$(curl -s http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"secret123"}' | jq -r '.data.access_token')
```

创建设备：

```bash
curl http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"device_name":"phone","channel_type":"hybrid"}'
```

创建 Webhook：

```bash
curl -X POST http://localhost:8000/api/v1/devices/{device_id}/webhook \
  -H "Authorization: Bearer $TOKEN"
```

设备上报：

```bash
curl http://localhost:8000/api/v1/webhooks/smsforwarder/{webhook_token} \
  -H 'Content-Type: application/json' \
  -d '{"event_type":"sms","event_id":"evt-1","phone":"13812345678","content":"hello"}'
```

缓存查询：

```bash
curl http://localhost:8000/api/v1/devices/{device_id}/sms/query \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"mode":"cache","page_num":1,"page_size":10}'
```

## 前端控制台

项目包含 `frontend/` React SPA 管理台。开发时通过 Vite 代理访问后端 API，生产构建后由 FastAPI 同源托管。

开发启动：

```bash
# 后端
uv run uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`，前端会把 `/api/*` 代理到 `http://localhost:8000`。

生产构建：

```bash
cd frontend
npm run build
cd ..
uv run uvicorn app.main:app --port 8000
```

构建产物位于 `frontend/dist`。当该目录存在时，FastAPI 会在 `/` 托管控制台页面，`/api/v1/*` 仍由后端接口处理。

## 验证

```bash
uv run ruff check app tests
uv run pytest
uv run python -m compileall app tests
cd frontend && npm run build
```
