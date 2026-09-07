**文档概览**  
下面是对 **Vexa** 开源项目所有**向外分发的 API 能力**的中文整理。文档按模块（Agent、Meeting、Bot、Transcript、Recording、WebSocket、MCP 等）分类，列出每个模块的对外接口、请求方式、基本参数说明以及典型使用场景。所有接口均在网关 (`gateway‑rest` / `gateway‑ws`) 后方，通过 `X‑API‑Key`（ hosted）或 `X‑User‑Id`（ self‑hosted）进行身份认证。

---

## 1. 认证与基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `https://api.cloud.vexa.ai`（云端）或 `http://localhost:18056`（自建） |
| **统一 Header** | `X‑API‑Key: <your‑key>`（云端）<br>`X‑User‑Id: <user‑id>`（自建） |
| **速率限制** | 由 gateway 策略控制，默认每分钟若干请求（见 docs/rate‑limit） |
| **错误格式** | `{ "detail": "..." , "code": 400/401/403/422/502 … }` |

> **注意**：所有的身份信息都由 gateway 从 API Key / User‑Id 衍生，请求体/查参中的 `subject` 一律被忽略（安全策略 P20）。

---

## 2. Agent API（控制平面）

| 接口 | 方法 | 路径 | 说明 | 典型参数 |
|------|------|------|------|----------|
| **健康检查** | `GET` | `/health` | 返回 `{"status":"ok","service":"agent-api",...}` | - |
| **获取模型列表** | `GET` | `/api/models` | 返回当前主体可用的模型配置 | - |
| **派发 Unit** | `POST` | `/invocations` | 根据 `unit.v1`  envelope 分派任务到 runtime | `identity.subject`, `runner`, `workspaces`, `trigger`, `start` |
| **聊天（SSE）** | `POST` | `/api/chat` | 返回 `text/event-stream`，每一帧为 `message‑delta`、`tool‑call`、`tool‑result` 等 | `prompt`, `session?`, `active?`（subject 由 server 完成） |
| **聊天控制** | `POST` / `GET` | `/api/chat/reset` / `/api/sessions` / `/api/sessions/{id}/history` | 会话重置、列出会话、获取历史记录 | `{session?}` |
| **常规** | `POST` / `GET` / `PATCH` / `DELETE` | `/api/routines` | 定义/查询/启用/删除定时任务 | `name`, `cron`, `prompt`, `run_now` |
| **事件入口** | `POST` | `/events` | 接收 `event.v1` 事件，转换为 unit 进行分派 | `name`, `subject`, `source`, `plan` |
| **实时会议协同** | `POST` / `GET` | `/api/meeting/start` / `/api/meeting/process` / `/api/meeting/relay-health` / `/api/meeting/stream` | 发起/暂停会议转译、健康检查、SSE 实时 transcript + card 流 | `native_id`, `platform`, `on`（开关） |
| **工作空间** | `GET` / `POST` / `PUT` / `DELETE` | `/api/workspace/tree`, `/api/workspace/file`, `/api/workspace/git`, `/api/workspace/upload`, `/api/workspace/init`, `/api/workspace/attached`, `/api/workspace/swap` | 查看/上传/初始化/交换 git 工作空间 | 路径、分支、token 等 |
| **模型调度** | `POST` / `GET` | `/api/routines`, `/api/routines/{name}/enabled` | 管理例行任务 | `cron`, `prompt` |

> **适用场景**：在自己的工作空间里派发 Claude‑code、生成任务、流式返回聊天回复、管理定时 Routine、对接外部事件（如邮件到任务）。

---

## 3. Meetings API（会议捕获与管理）

| 接口 | 方法 | 路径 | 说明 | 典型参数 |
|------|------|------|------|----------|
| **计划/导入会议** | `PUT` | `/user/calendar` | 绑定日历（ICS URL），开启自动加入 | `ics_url`, `auto_join`, `bot_name` |
| **发起 Bot** | `POST` | `/bots` | 在指定平台加入会议 | `platform` (`google_meet`/`zoom`/`teams`/`jitsi`), `native_meeting_id`, `bot_name`, `passcode?` |
| **获取会议列表** | `GET` | `/meetings`（支持 pagination `limit/offset`） | 查询已记录的会议 | `limit`, `offset` |
| **会议详情** | `GET` | `/meetings/{platform}/{native_meeting_id}` | 返回会议记录（状态、开始时间、参与者等） | - |
| **参与者** | `GET` | `/meetings/{platform}/{native_meeting_id}/participants` | 返回参与者列表（姓名、邮件、响应状态） | - |
| **转录状态** | `GET` | `/transcripts/{platform}/{native_meeting_id}` | 实时或已完成的转录文本流 | - |
| **录像** | `GET` / `POST` / `DELETE` | `/recordings`, `/recordings/{id}`, `/recordings/{id}` | 查询、下载、删除录制文件 | `limit`, `offset`；支持 Range 秒级 seeking |
| **网hook** | `POST` / `GET` | `/webhooks` / `/webhooks/{id}` | 创建/列出已签名的 meeting.completed / bot.failed 回调 | `url`, `secret`（会议数据内部） |
| **日历连接** | `GET` / `PUT` / `DELETE` | `/user/calendars/{id}` | 单独的 calendar 连接 CRUD（Google Calendar、Outlook） | `ics_url`, `auto_join` |

> **适用场景**：自动将会议 Bot  Joining 到 Google Meet/Zoom/Teams，实时获取转录文本、参与者信息、事后录像回放，以及日历同步与会议计划。

---

## 4. Bot 控制 API（机器人运行时命令）

| 接口 | 方法 | 路径 | 说明 | 典型参数 |
|------|------|------|------|----------|
| **发送聊天指令** | `POST` | `/bots/{platform}/{native_meeting_id}/chat` | 让机器人在会议中发言/发送消息 | `text`, `speaker`（可选） |
| **静音/解除静音** | `POST` | `/bots/{platform}/{native_meeting_id}/mute` | 切换 mic 状态 | `mute: true/false` |
| **共享屏幕** | `POST` | `/bots/{platform}/{native_meeting_id}/share` | 开始/停止屏幕共享 | `screen_id`（可选） |
| **结束会议** | `POST` | `/bots/{platform}/{native_meeting_id}/leave` | 让机器人离开会议 | - |

> **适用场景**：会议中实时控制机器人行为（发言、静音、屏幕共享），多用于交互式机器人 demo。

---

## 5. Transcript / 实时流 API（SSE / WebSocket）

| 接口 | 方法 | 路径 | 说明 | 说明 |
|------|------|------|------|------|
| **SSE  transcript 流** | `GET` | `/api/meeting/stream?meeting_id=&session_uid=` | 返回 `id:` 标记的事件流，类型包括 `transcript`、`card`、`message‑delta`、`tool‑call`、`ping`、`meeting‑end`。可通过 `Last-Event-ID` 实现断点续传。 | 必须携带 `meeting_id` 与 `session_uid`（或 `native_id`） |
| **WebSocket gateway** | `WS` | `ws://localhost:18056/ws.v1` / `wss://api.cloud.vexa.ai/ws.v1` | 网关层的 WebSocket，用于会议原始音频流、实时事件广播。订阅 `tc‑stream`、`out‑stream` 等 data‑asset。 | 连接后发送 `{"type":"subscribe","asset":"tc-stream"}` 等 |
| **MCP（Model‑Control‑Protocol）** | `HTTP` | `GET/POST /mcp`（FastAPI mount） |  expose tools & prompts 供外部调用，无需认证（或使用 API key）。适合快速原型开发。 | `{"tool":"search","args":{...}}` |

> **适用场景**：需要**实时** transcript 与 agent 输出的应用（如 live 字幕、交互式 AI 助手），以及想要直接订阅内部 pub/sub 流的运维或集成方。

---

## 6. Recordings API（录像与媒体文件）

| 接口 | 方法 | 路径 | 说明 | 典型参数 |
|------|------|------|------|----------|
| **列出录像** | `GET` | `/recordings` | 支持 `limit`/`offset` 分页 | `limit`, `offset` |
| **单录像详情** | `GET` | `/recordings/{recording_id}` | 返回元数据（时长、状态、关联的 transcript id） | - |
| **下载媒体分片** | `GET` | `/recordings/{recording_id}/media/{media_file_id}/raw` | 支持 HTTP `Range` 头实现分片下载（206） | `Range: bytes=0-1023` |
| **删除录像** | `DELETE` | `/recordings/{recording_id}` | 标记删除，实际清理由后台异步进行 | - |

> **适用场景**：会后导出高质量音频/视频、配合第三方编辑工具或存档。

---

## 7. Webhook / 事件分发

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **创建 webhook** | `POST` | `/webhooks` | 提供目标 URL，Vexa 会对 `meeting.completed` 与 `bot.failed` 事件发送已 HMAC‑SHA256 签名的 POST 请求。 |
| **列出/webhook** | `GET` | `/webhooks` | 返回已配置的 webhook 列表（含启用状态、签名密钥）。 |
| **删除 webhook** | `DELETE` | `/webhooks/{id}` | 禁用并移除该 webhook。 |

> **安全点**：签名放在 `X‑Vexa‑Signature` header， payload 包含 `event.type`、`meeting.id` 与 `timestamp`，建议在服务端验签后再处理业务。

---

## 8. 其它辅助接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **Settings（录像默认、webhook 配置）** | `GET` / `PUT` | `/settings` | 修改账号级默认录像时长、自动录制开关、webhook URL 等。 |
| **用户管理（仅 admin）** | `GET` / `POST` / `DELETE` | `/admin/users` / `/admin/users/{id}` | 创建/查询/冻结用户账号，分配 `scopes` 与 `max_concurrent_bots`。 |
| **身份 token** | `POST` | `/admin/api-tokens` | 生成带 scoped `X‑API‑Key` 的一次性或长期 token。 |

> **适用场景**：组织层面的权限管理、自动化运维（如定时清理旧录像、批量生成调测 token）。

---

## 9. 使用流程示例（中文）

### 场景 A：自动化会议捕获 & 实时转译

1. **绑定日历**  
   ```bash
   curl -X PUT "http://localhost:18056/user/calendar" \
        -H "X-API-Key: $KEY" \
        -H "Content-Type: application/json" \
        -d '{"ics_url":"https://cal.google.com/…basic.ics","auto_join":true}'
   ```

2. **发起会议 Bot**  
   ```bash
   curl -X POST "http://localhost:18056/bots" \
        -H "X-API-Key: $KEY" \
        -H "Content-Type: application/json" \
        -d '{"platform":"zoom","native_meeting_id":"MTg5NDk5OTk5OA","bot_name":"vexa‑bot"}'
   ```

3. **订阅实时 transcript（SSE）**  
   ```bash
   curl -N "http://localhost:18056/api/meeting/stream?meeting_id=12345&session_uid=abcdef" \
        -H "X-API-Key: $KEY" \
        | while read line; do echo "$line"; done
   ```

4. **事后下载录像**  
   ```bash
   # 获取录像列表
   curl "http://localhost:18056/recordings?limit=5" -H "X-API-Key: $KEY"
   # 下载单个分片（假设 recording_id=rd1, media_file_id=mf1，前 1KB）
   curl -r 0-1023 "http://localhost:18056/recordings/rd1/media/mf1/raw" -O
   ```

### 场景 B：在会议中让机器人发言

```bash
curl -X POST "http://localhost:18056/bots/zoom/MTg5NDk5OTk5OA/chat" \
     -H "X-API-Key: $KEY" \
     -H "Content-Type: application/json" \
     -d '{"text":"大家好，我是 Vexa 机器人，正在记录本场会议。"}'
```

### 场景 C：通过 MCP 快速试用工具

```bash
curl -X POST "http://localhost:18056/mcp" \
     -H "Content-Type: application/json" \
     -d '{"tool":"search","args":{"query":"2024 AI 会议趋势"}}'
```

---

## 10. 目录与版本说明

| 文件 | 作用 |
|------|------|
| `API_INTERFACES.md`（项目根目录） | 本文档的源数据（已在 repo 中生成，涵盖 `architecture.calm.json`、`contracts.seal.json` 所有接口） |
| `contracts.seal.json` | 已发布的合约 hash，CI 会检查 gateway + meeting‑api 是否仍然提供对应的 `*.v1` 接口 |
| `architecture.calm.json` | 完整的模块/系统模型，决定了哪些节点是 single‑writer、哪些是 read‑only，用于 gate:dataflow 校验 |

> **版本**：以上文档对应 **Vexa 0.12**（官方文档注明 “These docs cover Vexa 0.12”）。若使用 hosted 云端 `api.cloud.vexa.ai`，则同一套接口可直接使用；自建请确保 `make all` 后的 gateway 服务已启动。

---

## 11. 小结

- **两大核心 API**：  
  1. **Agent API**——面向知识工作区的控制平面（调度、聊天、Routine、Workspace）。  
  2. **Meetings API**——面向会议捕获、转录、参与者、录像的完整生命周期。

- **全部接口均在 gateway 后方**，统一使用 `X‑API‑Key`（云端）或 `X‑User‑Id`（自建）进行身份校验。  
- **实时流** 以 SSE 或 WebSocket 形式提供，保证低延迟的 transcript 与 agent 输出。  
- **合约 (`*.v1`)** 与 `contracts.seal.json` 保证了向外接口的**不随意变更**，CI 会在每次提交时检查接口是否仍然可用，缺失或重命名的接口必须在 `KNOWN_GAPS.json` 中登记。

> 若需要进一步的 **OpenAPI/Swagger** 定义或 **代码示例**（如 Python、curl、Node），请告诉我，我可以进一步导出对应的 JSON/YAML 文件。