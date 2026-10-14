type Role = "user" | "assistant";

interface ChatMessage { role: Role; content: string; }
interface StreamEvent {
  type: "start" | "route" | "retrieval" | "delta" | "done" | "error";
  model?: string;
  content?: string;
  message?: string;
  route?: "general_chat" | "rag_chat";
  confidence?: number;
  count?: number;
}

const API_URL = "http://127.0.0.1:8000/agent/run";
const messages: ChatMessage[] = [];
const messagesElement = document.querySelector<HTMLElement>("#messages");
const emptyState = document.querySelector<HTMLElement>("#empty-state");
const form = document.querySelector<HTMLFormElement>("#composer-form");
const input = document.querySelector<HTMLTextAreaElement>("#composer-input");
const sendButton = document.querySelector<HTMLButtonElement>("#send-button");
const statusLabel = document.querySelector<HTMLElement>("#status-label");
const newChatButton = document.querySelector<HTMLButtonElement>("#new-chat");
const conversationTitle = document.querySelector<HTMLElement>("#conversation-title");

if (!messagesElement || !emptyState || !form || !input || !sendButton || !statusLabel || !newChatButton || !conversationTitle) {
  throw new Error("Chat UI failed to initialize");
}

const scrollToBottom = (): void => { messagesElement.scrollTop = messagesElement.scrollHeight; };

const setStreaming = (streaming: boolean): void => {
  input.disabled = streaming;
  sendButton.disabled = streaming;
  statusLabel.textContent = streaming ? "DeepSeek 正在思考…" : "DeepSeek v4.1 · Streamable HTTP";
  statusLabel.dataset.active = String(streaming);
};

const createMessageElement = (role: Role, content: string): HTMLElement => {
  const article = document.createElement("article");
  article.className = `message message--${role}`;
  const avatar = document.createElement("div");
  avatar.className = "message__avatar";
  avatar.textContent = role === "user" ? "你" : "✦";
  const body = document.createElement("div");
  body.className = "message__body";
  body.textContent = content;
  article.append(avatar, body);
  messagesElement.append(article);
  scrollToBottom();
  return body;
};

const consumeLine = (line: string, assistantBody: HTMLElement): void => {
  if (!line.trim()) return;
  const event = JSON.parse(line) as StreamEvent;
  if (event.type === "delta" && event.content) {
    statusLabel.textContent = "DeepSeek 正在回答…";
    assistantBody.textContent += event.content;
    scrollToBottom();
  }
  if (event.type === "route") {
    statusLabel.textContent = event.route === "rag_chat"
      ? "Jev 已选择知识库问答，正在召回…"
      : "Jev 已选择普通聊天，正在生成…";
  }
  if (event.type === "retrieval") {
    statusLabel.textContent = `百炼已召回 ${event.count ?? 0} 条知识，正在生成…`;
  }
  if (event.type === "error") throw new Error(event.message ?? "模型请求失败");
};

const streamReply = async (): Promise<void> => {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, temperature: 0.6 }),
  });
  if (!response.ok) throw new Error(`服务端返回 ${response.status}: ${await response.text()}`);
  if (!response.body) throw new Error("浏览器未提供流式响应体");

  const assistant: ChatMessage = { role: "assistant", content: "" };
  messages.push(assistant);
  const assistantBody = createMessageElement("assistant", "");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) consumeLine(line, assistantBody);
      if (done) break;
    }
    if (buffer) consumeLine(buffer, assistantBody);
    assistant.content = assistantBody.textContent ?? "";
  } catch (error) {
    assistant.content = assistantBody.textContent ?? "";
    if (!assistant.content) {
      messages.pop();
      assistantBody.closest("article")?.remove();
    }
    throw error;
  }
};

const submitMessage = async (): Promise<void> => {
  const content = input.value.trim();
  if (!content) return;
  emptyState.hidden = true;
  if (messages.length === 0) conversationTitle.textContent = content.slice(0, 28);
  messages.push({ role: "user", content });
  createMessageElement("user", content);
  input.value = "";
  input.style.height = "auto";
  setStreaming(true);
  try {
    await streamReply();
  } catch (error) {
    const message = error instanceof Error ? error.message : "未知错误";
    createMessageElement("assistant", `连接失败：${message}`);
  } finally {
    setStreaming(false);
    input.focus();
  }
};

form.addEventListener("submit", (event) => { event.preventDefault(); void submitMessage(); });
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
});
newChatButton.addEventListener("click", () => {
  messages.length = 0;
  messagesElement.replaceChildren();
  emptyState.hidden = false;
  conversationTitle.textContent = "新对话";
  input.value = "";
  input.focus();
});
document.querySelectorAll<HTMLButtonElement>("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt ?? "";
    input.focus();
  });
});
input.focus();
