# 设备 Webhook 挂载与 SmsForwarder Server API 查询对接需求文档

## 1. 文档目的

本文档用于设计一个基于 **Python FastAPI** 的设备接入与查询平台。

平台目标是在现有 B/S 架构下，**不使用 WebSocket**，改为通过 **Webhook 接口**让设备主动挂载到平台，并通过平台统一 API 查询设备数据。

对于当前 SmsForwarder 已有能力，平台需要兼容其两类能力：

1. **Webhook 发送通道**：设备可将短信、来电、通知、电量等事件主动推送到平台 Webhook，用于设备挂载、状态上报、事件入库。
2. **Server 端 HTTP API**：平台可通过公网服务器、Frp、VPN、内网穿透等方式访问 SmsForwarder 暴露的查询接口，实现短信、通话、联系人、电量、定位等实时查询。

本文档覆盖：

- 设备 Webhook 挂载设计
- FastAPI 服务端架构
- SmsForwarder Server API 对接说明
- 设备数据查询 API 设计
- Webhook 事件接收、验签、去重、入库设计
- 数据库设计
- 安全、鉴权、审计、限流设计
- 技术栈推荐
- 分阶段落地规划

---

## 2. 背景说明

当前系统采用 B/S 架构，服务端部署在公网服务器。设备通常位于局域网、移动网络、NAT 或运营商 CGNAT 环境中，公网服务端无法稳定直接访问设备。

在不使用 WebSocket 的前提下，设备接入平台有两种方式：

1. **设备主动 Webhook 上报**：设备将事件推送到平台，例如短信、来电、通知、电量状态等。
2. **平台主动 HTTP 查询设备**：当需要实时查询短信、通话、联系人、电量、定位时，平台通过 SmsForwarder Server API 调用设备。

因此，Webhook 主要解决：

- 设备挂载
- 设备身份绑定
- 设备在线/活跃状态更新
- 事件数据上报
- 缓存数据查询

Server API 主要解决：

- 实时查短信
- 实时查通话记录
- 实时查联系人
- 实时查电量
- 实时查定位
- 查询服务端配置

平台需要将 Webhook 上报数据与 Server API 查询能力统一抽象，对外提供一致的设备数据 API。

---

## 3. 重要边界说明

Webhook 是 **设备主动调用平台** 的单向 HTTP 请求，不是长连接。

因此：

1. Webhook 本身不能像 WebSocket 一样让服务端实时向设备下发命令。
2. 如果平台需要实时查询设备数据，仍然需要设备的 SmsForwarder Server API 可被平台访问。
3. 如果设备 Server API 不可达，平台只能返回 Webhook 已上报的缓存数据，无法实时拉取设备数据。

所以本设计采用：

```text
Webhook：设备挂载、事件上报、活跃状态、缓存数据
Server API：实时查询设备数据
```

---

## 4. 建设目标

### 4.1 业务目标

1. 支持设备通过 Webhook 主动挂载到平台。
2. 支持设备事件上报，包括短信、来电、通知、电量等。
3. 支持根据 Webhook 上报更新设备活跃状态。
4. 支持平台通过统一 HTTP API 查询设备数据。
5. 支持对接 SmsForwarder 现有 Server HTTP API。
6. 支持通过 Frp、VPN、内网穿透等方式访问设备本地服务。
7. 支持短信、通话、联系人、电量、定位、配置查询。
8. 支持 Webhook 验签、去重、幂等处理。
9. 支持请求超时、错误处理、操作审计、日志脱敏。
10. 支持设备权限、用户权限、API 限流、安全鉴权。
11. **中间件极简化**：数据库仅用 PostgreSQL 或 SQLite，移除 Redis、MQ 等额外中间件依赖；部署层使用 Nginx 作为容器内统一入口，仅对外暴露一个端口。

### 4.2 非目标

V1 阶段不强制实现：

- 修改 SmsForwarder 源码
- WebSocket 设备长连接
- 原生设备端 Agent 开发
- 设备主动拉取平台命令
- 批量设备调度
- 查询结果长期全量存储
- 独立缓存中间件（Redis）

---

## 5. 总体架构

### 5.1 推荐架构

```text
浏览器 / 第三方系统
        │
        │ HTTPS
        ▼
FastAPI 应用服务
        │
        ├── REST API 模块
        ├── Webhook Receiver 模块
        ├── Device Command Service
        ├── SmsForwarder Adapter
        └── Auth / Audit / RateLimit
        │
        └── PostgreSQL 或 SQLite
                │
                ├── Webhook 入站
                │       └── SmsForwarder Webhook 发送通道
                │
                └── HTTP / Frp / VPN
                        └── SmsForwarder Server API
```

### 5.2 数据流

#### 5.2.1 设备挂载/事件上报

```text
SmsForwarder 设备
  ↓ Webhook POST
FastAPI Webhook Receiver
  ↓ 验签 / 解析 / 去重
更新设备活跃状态（数据库记录）
  ↓
事件入库
```

#### 5.2.2 平台实时查询设备数据

```text
浏览器 / 第三方系统
  ↓ HTTPS API
FastAPI REST API
  ↓ 权限校验
Device Command Service
  ↓
SmsForwarder HTTP Adapter
  ↓ HTTP / Frp / VPN
SmsForwarder Server API
  ↓
返回实时查询结果
```

#### 5.2.3 平台缓存查询

```text
浏览器 / 第三方系统
  ↓ HTTPS API
FastAPI REST API
  ↓
读取 Webhook 已上报事件（数据库查询）
  ↓
返回缓存数据
```

---

## 6. 通道抽象设计

平台对设备通道做统一抽象：

```text
DeviceChannel
├── WebhookInboundChannel
│   └── 设备主动上报事件、状态、心跳
└── SmsForwarderHttpChannel
    └── 平台主动调用 SmsForwarder Server API
```

对外 API 不关心底层通道。例如：

```text
POST /api/v1/devices/{device_id}/sms/query
```

内部可根据查询模式选择：

- 实时模式：调用 SmsForwarder `/sms/query`
- 缓存模式：读取 Webhook 上报入库的短信事件

---

## 7. 设备 Webhook 挂载设计

### 7.1 Webhook 地址

平台为每个设备或每个租户生成 Webhook 地址。

推荐格式：

```text
POST https://api.example.com/api/v1/webhooks/smsforwarder/{webhook_token}
```

其中 `webhook_token` 是平台生成的随机令牌，用于识别设备或接入配置。

### 7.2 设备挂载方式

在 SmsForwarder 中配置 Webhook 发送通道，将 Webhook URL 设置为平台地址。

设备首次向该 Webhook 地址发送事件时，平台根据以下信息完成挂载：

- `webhook_token`
- 请求签名，若启用
- 上报内容中的设备备注、SIM 信息、设备标识
- 请求来源 IP，仅作为辅助信息

平台可支持两种挂载模式：

#### 模式 A：预创建设备

1. 管理员在平台创建设备。
2. 平台生成 `device_id` 和 `webhook_token`。
3. 管理员将 Webhook URL 配置到 SmsForwarder。
4. 设备首次上报后，平台将设备标记为已挂载。

#### 模式 B：自动创建设备

1. 管理员创建一个接入令牌。
2. 多台设备使用该令牌上报。
3. 平台根据设备备注、SIM 信息或自定义字段生成设备记录。
4. 管理员在后台确认绑定。

V1 推荐使用 **模式 A：预创建设备**，更安全、可控。

### 7.3 Webhook 公共请求格式

由于 SmsForwarder 的 Webhook 发送通道可能支持自定义模板，平台建议定义统一 JSON 模板：

```json
{
  "event_id": "${timestamp}_${from}_${type}",
  "event_type": "sms",
  "device_mark": "${device_mark}",
  "sim_info": "${sim_info}",
  "timestamp": 1781488800000,
  "data": {
    "from": "10086",
    "content": "短信内容",
    "name": "中国移动",
    "sim_id": 0,
    "sub_id": 1
  }
}
```

如果设备无法按统一模板发送，平台需要提供兼容解析器，将原始 Webhook 内容保存到 `raw_payload` 并尽可能解析标准字段。

### 7.4 Webhook 响应格式

平台返回：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "received": true
  },
  "timestamp": 1781488800000
}
```

对于重复事件也应返回成功，避免设备反复重试：

```json
{
  "code": 200,
  "msg": "duplicate ignored",
  "data": {
    "received": true,
    "duplicate": true
  }
}
```

---

## 8. Webhook 事件类型设计

### 8.1 短信事件

```json
{
  "event_id": "sms_1781488800000_10086",
  "event_type": "sms",
  "device_id": "device-001",
  "timestamp": 1781488800000,
  "data": {
    "name": "中国移动",
    "number": "10086",
    "content": "您的验证码是 123456",
    "type": 1,
    "sim_id": 0,
    "sub_id": 1
  }
}
```

### 8.2 来电/通话事件

```json
{
  "event_id": "call_1781488800000_13800138000",
  "event_type": "call",
  "device_id": "device-001",
  "timestamp": 1781488800000,
  "data": {
    "name": "张三",
    "number": "13800138000",
    "type": 1,
    "duration": 0,
    "sim_id": 0,
    "sub_id": 1
  }
}
```

### 8.3 通知事件

```json
{
  "event_id": "notification_1781488800000_com.example.app",
  "event_type": "notification",
  "device_id": "device-001",
  "timestamp": 1781488800000,
  "data": {
    "package_name": "com.example.app",
    "app_name": "示例应用",
    "title": "通知标题",
    "content": "通知内容"
  }
}
```

### 8.4 电量事件

```json
{
  "event_id": "battery_1781488800000",
  "event_type": "battery",
  "device_id": "device-001",
  "timestamp": 1781488800000,
  "data": {
    "level": "82%",
    "status": "充电中",
    "health": "良好",
    "plugged": "AC"
  }
}
```

### 8.5 设备心跳/状态事件

如果 SmsForwarder 可通过自动任务或 Webhook 模板定时上报，可使用：

```json
{
  "event_id": "heartbeat_1781488800000",
  "event_type": "heartbeat",
  "device_id": "device-001",
  "timestamp": 1781488800000,
  "data": {
    "device_mark": "备用机-001",
    "battery_level": "82%",
    "network_type": "wifi"
  }
}
```

如果没有独立心跳，平台将任意有效 Webhook 事件视为设备活跃信号。

---

## 9. SmsForwarder Server API 对接说明

本节基于 SmsForwarder Wiki 中 **"附录2：主动请求(远程控制)"** 的说明整理。

### 9.1 适用版本

| 版本 | 能力 |
|---|---|
| v3.0.0+ | 新版远程控制 API |
| v3.1.0+ | RSA、SM4 加密传输 |
| v3.2.0+ | 远程查定位、远程加话簿 |
| v2.4.4 及以下 | 旧版 HttpServer / SmsHub 轮询机制 |

平台优先对接 v3.x API。

### 9.2 基础访问地址

局域网访问格式：

```text
http://手机IP:5000/<接口URI>
```

默认端口：

```text
5000
```

通过 Frp 内网穿透时，可使用域名或公网端口：

```text
http://smsf.example.com/<接口URI>
http://公网服务器IP:remote_port/<接口URI>
```

### 9.3 请求方式

默认请求方式：

```http
POST
```

请求头：

```http
Content-Type: application/json; charset=utf-8
```

### 9.4 公共请求格式

```json
{
  "data": {},
  "timestamp": 1652590258638,
  "sign": ""
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `data` | Any | 是 | 具体接口参数 |
| `timestamp` | Long | 是 | 当前毫秒时间戳，和调用时间误差不能超过 1 小时 |
| `sign` | String | 否 | 开启签名校验时必填 |

### 9.5 公共响应格式

```json
{
  "code": 200,
  "msg": "success",
  "data": {},
  "timestamp": 1652590258638,
  "sign": ""
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | Int | `200` 成功，`500` 失败 |
| `msg` | String | 成功或失败提示 |
| `data` | Any | 成功时返回业务数据 |
| `timestamp` | Long | 服务端毫秒时间戳 |
| `sign` | String | 服务端启用签名且成功时返回 |

### 9.6 签名规则

签名原文：

```text
timestamp + "\n" + 密钥
```

算法流程：

1. 使用 `HmacSHA256` 计算签名。
2. 对结果进行 Base64 编码。
3. 再进行 URL Encode。
4. 字符集使用 UTF-8。

平台在调用 SmsForwarder API 时，如果设备开启签名校验，需要自动生成 `timestamp` 和 `sign`。

### 9.7 加密传输

#### RSA 加密

适用 v3.1.0+：

- 客户端使用公钥加密请求。
- 服务端使用私钥解密请求。
- 服务端使用私钥加密响应。
- 客户端使用公钥解密响应。
- 加密前报文结构与明文一致。
- 原始报文先 Base64，再 RSA 加密后 POST。

#### SM4 加密

适用 v3.1.0+：

- 客户端和服务端共用 SM4 密钥。
- 请求和响应均使用 SM4 密钥加密。
- 加密前报文结构与明文一致。
- 使用 SmsF 微信小程序作为客户端时必须使用 SM4。

V1 阶段建议优先支持明文 + 签名；V2 支持 SM4；RSA 可作为后续增强。

---

## 10. SmsForwarder 查询接口清单

### 10.1 查询服务端配置

接口：

```text
/config/query
```

建议调用其他接口前先调用该接口，用于判断远程功能是否启用。

请求：

```json
{
  "data": {},
  "timestamp": 1652590258638,
  "sign": ""
}
```

主要返回字段：

| 字段 | 说明 |
|---|---|
| `enable_api_battery_query` | 是否启用远程查电量 |
| `enable_api_call_query` | 是否启用远程查通话 |
| `enable_api_clone` | 是否启用一键换新机 |
| `enable_api_contact_query` | 是否启用远程查话簿 |
| `enable_api_sms_query` | 是否启用远程查短信 |
| `enable_api_sms_send` | 是否启用远程发短信 |
| `enable_api_wol` | 是否启用远程 WOL |
| `extra_device_mark` | 设备备注 |
| `extra_sim1` | SIM1 备注 |
| `extra_sim2` | SIM2 备注 |
| `sim_info_list` | 实时 SIM 卡槽信息 |

### 10.2 远程查短信

接口：

```text
/sms/query
```

请求：

```json
{
  "data": {
    "type": 1,
    "page_num": 1,
    "page_size": 10,
    "keyword": "关键字"
  },
  "timestamp": 1652590258638,
  "sign": ""
}
```

参数：

| 字段 | 类型 | 必填 | 说明 |
|---|---:|---|---|
| `type` | Int | 是 | 短信类型，`1=接收`，`2=发送` |
| `page_num` | Int | 是 | 页码，默认 1 |
| `page_size` | Int | 是 | 每页数量，默认 10 |
| `keyword` | String | 否 | 关键字，模糊匹配短信内容 |

返回数据项：

| 字段 | 说明 |
|---|---|
| `name` | 联系人姓名 |
| `number` | 联系人号码 |
| `content` | 短信内容 |
| `date` | 短信时间 |
| `type` | 短信类型，`1=接收`，`2=发送` |
| `sim_id` | 卡槽 ID，`0=SIM1`，`1=SIM2`，`-1=获取失败` |
| `sub_id` | 卡槽主键，`0=获取失败`，非 0 表示 SIM 插入手机的序号 |

注意：SIM 卡发生变化或被拔出时，`sim_id` 可能返回 `-1`。

### 10.3 远程查通话

接口：

```text
/call/query
```

请求：

```json
{
  "data": {
    "type": 1,
    "page_num": 1,
    "page_size": 10,
    "phone_number": "15888888888"
  },
  "timestamp": 1652590258638,
  "sign": ""
}
```

参数：

| 字段 | 类型 | 必填 | 说明 |
|---|---:|---|---|
| `type` | Int | 否 | 通话类型，`1=呼入`，`2=呼出`，`3=未接`，`0=不筛选` |
| `page_num` | Int | 是 | 页码，默认 1 |
| `page_size` | Int | 是 | 每页数量，默认 10 |
| `phone_number` | String | 否 | 手机号码，模糊匹配 |

返回数据项：

| 字段 | 说明 |
|---|---|
| `name` | 姓名，可为空 |
| `number` | 号码 |
| `dateLong` | 通话日期 |
| `duration` | 通话时长，单位秒 |
| `type` | 通话类型，`1=呼入`，`2=呼出`，`3=未接` |
| `sim_id` | 卡槽 ID，`0=SIM1`，`1=SIM2`，`-1=获取失败` |

### 10.4 远程查联系人

接口：

```text
/contact/query
```

请求：

```json
{
  "data": {
    "phone_number": "15888888888",
    "name": "pppscn"
  },
  "timestamp": 1652590258638,
  "sign": ""
}
```

参数：

| 字段 | 类型 | 必填 | 说明 |
|---|---:|---|---|
| `phone_number` | String | 否 | 手机号码，模糊匹配 |
| `name` | String | 否 | 姓名，模糊匹配 |

返回数据项：

| 字段 | 说明 |
|---|---|
| `name` | 姓名，可为空 |
| `phone_number` | 号码 |

### 10.5 远程查电量

接口：

```text
/battery/query
```

请求：

```json
{
  "data": {},
  "timestamp": 1652590258638,
  "sign": ""
}
```

返回字段：

| 字段 | 说明 |
|---|---|
| `level` | 剩余电量 |
| `scale` | 满电容量 |
| `voltage` | 当前电压，可为空 |
| `temperature` | 当前温度，可为空 |
| `status` | 电池状态 |
| `health` | 健康度 |
| `plugged` | 充电器类型 |

### 10.6 远程查定位

适用 v3.2.0+。

接口：

```text
/location/query
```

请求：

```json
{
  "data": {},
  "timestamp": 1652590258638,
  "sign": ""
}
```

返回字段：

| 字段 | 说明 |
|---|---|
| `address` | GPS 坐标逆转后的地址，可为空 |
| `latitude` | 纬度 |
| `longitude` | 经度 |
| `provider` | 定位供应商，可为空 |
| `time` | 上一次定位时间 |

---

## 11. 其他 SmsForwarder 远程控制接口

### 11.1 远程发短信

接口：

```text
/sms/send
```

请求：

```json
{
  "data": {
    "sim_slot": 1,
    "phone_numbers": "15888888888;19999999999",
    "msg_content": "短信内容"
  },
  "timestamp": 1652590258638,
  "sign": ""
}
```

参数：

| 字段 | 说明 |
|---|---|
| `sim_slot` | 发送卡槽，`1=SIM1`，`2=SIM2` |
| `phone_numbers` | 接收手机号，多个号码用英文分号分隔 |
| `msg_content` | 短信内容，最多 390 字符，最多 6 条短信 |

### 11.2 一键换新机：拉取配置

接口：

```text
/clone/pull
```

请求：

```json
{
  "data": {
    "version_code": 300038
  },
  "timestamp": 1652590258638,
  "sign": ""
}
```

### 11.3 一键换新机：推送配置

接口：

```text
/clone/push
```

### 11.4 远程 WOL

接口：

```text
/wol/send
```

请求：

```json
{
  "data": {
    "mac": "24:5E:BE:0C:45:9A",
    "ip": "192.168.168.168"
  },
  "timestamp": 1652590258638,
  "sign": ""
}
```

### 11.5 远程加话簿

适用 v3.2.0+。

接口：

```text
/contact/add
```

请求：

```json
{
  "timestamp": 1676020173225,
  "sign": "",
  "data": {
    "phone_number": "15888888888;19999999999",
    "name": "真实姓名"
  }
}
```

---

## 12. 平台 REST API 设计

### 12.1 统一响应格式

```json
{
  "code": 200,
  "msg": "success",
  "data": {},
  "request_id": "cmd-001",
  "timestamp": 1781488800000
}
```

### 12.2 Webhook 管理 API

#### 创建设备 Webhook

```http
POST /api/v1/devices/{device_id}/webhook
```

响应：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "webhook_url": "https://api.example.com/api/v1/webhooks/smsforwarder/wh_xxx",
    "webhook_token": "wh_xxx"
  }
}
```

#### 重置设备 Webhook Token

```http
POST /api/v1/devices/{device_id}/webhook/rotate
```

### 12.3 Webhook 接收 API

```http
POST /api/v1/webhooks/smsforwarder/{webhook_token}
```

该接口由设备调用，不需要用户 JWT，但必须通过 `webhook_token`、签名或 IP 策略完成设备鉴权。

### 12.4 设备列表

```http
GET /api/v1/devices
```

### 12.5 设备详情

```http
GET /api/v1/devices/{device_id}
```

### 12.6 查询配置

```http
POST /api/v1/devices/{device_id}/config/query
```

### 12.7 查询短信

```http
POST /api/v1/devices/{device_id}/sms/query
```

请求：

```json
{
  "mode": "realtime",
  "type": 1,
  "page_num": 1,
  "page_size": 10,
  "keyword": ""
}
```

`mode` 说明：

| 值 | 说明 |
|---|---|
| `realtime` | 调用 SmsForwarder Server API 实时查询 |
| `cache` | 查询 Webhook 上报入库的缓存数据 |

### 12.8 查询通话

```http
POST /api/v1/devices/{device_id}/calls/query
```

请求：

```json
{
  "mode": "realtime",
  "type": 0,
  "page_num": 1,
  "page_size": 10,
  "phone_number": ""
}
```

### 12.9 查询联系人

```http
POST /api/v1/devices/{device_id}/contacts/query
```

请求：

```json
{
  "mode": "realtime",
  "page_num": 1,
  "page_size": 10,
  "phone_number": "",
  "name": ""
}
```

### 12.10 查询电量

```http
POST /api/v1/devices/{device_id}/battery/query
```

请求：

```json
{
  "mode": "realtime"
}
```

### 12.11 查询定位

```http
POST /api/v1/devices/{device_id}/location/query
```

请求：

```json
{
  "mode": "realtime"
}
```

---

## 13. FastAPI 项目结构建议

```text
sms-forwarder-server/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logger.py
│   │   └── exceptions.py
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── devices.py
│   │       ├── webhooks.py
│   │       ├── sms.py
│   │       ├── calls.py
│   │       ├── contacts.py
│   │       ├── battery.py
│   │       ├── location.py
│   │       └── config.py
│   ├── adapters/
│   │   ├── base.py
│   │   ├── webhook_parser.py
│   │   └── smsforwarder_http_adapter.py
│   ├── services/
│   │   ├── device_service.py
│   │   ├── command_service.py
│   │   ├── webhook_service.py
│   │   ├── audit_service.py
│   │   └── auth_service.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── device.py
│   │   ├── webhook.py
│   │   ├── command.py
│   │   ├── sms.py
│   │   ├── call.py
│   │   ├── contact.py
│   │   ├── battery.py
│   │   ├── location.py
│   │   └── config.py
│   ├── models/
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── device_webhook.py
│   │   ├── device_event.py
│   │   ├── device_command_log.py
│   │   └── audit_log.py
│   ├── repositories/
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── migrations/
│   └── utils/
│       ├── id_generator.py
│       ├── masking.py
│       ├── rate_limiter.py
│       └── deduplication.py
├── docs/
├── tests/
├── alembic.ini
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 14. 数据库设计

### 14.1 数据库选型原则

中间件最小化，数据库承载所有状态和数据。支持两种选择：

| 数据库 | 适用场景 |
|---|---|
| **PostgreSQL** | 生产部署，多用户并发，需要 JSONB 查询和扩展能力 |
| **SQLite** | 开发调试，单用户或少量设备，零配置 |

代码层面通过 SQLAlchemy 统一封装，切换数据库只需修改连接字符串。

### 14.2 设备表 `devices`

```sql
CREATE TABLE devices (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(128) UNIQUE NOT NULL,
    device_name VARCHAR(255),
    channel_type VARCHAR(64) NOT NULL DEFAULT 'hybrid',
    base_url TEXT,
    sign_secret_encrypted TEXT,
    sm4_key_encrypted TEXT,
    rsa_public_key TEXT,
    platform VARCHAR(64),
    app_version VARCHAR(64),
    protocol_version VARCHAR(32),
    status VARCHAR(32) DEFAULT 'inactive',
    is_active BOOLEAN DEFAULT false,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    last_webhook_at TIMESTAMP WITH TIME ZONE,
    webhook_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

`channel_type` 可选值：

| 值 | 说明 |
|---|---|
| `webhook_only` | 仅接收设备上报，查询只能走缓存 |
| `smsforwarder_http` | 仅通过 SmsForwarder Server API 查询 |
| `hybrid` | Webhook 上报 + Server API 实时查询 |

### 14.3 设备 Webhook 表 `device_webhooks`

```sql
CREATE TABLE device_webhooks (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(128) NOT NULL REFERENCES devices(device_id),
    webhook_token_hash VARCHAR(255) UNIQUE NOT NULL,
    webhook_token_prefix VARCHAR(16) NOT NULL,
    webhook_secret_encrypted TEXT,
    enabled BOOLEAN DEFAULT true,
    last_called_at TIMESTAMP WITH TIME ZONE,
    called_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### 14.4 设备事件表 `device_events`

```sql
CREATE TABLE device_events (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(255),
    device_id VARCHAR(128) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    event_time TIMESTAMP WITH TIME ZONE,
    normalized_payload JSONB,
    raw_payload JSONB,
    source_ip VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(device_id, event_id)
);
```

索引建议：

```sql
CREATE INDEX idx_device_events_device_id ON device_events(device_id);
CREATE INDEX idx_device_events_event_type ON device_events(event_type);
CREATE INDEX idx_device_events_created_at ON device_events(created_at);
```

### 14.5 设备能力表 `device_capabilities`

```sql
CREATE TABLE device_capabilities (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(128) NOT NULL,
    capability VARCHAR(128) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(device_id, capability)
);
```

### 14.6 指令日志表 `device_command_logs`

```sql
CREATE TABLE device_command_logs (
    id BIGSERIAL PRIMARY KEY,
    request_id VARCHAR(128) UNIQUE NOT NULL,
    device_id VARCHAR(128) NOT NULL,
    user_id BIGINT,
    command_type VARCHAR(128) NOT NULL,
    channel_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    request_summary JSONB,
    response_summary JSONB,
    error_msg TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### 14.7 审计日志表 `audit_logs`

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(128) NOT NULL,
    device_id VARCHAR(128),
    client_ip VARCHAR(64),
    user_agent TEXT,
    result VARCHAR(32),
    detail JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### 14.8 用户表 `users`

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(128) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### 14.9 用户权限表 `user_permissions`

```sql
CREATE TABLE user_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    permission VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(128),
    granted BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, permission, resource_type, resource_id)
);
```

---

## 15. 基于数据库的去重、限流与状态管理

由于不依赖 Redis 中间件，去重、限流和活跃状态通过数据库实现。

### 15.1 Event 去重

通过数据库唯一约束实现：

```sql
UNIQUE(device_id, event_id)
```

Webhook 接收时 `INSERT ... ON CONFLICT DO NOTHING`。

### 15.2 设备活跃状态

由 `devices` 表的字段直接记录：

- `last_seen_at`：最后任意事件时间
- `last_webhook_at`：最后 Webhook 上报时间
- `is_active`：活跃标记
- `webhook_count`：上报次数统计

收到任意有效 Webhook 事件后，在同一个事务中更新这些字段。

### 15.3 API 限流

简单限流使用数据库记录时间窗口：

```sql
CREATE TABLE rate_limits (
    id BIGSERIAL PRIMARY KEY,
    resource_key VARCHAR(255) NOT NULL,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    request_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(resource_key, window_start)
);
```

`resource_key` 示例：

```text
webhook:wh_xxx
user:123:sms_query
device:device-001:sms_query
```

限流流程：

1. 计算当前时间窗口起始时间，例如按分钟截断。
2. `INSERT ... ON CONFLICT` 获取或创建窗口记录。
3. 检查 `request_count` 是否超过上限。
4. 递增 `request_count`。
5. 定期清理过期窗口记录。

V1 可以使用简单的 `REFRESH_LOCK` 自旋重试方式。

如果并发量不大，也可以在应用内存中维护限流计数器，通过定期清理或超过上限时回退到数据库持久化。

### 15.4 nonce 防重放

```sql
CREATE TABLE webhook_nonces (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(128) NOT NULL,
    nonce VARCHAR(128) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(device_id, nonce)
);
```

定期清理过期的 nonce 记录。

---

## 16. 安全设计

### 16.1 传输安全

生产环境必须使用：

```text
HTTPS
```

SmsForwarder HTTP API 如经公网访问，必须通过平台后端代理，不建议直接暴露原始接口。

### 16.2 Webhook 鉴权

V1 支持：

- 高强度 `webhook_token`
- HTTPS
- 请求频率限制（数据库记录）
- `event_id` 去重

V2 支持：

- `X-Signature` HMAC 签名
- `X-Timestamp` 时间戳校验
- `X-Nonce` 防重放
- IP 白名单，按需启用

推荐签名原文：

```text
timestamp + "\n" + nonce + "\n" + sha256(body)
```

### 16.3 用户权限

建议权限粒度：

```text
device:view
device:webhook:manage
device:event:view
device:config:query
device:battery:query
device:sms:query
device:call:query
device:contact:query
device:location:query
device:sms:send
device:contact:add
device:admin
```

### 16.4 SmsForwarder HTTP 通道安全

平台调用 SmsForwarder HTTP API 时，需要按设备配置生成：

- `timestamp`
- `sign`
- 加密请求体，V2+

平台不应将设备的原始 `base_url`、签名密钥、SM4 密钥暴露给前端。

### 16.5 日志脱敏

默认不完整记录：

- 短信正文
- 手机号
- 联系人
- 通话号码
- 定位详细地址
- Webhook Token
- 签名密钥
- SM4 密钥
- RSA 私钥

手机号脱敏：

```text
138****5678
```

短信内容日志只记录长度：

```json
{
  "content_length": 68
}
```

### 16.6 限流建议

| 资源 | 限制 | 实现方式 |
|---|---|---|
| 单 Webhook Token 上报 | 120 次/分钟 | 数据库 `rate_limits` 表 |
| 单用户短信查询 | 30 次/分钟 | 数据库 `rate_limits` 表 |
| 单设备短信查询 | 10 次/分钟 | 数据库 `rate_limits` 表 |
| 单设备并发实时查询 | 3 | 应用层信号量 + 超时 |
| API 登录失败 | 10 次/分钟 | 数据库 `rate_limits` 表 |

---

## 17. 错误码设计

| HTTP 状态码 | 业务 code | 说明 |
|---:|---:|---|
| 200 | 200 | 成功 |
| 400 | 400 | 参数错误 |
| 401 | 401 | 未登录/认证失败 |
| 403 | 403 | 无权限 |
| 404 | 404 | 设备不存在 |
| 409 | 409 | 设备通道不可用 |
| 429 | 429 | 请求过于频繁 |
| 500 | 500 | 服务端异常 |
| 502 | 502 | 设备通道响应异常 |
| 504 | 504 | 设备响应超时 |

Webhook 接口即使遇到重复事件，也应返回 200，避免设备反复重试。

---

## 18. Python FastAPI 技术栈推荐

### 18.1 后端核心

| 功能 | 推荐技术 |
|---|---|
| Web 框架 | FastAPI |
| ASGI Server | Uvicorn |
| 数据校验 | Pydantic v2 |
| ORM | SQLAlchemy 2.0 |
| 数据迁移 | Alembic |
| 数据库 | PostgreSQL 或 SQLite |
| HTTP 客户端 | httpx |
| 鉴权 | PyJWT / python-jose |
| 密码哈希 | passlib / bcrypt |
| 配置管理 | pydantic-settings |
| 日志 | structlog / loguru |
| JSON | orjson |
| 测试 | pytest + pytest-asyncio |
| 代码质量 | ruff + mypy |

### 18.2 推荐依赖

PostgreSQL 环境：

```toml
[project]
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "pydantic",
  "pydantic-settings",
  "sqlalchemy",
  "psycopg2-binary",
  "alembic",
  "httpx",
  "python-jose[cryptography]",
  "passlib[bcrypt]",
  "structlog",
  "orjson",
  "pytest",
  "pytest-asyncio",
  "ruff",
  "mypy"
]
```

SQLite 开发/轻量环境：

```toml
[project]
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "pydantic",
  "pydantic-settings",
  "sqlalchemy",
  "alembic",
  "httpx",
  "python-jose[cryptography]",
  "passlib[bcrypt]",
  "structlog",
  "orjson",
  "pytest",
  "pytest-asyncio",
  "ruff",
  "mypy"
]
```

仅 SQLite 时不需要 `psycopg2-binary`，SQLAlchemy 内置支持 SQLite，零额外依赖。

### 18.3 前端推荐

| 功能 | 推荐技术 |
|---|---|
| 框架 | React + TypeScript |
| 构建 | Vite |
| UI | Ant Design / shadcn/ui |
| 请求 | Axios / TanStack Query |
| 状态管理 | Zustand / Redux Toolkit |
| 表格 | TanStack Table / AG Grid |
| 图表 | ECharts / Recharts |

---

## 19. 部署与架构设计

### 19.1 部署目标

项目采用 **React + FastAPI + Nginx** 的 Docker 化部署方式。

核心目标：

1. 前端 React 构建为静态资源。
2. FastAPI 提供后端 API 与 Webhook 接收接口。
3. Nginx 作为容器内统一入口：
   - 反向代理 `/web/` 到前端 React 管理后台。
   - 反向代理 `/api/` 到 FastAPI。
   - 对外只暴露一个 HTTP 端口。
4. 数据库默认使用 SQLite，生产或多用户部署可通过配置切换为 PostgreSQL。
5. 不引入 Redis、MQ、Celery 等额外中间件。

### 19.2 推荐容器架构

#### 默认 SQLite 单容器模式

```text
Docker Compose
└── webapp 单容器
    ├── Nginx，对外暴露唯一端口 80 或 8080
    ├── /web/ → React 静态资源
    ├── /api/ → FastAPI 后台进程
    └── SQLite 文件 /data/smsf.db
```

SQLite 是默认数据库，适合开发、测试、少量设备或单机私有部署。

#### 可配置 PostgreSQL 生产模式

```text
Docker Compose
├── web 容器
│   ├── Nginx，对外暴露唯一端口 80 或 8080
│   ├── React 静态资源
│   └── 反向代理 /api/ 到 api 容器
├── api 容器
│   └── FastAPI，仅 Docker 内网访问，不暴露宿主机端口
└── db 容器
    └── PostgreSQL，仅 Docker 内网访问，不暴露宿主机端口
```

外部访问路径：

```text
http://服务器IP:8080/web/                     → React 前端
http://服务器IP:8080/api/v1/...               → FastAPI API
http://服务器IP:8080/api/v1/webhooks/...      → Webhook 接收接口
```

PostgreSQL 适合生产、多用户、多设备或并发写入场景。

### 19.3 路由设计

Nginx 对外暴露一个端口，内部按路径分流：

| 外部路径 | 目标 | 说明 |
|---|---|---|
| `/` | 302 跳转到 `/web/` | 默认入口 |
| `/web/` | React 静态文件 | 管理后台页面 |
| `/web/assets/` | React 静态资源 | JS/CSS/图片 |
| `/api/` | FastAPI | REST API |
| `/api/v1/webhooks/` | FastAPI | 设备 Webhook 接收 |
| `/api/docs` | FastAPI，可选 | OpenAPI 文档，生产可关闭 |
| `/api/openapi.json` | FastAPI，可选 | OpenAPI Schema，生产可关闭 |

### 19.4 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 2m;

    root /usr/share/nginx/html;
    index index.html;

    location = / {
        return 302 /web/;
    }

    location /web/ {
        alias /usr/share/nginx/html/;
        try_files $uri $uri/ /web/index.html;
    }

    location /api/ {
        proxy_pass http://api:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    location /api/docs {
        proxy_pass http://api:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/openapi.json {
        proxy_pass http://api:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 19.5 Docker Compose，默认 SQLite 单容器模式

默认使用 SQLite，不需要单独启动数据库容器。React、FastAPI、Nginx 在同一个容器内运行，仅对外暴露 Nginx 一个端口。

```yaml
version: "3.8"

services:
  webapp:
    build:
      context: .
      dockerfile: docker/webapp/Dockerfile
    ports:
      - "8080:80"
    environment:
      DATABASE_URL: "sqlite:////data/smsf.db"
    volumes:
      - sqldata:/data

volumes:
  sqldata:
```

宿主机只开放：

```text
8080 → webapp:80
```

外部访问：

```text
http://服务器IP:8080/web/
http://服务器IP:8080/api/v1/...
```

### 19.6 Docker Compose，可配置 PostgreSQL 模式

PostgreSQL 模式用于生产或多用户部署。只对外暴露 `web` 容器的一个端口，`api` 和 `db` 不暴露宿主机端口。

```yaml
version: "3.8"

services:
  web:
    build:
      context: .
      dockerfile: docker/nginx/Dockerfile
    ports:
      - "8080:80"
    depends_on:
      - api

  api:
    build:
      context: .
      dockerfile: docker/api/Dockerfile
    environment:
      DATABASE_URL: "postgresql://user:pass@db:5432/smsf"
    depends_on:
      - db
    expose:
      - "8000"

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: smsf
    volumes:
      - pgdata:/var/lib/postgresql/data
    expose:
      - "5432"

volumes:
  pgdata:
```

宿主机只开放：

```text
8080 → web:80
```

不开放：

```text
FastAPI 8000
PostgreSQL 5432
```

### 19.7 Dockerfile 设计建议

#### React 构建阶段

```dockerfile
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
```

#### FastAPI 镜像

```dockerfile
FROM python:3.12-slim AS api
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Nginx 镜像

```dockerfile
FROM nginx:1.27-alpine
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html
```

SQLite 单容器模式需要进程管理，可使用 `supervisord` 或启动脚本同时启动 Uvicorn 与 Nginx。生产更推荐 PostgreSQL 多容器模式，结构更清晰。

### 19.8 HTTPS 建议

Docker 内部只暴露一个 HTTP 端口。生产 HTTPS 可以选择：

1. 在宿主机或云负载均衡上终止 TLS，再转发到 `8080`。
2. 将证书挂载到 Nginx 容器，在容器内监听 `443`，但仍只暴露一个端口，例如：

```yaml
ports:
  - "443:443"
```

无论选择哪种方式，对外入口都保持单端口原则。

### 19.9 部署约束

1. Docker 对外只暴露一个端口。
2. FastAPI 不直接暴露给公网。
3. 数据库不直接暴露给公网。
4. Webhook URL 与管理后台共用同一域名和端口。
5. SmsForwarder 设备配置 Webhook 时使用：

```text
https://你的域名/api/v1/webhooks/smsforwarder/{webhook_token}
```

6. 平台前端访问：

```text
https://你的域名/web/
```

7. 平台 API 访问：

```text
https://你的域名/api/v1/...
```

---

## 20. 版本规划

### V1：MVP 版本

目标：跑通设备 Webhook 挂载、事件接收、SmsForwarder HTTP API 对接。

功能：

- 用户登录
- 设备管理
- Webhook Token 生成
- Webhook 接收接口
- 设备首次上报挂载
- 设备活跃状态更新（数据库字段）
- Webhook 事件入库
- Webhook 去重（数据库唯一约束）
- SmsForwarder HTTP 明文 + 签名调用
- `/config/query`
- `/sms/query`
- `/call/query`
- `/contact/query`
- `/battery/query`
- `/location/query`
- 基础指令日志
- 基础审计日志
- 单实例部署
- **数据库承载全部状态**
- 数据库：默认 SQLite，可通过 `DATABASE_URL` 切换为 PostgreSQL

### V2：安全增强

新增：

- Webhook HMAC 签名
- Webhook nonce 防重放（数据库 `webhook_nonces` 表）
- SmsForwarder SM4 加密调用
- 数据库限流（`rate_limits` 表）
- 权限细分
- 日志脱敏增强
- Webhook Token 轮换
- API 密钥轮换

### V3：规模化

新增：

- 异步事件处理（SQLAlchemy + 后台 Task）
- 设备分组
- 批量查询
- Prometheus 指标
- Grafana 监控
- 告警通知
- 数据库定期清理策略

---

## 21. 部署与使用注意事项

### 21.1 数据库选型切换

SQLAlchemy 配置通过 `DATABASE_URL` 环境变量控制：

```python
# SQLite 开发
DATABASE_URL=sqlite:///./smsf.db

# PostgreSQL 生产
DATABASE_URL=postgresql://user:pass@localhost:5432/smsf
```

代码中统一使用 SQLAlchemy ORM，不需要为不同数据库修改业务代码。

仅需注意：

- SQLite 不支持并发写入，不要用于多 worker/多实例生产环境
- SQLite 的 `JSONB` 字段降级为 `JSON`，功能一致
- PostgreSQL 更适合生产，支持并发、JSONB 索引、MVCC

### 21.2 数据库清理

由于不使用 Redis 作为缓存，Webhook 事件、日志等数据都存储在数据库中。建议设置定期清理策略：

- Webhook 事件：保留 30~90 天
- 指令日志：保留 30~90 天
- 审计日志：保留 90~365 天
- rate_limits 窗口：保留 1~7 天
- webhook_nonces：保留 24 小时

可通过定时脚本或 FastAPI 后台任务实现。

### 21.3 去重注意事项

由于去重依赖数据库唯一约束：

- `event_id` 必须由设备端生成，保证同一事件每次上报的 `event_id` 一致
- 如果设备端 `event_id` 生成不可靠，建议在 Webhook 处理前由平台补充生成稳定的去重键

### 21.4 限流性能

数据库限流在高并发下可能会有锁竞争。V1 阶段：

- Webhook 上报 120 次/分钟/Tokened
- 用户查询 30 次/分钟

这个量级下单条数据库 `INSERT ... ON CONFLICT` 足够应对。

如果后续并发量显著增大，可以：

- 在应用层增加内存缓存限流
- 或引入简单的文件锁/信号量
- 或升级到 Redis 限流，此时才引入 Redis

---

## 22. 关键设计建议

1. 不使用 WebSocket，设备接入统一通过 Webhook 入站。
2. 不使用 Redis，去重、限流、状态均通过数据库实现。
3. 数据库可选 PostgreSQL 或 SQLite，通过 `DATABASE_URL` 切换。
4. Webhook 负责设备挂载、事件上报、活跃状态，不负责实时命令下发。
5. 实时查询仍通过 SmsForwarder Server API 完成。
6. 如果设备 Server API 不可达，只能返回 Webhook 缓存数据。
7. 平台 API 层不要直接感知底层通道，应通过 `DeviceCommandService` 调用。
8. 设备通道应抽象为 Adapter，便于兼容 Webhook-only、SmsForwarder HTTP、Hybrid 模式。
9. SmsForwarder HTTP API 原始端口不应直接暴露公网。
10. 查询短信、联系人、通话、定位等敏感数据时必须做权限控制和审计。
11. 默认不持久化完整短信内容、联系人号码、定位地址；如果业务必须存储，需要加密和设置保留期限。
12. 调用 SmsForwarder 前建议先调用 `/config/query` 判断能力是否开启。
13. Webhook 接口必须支持幂等，重复事件不应造成重复入库或重复告警。

---

## 23. 总结

本平台最终形态是一个 **Webhook 设备挂载 + SmsForwarder HTTP 查询网关**，数据库承载全部状态：

```text
设备 SmsForwarder
  ↓ Webhook 上报
FastAPI Webhook Receiver
  ↓ 去重 / 入库
设备挂载 / 状态更新 / 事件入库

前端 / 第三方系统
  ↓
FastAPI REST API
  ↓
DeviceCommandService
  ↓
SmsForwarder HTTP Adapter
  ↓
SmsForwarder Server API
```

### 中间件极简

```text
必须：
  React 前端
  FastAPI 后端
  Nginx 统一入口
  PostgreSQL（生产） 或 SQLite（开发）

不需要：
  Redis
  RabbitMQ / Kafka
  Celery
  多个对外端口
```

### 数据库的全能角色

在无 Redis 架构下，数据库承担：

- 设备信息持久化
- Webhook 事件存储
- 设备活跃状态
- Event 去重
- nonce 防重放
- 限流窗口计数
- 指令日志和审计日志

V1 阶段优先落地：

```text
React + FastAPI + Nginx + SQLite/PostgreSQL + Webhook Receiver + SmsForwarder HTTP API Adapter；Docker 对外仅暴露 Nginx 一个端口。
```