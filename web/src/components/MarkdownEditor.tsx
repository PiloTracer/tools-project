"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Suggestion = { label: string; insert: string };

export function MarkdownEditor({
  value,
  onChange,
  rows = 4,
  placeholder = "",
  mentionSuggestions,
  refSuggestions,
  onPasteFiles,
  onDropFiles,
}: {
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  placeholder?: string;
  mentionSuggestions?: (prefix: string) => Promise<Suggestion[]>;
  refSuggestions?: (prefix: string) => Promise<Suggestion[]>;
  onPasteFiles?: (files: File[]) => void;
  onDropFiles?: (files: File[]) => void;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [suggestIdx, setSuggestIdx] = useState(0);

  const fetchSuggestions = useCallback(async () => {
    const el = textareaRef.current;
    if (!el) return;
    const pos = el.selectionStart;
    const text = value.slice(0, pos);
    const m = text.match(/(?:^|\s)([@#])([\w.-]*)$/);
    if (!m || !m[2]) {
      setSuggestions([]);
      return;
    }
    const type = m[1] as "@" | "#";
    const prefix = m[2];
    if (type === "@" && mentionSuggestions) {
      const res = await mentionSuggestions(prefix);
      setSuggestions(res.slice(0, 10));
      setSuggestIdx(0);
    } else if (type === "#" && refSuggestions) {
      const res = await refSuggestions(prefix);
      setSuggestions(res.slice(0, 10));
      setSuggestIdx(0);
    } else {
      setSuggestions([]);
    }
  }, [value, mentionSuggestions, refSuggestions]);

  useEffect(() => {
    const timer = setTimeout(() => fetchSuggestions(), 150);
    return () => clearTimeout(timer);
  }, [fetchSuggestions]);

  function applySuggestion(s: Suggestion) {
    const el = textareaRef.current;
    if (!el) return;
    const pos = el.selectionStart;
    const text = value.slice(0, pos);
    const m = text.match(/(?:^|\s)([@#])([\w.-]*)$/);
    if (!m) return;
    const type = m[1];
    const start = pos - m[0].length;
    const before = value.slice(0, start);
    const after = value.slice(pos);
    const replacement = `${type}${s.insert} `;
    onChange(before + replacement + after);
    setSuggestions([]);
    setTimeout(() => {
      const el2 = textareaRef.current;
      if (el2) {
        const newPos = before.length + replacement.length;
        el2.focus();
        el2.setSelectionRange(newPos, newPos);
      }
    }, 0);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (suggestions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSuggestIdx((i) => Math.min(i + 1, suggestions.length - 1));
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSuggestIdx((i) => Math.max(i - 1, 0));
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        applySuggestion(suggestions[suggestIdx]);
        return;
      }
      if (e.key === "Escape") {
        setSuggestions([]);
        return;
      }
    }
  }

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    function onDragOver(e: DragEvent) {
      e.preventDefault();
      if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
    }
    function onDrop(e: DragEvent) {
      e.preventDefault();
      if (!onDropFiles) return;
      const files = Array.from(e.dataTransfer?.files ?? []);
      if (files.length) onDropFiles(files);
    }
    el.addEventListener("dragover", onDragOver);
    el.addEventListener("drop", onDrop);
    return () => {
      el.removeEventListener("dragover", onDragOver);
      el.removeEventListener("drop", onDrop);
    };
  }, [textareaRef, onDropFiles]);

  return (
    <div className="md-editor" style={{ position: "relative" }}>
      <textarea
        ref={textareaRef}
        className="input"
        rows={rows}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        onPaste={(e) => {
          if (!onPasteFiles) return;
          const items = e.clipboardData?.items;
          if (!items) return;
          const files: File[] = [];
          for (let i = 0; i < items.length; i++) {
            const f = items[i].getAsFile();
            if (f) files.push(f);
          }
          if (files.length) {
            e.preventDefault();
            onPasteFiles(files);
          }
        }}
        placeholder={placeholder}
        style={{ width: "100%" }}
      />
      {suggestions.length > 0 && (
        <ul
          className="md-editor-suggest"
          style={{
            position: "absolute",
            bottom: "100%",
            left: 0,
            right: 0,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            listStyle: "none",
            margin: 0,
            padding: "0.25rem",
            maxHeight: 200,
            overflowY: "auto",
            zIndex: 10,
            boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
          }}
        >
          {suggestions.map((s, i) => (
            <li
              key={i}
              onMouseDown={(e) => {
                e.preventDefault();
                applySuggestion(s);
              }}
              className="text-sm"
              style={{
                padding: "0.35rem 0.55rem",
                borderRadius: 4,
                cursor: "pointer",
                background: i === suggestIdx ? "var(--border)" : "transparent",
              }}
            >
              {s.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
