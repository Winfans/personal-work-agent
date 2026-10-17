import type { AgentMessage, StreamEvent } from "./types";

const API_URL = "http://127.0.0.1:8000/agent/run";
const CONVERSATIONS_URL = "http://127.0.0.1:8000/api/v1/conversations";

interface StreamHandlers {
  onEvent: (event: StreamEvent) => void;
}

const consumeLine = (line: string, handlers: StreamHandlers): void => {
  if (!line.trim()) return;
  const event = JSON.parse(line) as StreamEvent;
  if (event.type === "error") {
    throw new Error(event.message ?? "模型请求失败");
  }
  handlers.onEvent(event);
};

const streamRequest = async (
  url: string,
  body: object,
  handlers: StreamHandlers,
  signal: AbortSignal,
): Promise<void> => {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { message?: string } | null;
    throw new Error(body?.message ?? `服务端返回 ${response.status}`);
  }
  if (!response.body) throw new Error("浏览器未提供流式响应体");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) consumeLine(line, handlers);
    if (done) break;
  }

  if (buffer) consumeLine(buffer, handlers);
};

export const streamAgentReply = (
  messages: AgentMessage[], handlers: StreamHandlers, signal: AbortSignal,
): Promise<void> => streamRequest(API_URL, { messages, temperature: 0.6 }, handlers, signal);

export const streamConversationReply = (
  conversationId: number, message: string, handlers: StreamHandlers, signal: AbortSignal,
): Promise<void> => streamRequest(
  `${CONVERSATIONS_URL}/${conversationId}/run`,
  { message, temperature: 0.6 },
  handlers,
  signal,
);
