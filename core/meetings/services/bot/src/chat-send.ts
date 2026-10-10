/**
 * Chat send adapter — the meeting-chat half of the acts.v1 `chat_send` path.
 *
 * 【入会问候需求】meeting-api 在 bot FSM 前进到 active(入会成功)的瞬间,把会前配置的
 * 问候语(greeting,bot_spawn 请求字段,持久化于 meeting.data)以 acts.v1 `chat_send`
 * 形态发布到 `bot_commands:meeting:{id}` 命令总线;本控制器是其 bot 端落点:在会议 UI
 * 的 chat 输入框写入文本并提交。与 SpeakController 同一驱动模式 —— page.evaluate 直接
 * 驱动会议 DOM(防御性选择器,失败仅记日志,绝不影响会议进程),由 index.ts 的 teeActs
 * 与 voice 并联(单一订阅,orchestrator 仍独占 `leave`)。
 *
 * 平台:Teams 会议聊天优先(`data-tid="textbox"` + 发送按钮 `data-tid="sendMessage"`),
 * 按 aria-label/placeholder 兜底;其他平台沿用通用可编辑区探测。
 *
 * Node-only page-driving glue — 无 DOM 的 CI 不可单测,正确性由真实会议 live leg 证明。
 */
import type { Page } from '@vexa/remote-browser';
import type { Invocation } from './config.js';

/** 会议 chat 发送控制器(acts.v1 `chat_send` 的 bot 端执行体)。 */
export interface ChatController {
  /** 在会议 chat 输入框发送 `text`。best-effort:失败记日志并正常返回,不向外抛。 */
  send(text: string): Promise<void>;
}

export function createChatController(page: Page, inv: Invocation): ChatController {
  const platform = inv.platform;
  return {
    async send(text: string): Promise<void> {
      const body = (text ?? '').trim();
      if (!body) return;                                   // 空文案直接跳过(不发空消息)
      console.log(`[bot] chat_send: "${body.slice(0, 60)}"`);
      // Runs IN THE BROWSER; reach the DOM via globalThis (no DOM types in this Node-typed file).
      const outcome = await page
        .evaluate(async ({ body, platform }) => {
          const w = globalThis as any;
          const doc = w.document;
          // 输入框:Teams 会议聊天 data-tid=textbox,其次 messagebox / 通用可编辑区兜底;
          // 按 aria-label/placeholder 排除搜索框等非聊天输入。
          const selectors =
            platform === 'teams'
              ? ['[data-tid="textbox"]', '[data-tid="messagebox"]', 'div[role="textbox"][contenteditable="true"]', 'textarea']
              : ['div[role="textbox"][contenteditable="true"]', 'textarea', '[data-tid="textbox"]'];
          const findInput = (): any => {
            for (const sel of selectors) {
              const candidates = Array.from(doc?.querySelectorAll(sel) ?? []) as any[];
              const input =
                candidates.find((el) => {
                  const label = `${el.getAttribute?.('aria-label') ?? ''} ${el.getAttribute?.('placeholder') ?? ''}`;
                  return !/search|filter/i.test(label);
                }) ?? null;
              if (input) return input;
            }
            return null;
          };
          let input = findInput();
          // 【入会问候需求】Teams 默认可能收起会议聊天。找不到输入框时先展开 Chat
          // 面板并等待其异步挂载，再重试一次；失败仍按 best-effort 返回，不阻断入会。
          if (!input && platform === 'teams') {
            const chatButton = (Array.from(doc?.querySelectorAll('button') ?? []) as any[]).find((button) => {
              const tid = button.getAttribute?.('data-tid') ?? '';
              const label = `${button.getAttribute?.('aria-label') ?? ''} ${button.getAttribute?.('title') ?? ''}`;
              return /chat/i.test(tid) || /(^|\s)(open\s+)?chat(\s|$)/i.test(label);
            });
            if (chatButton) {
              chatButton.click();
              await new Promise((resolve) => w.setTimeout(resolve, 500));
              input = findInput();
            }
          }
          if (!input) return 'no-chat-input';
          input.focus?.();
          // 写入文本:优先 execCommand insertText(会触发框架监听到的 input 事件),
          // 未生效(返回值/内容不变)再直接赋值并手动派发 input 事件。
          const before = input.textContent ?? '';
          doc?.execCommand?.('insertText', false, body);
          if ((input.textContent ?? '') === before) {
            if (input.tagName === 'TEXTAREA' || input.tagName === 'INPUT') input.value = body;
            else input.textContent = body;
            input.dispatchEvent?.(new w.InputEvent('input', { bubbles: true }));
          }
          // 提交:优先显式发送按钮(Teams data-tid=sendMessage / aria-label=Send),
          // 其次在输入框上派发 Enter 键事件。
          const sendBtn = (Array.from(doc?.querySelectorAll('button') ?? []) as any[]).find(
            (b) =>
              /sendMessage/i.test(b.getAttribute?.('data-tid') ?? '') ||
              /^(send)$/i.test(b.getAttribute?.('aria-label') ?? '')
          );
          if (sendBtn) {
            sendBtn.click();
            return 'sent-button';
          }
          input.dispatchEvent?.(
            new w.KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
          );
          return 'sent-enter';
        }, { body, platform })
        .catch((e) => {
          console.error(`[bot] chat_send failed: ${String(e)}`);
          return 'evaluate-error';
        });
      console.log(`[bot] chat_send: outcome=${String(outcome)}`);
    },
  };
}
