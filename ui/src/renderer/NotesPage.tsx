import { useEffect, useState } from "react";

import { createNote, deleteNote, listNotes, updateNote } from "./notes-api";
import type { Note } from "./notes-api";

const dateFormatter = new Intl.DateTimeFormat("zh-CN", {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const noteTimestamp = (value: string): string => dateFormatter.format(new Date(value));

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectNote = (note: Note): void => {
    setSelectedId(note.id);
    setTitle(note.title);
    setContent(note.content);
    setError(null);
  };

  useEffect(() => {
    const controller = new AbortController();
    void listNotes(controller.signal)
      .then((result) => {
        setNotes(result);
        if (result.length > 0) selectNote(result[0]);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "加载笔记失败");
      })
      .finally(() => setIsLoading(false));
    return () => controller.abort();
  }, []);

  const handleCreate = async (): Promise<void> => {
    setIsSaving(true);
    setError(null);
    try {
      const note = await createNote({ title: "未命名笔记", content: "" });
      setNotes((current) => [note, ...current]);
      selectNote(note);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "创建笔记失败");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSave = async (): Promise<void> => {
    if (selectedId === null || !title.trim()) {
      setError("笔记标题不能为空");
      return;
    }
    setIsSaving(true);
    setError(null);
    try {
      const note = await updateNote(selectedId, { title: title.trim(), content });
      setNotes((current) => current.map((item) => item.id === note.id ? note : item));
      setTitle(note.title);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "保存笔记失败");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (): Promise<void> => {
    if (selectedId === null || !window.confirm("确定删除这条笔记吗？")) return;
    setIsSaving(true);
    setError(null);
    try {
      await deleteNote(selectedId);
      const remaining = notes.filter((note) => note.id !== selectedId);
      setNotes(remaining);
      if (remaining.length > 0) {
        selectNote(remaining[0]);
      } else {
        setSelectedId(null);
        setTitle("");
        setContent("");
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "删除笔记失败");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="notes-page">
      <aside className="notes-list-pane">
        <header className="notes-list-header">
          <div>
            <strong>笔记</strong>
            <span>{notes.length} 条</span>
          </div>
          <button type="button" onClick={() => void handleCreate()} disabled={isSaving} title="新建笔记">
            ＋
          </button>
        </header>

        <div className="notes-list">
          {isLoading ? <p className="notes-placeholder">正在加载笔记…</p> : null}
          {!isLoading && notes.length === 0 ? (
            <div className="notes-placeholder">
              <p>还没有笔记</p>
              <button type="button" onClick={() => void handleCreate()}>创建第一条笔记</button>
            </div>
          ) : null}
          {notes.map((note) => (
            <button
              key={note.id}
              className={`note-list-item${selectedId === note.id ? " note-list-item--active" : ""}`}
              type="button"
              onClick={() => selectNote(note)}
            >
              <strong>{note.title}</strong>
              <span>{note.content || "暂无内容"}</span>
              <time>{noteTimestamp(note.updated_at)}</time>
            </button>
          ))}
        </div>
      </aside>

      <section className="note-editor">
        {selectedId === null ? (
          <div className="note-editor-empty">
            <div className="agent-mark">▤</div>
            <h1>记录你的工作</h1>
            <p>创建一条笔记，随时整理想法和待办事项。</p>
            <button type="button" onClick={() => void handleCreate()} disabled={isSaving}>新建笔记</button>
          </div>
        ) : (
          <>
            <header className="note-editor-header">
              <span>{isSaving ? "正在保存…" : "笔记已连接远程 MySQL"}</span>
              <div>
                <button className="note-delete-button" type="button" onClick={() => void handleDelete()} disabled={isSaving}>
                  删除
                </button>
                <button className="note-save-button" type="button" onClick={() => void handleSave()} disabled={isSaving}>
                  保存
                </button>
              </div>
            </header>
            <div className="note-editor-fields">
              <input
                value={title}
                maxLength={255}
                aria-label="笔记标题"
                placeholder="笔记标题"
                onChange={(event) => setTitle(event.target.value)}
              />
              <textarea
                value={content}
                aria-label="笔记内容"
                placeholder="开始记录…"
                onChange={(event) => setContent(event.target.value)}
              />
            </div>
          </>
        )}
        {error ? <div className="note-error" role="alert">{error}</div> : null}
      </section>
    </main>
  );
}
