import type { AgentMessage, StreamEvent } from "./types";

const API_URL = "http://127.0.0.1:8000/agent/run";

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

export const streamAgentReply = async (
  messages: AgentMessage[],
  handlers: StreamHandlers,
  signal: AbortSignal,
): Promise<void> => {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, temperature: 0.6 }),
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
