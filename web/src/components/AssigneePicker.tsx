"use client";

import { useEffect, useRef, useState } from "react";

export type Member = { user_id: string; email: string; role: string };

export function AssigneePicker({
  members,
  value,
  onChange,
  disabled,
  compact,
}: {
  members: Member[];
  value: string | null;
  onChange: (userId: string | null) => void;
  disabled?: boolean;
  /** Compact mode: button trigger + absolute popover (for table cells). */
  compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    document.addEventListener("keydown", keyHandler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("keydown", keyHandler);
    };
  }, [open]);

  const filtered = query.trim()
    ? members.filter((m) => m.email.toLowerCase().includes(query.toLowerCase()))
    : members;

  const selectedEmail = value
    ? members.find((m) => m.user_id === value)?.email ?? `${value.slice(0, 8)}…`
    : null;

  function select(userId: string | null) {
    onChange(userId);
    setOpen(false);
    setQuery("");
  }

  if (compact) {
    return (
      <div ref={ref} style={{ position: "relative" }}>
        <button
          type="button"
          className="btn btn-ghost text-sm"
          disabled={disabled}
          onClick={() => setOpen(!open)}
          style={{
            padding: "0.15rem 0.3rem",
            fontSize: "0.8rem",
            maxWidth: "160px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            textAlign: "left",
          }}
        >
          {selectedEmail ?? "—"}
        </button>
        {open ? (
          <div
            style={{
              position: "absolute",
              top: "100%",
              left: 0,
              zIndex: 40,
              background: "var(--surface-overlay)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              boxShadow: "var(--shadow-md)",
              minWidth: "200px",
              maxHeight: "220px",
              overflowY: "auto",
            }}
          >
            <div style={{ padding: "0.35rem" }}>
              <input
                ref={inputRef}
                className="input text-sm"
                placeholder="Search members…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{ width: "100%", fontSize: "0.8rem", padding: "0.25rem 0.4rem" }}
              />
            </div>
            <button
              type="button"
              className="btn btn-ghost text-sm"
              style={{ display: "block", width: "100%", textAlign: "left", padding: "0.3rem 0.5rem", fontSize: "0.8rem", color: value ? "var(--text)" : "var(--accent)" }}
              onClick={() => select(null)}
            >
              — Unassigned
            </button>
            {filtered.map((m) => (
              <button
                key={m.user_id}
                type="button"
                className="btn btn-ghost text-sm"
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "0.3rem 0.5rem",
                  fontSize: "0.8rem",
                  background: m.user_id === value ? "var(--surface)" : undefined,
                }}
                onClick={() => select(m.user_id)}
              >
                {m.email}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  // Full mode: inline select-like
  return (
    <div ref={ref} style={{ position: "relative" }}>
      {open ? (
        <div
          style={{
            border: "1px solid var(--accent)",
            borderRadius: "var(--radius-sm)",
            background: "var(--surface-overlay)",
            boxShadow: "var(--shadow-md)",
            maxHeight: "240px",
            overflowY: "auto",
          }}
        >
          <div style={{ padding: "0.35rem", borderBottom: "1px solid var(--border)" }}>
            <input
              ref={inputRef}
              className="input text-sm"
              placeholder="Search members…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ width: "100%", fontSize: "0.85rem", padding: "0.3rem 0.5rem" }}
            />
          </div>
          <button
            type="button"
            className="btn btn-ghost text-sm"
            style={{ display: "block", width: "100%", textAlign: "left", padding: "0.35rem 0.6rem", color: value ? "var(--text)" : "var(--accent)", fontWeight: value ? 400 : 600 }}
            onClick={() => select(null)}
          >
            — Unassigned
          </button>
          {filtered.map((m) => (
            <button
              key={m.user_id}
              type="button"
              className="btn btn-ghost text-sm"
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "0.35rem 0.6rem",
                background: m.user_id === value ? "var(--surface)" : undefined,
                fontWeight: m.user_id === value ? 600 : 400,
              }}
              onClick={() => select(m.user_id)}
            >
              {m.email}
            </button>
          ))}
        </div>
      ) : (
        <div
          tabIndex={disabled ? undefined : 0}
          role="button"
          className="input text-sm"
          style={{
            cursor: disabled ? "default" : "pointer",
            display: "flex",
            alignItems: "center",
            minHeight: "2rem",
            padding: "0.3rem 0.5rem",
          }}
          onClick={() => !disabled && setOpen(true)}
          onKeyDown={(e) => { if (!disabled && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); setOpen(true); } }}
        >
          {selectedEmail ?? <span className="muted">—</span>}
        </div>
      )}
    </div>
  );
}
