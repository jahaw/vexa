# Vexa 对外API接口说明
本文档整理了 Vexa 所有面向外部开放的 API 与发布的数据契约规范，信息来源：`architecture.calm.json`、`contracts.seal.json` 以及对应的源码目录。

## 1. 服务级接口（HTTP / WebSocket / RPC）
| 接口名称 | 类型 | 源码路径 | 功能说明 |
|--------|------|----------|--------|
| **agent-api-rest** | API | `core/agent/services/agent-api` | 代理管控平面；向运行时分发任务，提供会议助手接口 |
| **gateway-rest** | API | `core/gateway/services/gateway` | 边缘网关API：权限鉴权（作用域校验）、REST路由分发、WebSocket消息广播 |
| **gateway-ws** | WebSocket | `core/gateway/services/gateway` | WebSocket长连接，用于网关推送实时会话流数据 |
| **admin-api-rest** | API | `core/identity/services/admin-api` | 身份服务：令牌签发/校验、用户管理、用户日历绑定配置 |
| **stt-endpoint** | API | `core/meetings/services/transcription` | 语音转文字接口（内置模型使用 faster‑whisper / CTranslate2，同时兼容 OpenAI 格式 `/v1/audio/transcriptions`） |
| **desktop-rest** | API | `core/meetings/services/desktop` | 一体化本地开发服务进程，集成机器人、音频采集器、网关能力 |
| **desktop-ingest-ws** | WebSocket | `core/meetings/services/desktop` | WebSocket通道，向本地服务推送实时音频流 |
| **meeting-api-rest** | API | `core/meetings/services/meeting-api` | 会议核心服务：音频采集、机器人启动管理、录制文件、会话管理、日历导入与自动入会 |
| **service-authority-rest** | API | `core/meetings/contracts/service-authority.v1` | 可选第三方准入决策接口（不属于开源核心组件，由部署方自行实现） |
| **system-webhook-rest** | API | `core/meetings/contracts/webhook.v1` | 可选签名回调接口，接收 `meeting.completed` 会议结束、`bot.failed` 机器人异常事件 |
| **mcp-http** | API（FastAPI） | `core/meetings/services/mcp` | 无状态 FastAPI 服务，挂载路径 `/mcp`，通过HTTP暴露工具集与提示词能力 |
| **runtime-rest** | API | `core/runtime/src` | 运行时内核接口：`POST /workloads` 创建工作负载（支持容器Docker/K8s/本地进程三种模式） |

## 2. 版本化数据契约规范
| 契约名称 | 源码路径 | 业务域 |
|--------|----------|--------|
| **api.v1** | `core/gateway/contracts/api.v1` | 网关对外公共数据契约 |
| **ws.v1** | `core/gateway/contracts/ws.v1` | 网关WebSocket消息结构契约 |
| **identity.v1** | `core/identity/contracts/identity.v1` | 身份数据契约（用户、访问令牌） |
| **acts.v1** | `core/meetings/contracts/acts.v1` | 会议动作契约（退出会议、发言指令等） |
| **captured‑signal.v1** | `core/meetings/contracts/captured‑signal.v1` | 采集音频信号数据契约 |
| **flagged‑issue.v1** | `core/meetings/contracts/flagged‑issue.v1` | 异常标记信息契约 |
| **invocation.v1** | `core/meetings/contracts/invocation.v1` | 工具调用执行契约 |
| **lifecycle.v1** | `core/meetings/contracts/lifecycle.v1` | 机器人生命周期状态流转与时间戳契约 |
| **service‑authority.v1** | `core/meetings/contracts/service‑authority.v1` | 第三方准入校验契约（可选启用） |
| **transcript.v1** | `core/meetings/contracts/transcript.v1` | 原始转写文本数据契约 |
| **webhook.v1** | `core/meetings/contracts/webhook.v1` | 终态事件回调消息投递契约 |
| **runtime.v1** | `core/runtime/contracts/runtime.v1` | 运行时工作负载模型契约 |
| **schedule.v1** | `core/runtime/contracts/schedule.v1` | 工作负载调度规则契约 |
| **execution‑targets.v1** | `deploy/contracts/execution‑targets.v1` | 部署执行目标环境契约 |
| **config.v1** | `deploy/contracts/config.v1` | 单服务部署配置契约 |

## 3. 客户端SDK（对外发布类库）
| SDK名称 | 源码目录 | 补充说明 |
|--------|----------|--------|
| **vexa‑client** | `sdks/` | 公开客户端库，遵循架构规范 P1–P12 |
| **vexa‑cli** | `sdks/` | 命令行工具，与客户端SDK对外能力保持一致 |
| **transcript‑rendering** | `sdks/` | 会议转写文本渲染工具集 |

> 约束规范：由 `docs/docs/governance/architecture.mdx`（P1‑P12）管控。SDK 的对外能力以入口文件/契约定义为准，依赖关系必须遵守依赖管控规则。

---

**重要说明**
上表所有接口均为架构模型定义的**唯一写入源**或**只读访问入口**。调用方必须严格使用已发布的版本化契约（`*.v1`）进行对接，禁止自行逆向解析生产者原始数据（规范 P23：单写源管控原则）。

如果你需要，我可以输出 Markdown 纯中文版、或者整理成 OpenAPI 风格接口摘要、导出为 Excel 表格。