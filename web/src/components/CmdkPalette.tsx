"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

type SearchResult = {
  id: string;
  label: string;
  subtitle: string;
  href: string;
};

export function CmdkPalette({
  serverSearch,
}: {
  serverSearch?: (q: string) => Promise<SearchResult[]>;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (!open) return;
    requestAnimationFrame(() => inputRef.current?.focus());
  }, [open]);

  function onQueryChange(v: string) {
    setQuery(v);
    if (searchTimer.current) {
      clearTimeout(searchTimer.current);
    }
    if (!v.trim()) {
      setResults([]);
      setSelectedIdx(0);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      const q = v.trim();
      if (serverSearch) {
        const res = await serverSearch(q);
        setResults(res.slice(0, 20));
      }
      setSelectedIdx(0);
    }, 200);
  }

  function navigate(href: string) {
    setOpen(false);
    setQuery("");
    setResults([]);
    if (href.startsWith("http")) {
      window.location.href = href;
    } else {
      router.push(href);
    }
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[selectedIdx]) {
        navigate(results[selectedIdx].href);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  useEffect(() => {
    listRef.current
      ?.querySelector('[data-cmdk-selected="true"]')
      ?.scrollIntoView({ block: "nearest" });
  }, [selectedIdx]);

  if (!open) return null;

  const actions: SearchResult[] = [
    { id: "act-today", label: "Go to Today", subtitle: "My Focus", href: "/today" },
    { id: "act-projects", label: "Go to Projects", subtitle: "All projects", href: "/projects" },
    { id: "act-inbox", label: "Go to Inbox", subtitle: "Quick capture", href: "/inbox" },
    { id: "act-admin", label: "Go to Admin", subtitle: "Admin users", href: "/admin/users" },
  ];

  const combined: SearchResult[] = query.trim()
    ? [
        ...results,
        ...actions.filter((a) =>
          a.label.toLowerCase().includes(query.toLowerCase()) ||
          a.subtitle.toLowerCase().includes(query.toLowerCase())
        ),
      ]
    : actions;

  return (
    <div
      className="cmdk-overlay"
      onClick={() => setOpen(false)}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(0,0,0,0.6)",
        display: "flex",
        justifyContent: "center",
        paddingTop: "14vh",
      }}
    >
      <div
        className="cmdk-panel"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "100%",
          maxWidth: 560,
          maxHeight: "50vh",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          boxShadow: "0 16px 48px rgba(0,0,0,0.4)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <input
          ref={inputRef}
          className="input"
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Search projects / tasks / tickets / commands..."
          style={{
            border: "none",
            borderBottom: "1px solid var(--border)",
            borderRadius: 0,
            padding: "0.85rem 1rem",
            fontSize: "0.95rem",
            background: "transparent",
          }}
        />
        <ul
          ref={listRef}
          style={{
            listStyle: "none",
            margin: 0,
            padding: "0.35rem",
            overflowY: "auto",
            flex: 1,
          }}
        >
          {combined.length === 0 && query.trim() ? (
            <li className="muted text-sm" style={{ padding: "1rem", textAlign: "center" }}>
              No results for &ldquo;{query}&rdquo;
            </li>
          ) : (
            combined.map((r, i) => (
              <li
                key={r.id}
                data-cmdk-selected={i === selectedIdx}
                onMouseEnter={() => setSelectedIdx(i)}
                onClick={() => navigate(r.href)}
                className="cmdk-item"
                style={{
                  padding: "0.55rem 0.75rem",
                  borderRadius: 6,
                  cursor: "pointer",
                  background:
                    i === selectedIdx ? "var(--border)" : "transparent",
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                <span style={{ fontWeight: 500 }}>{r.label}</span>
                <span className="muted text-sm">{r.subtitle}</span>
              </li>
            ))
          )}
        </ul>
        <div
          className="cmdk-footer text-sm muted"
          style={{
            padding: "0.45rem 1rem",
            borderTop: "1px solid var(--border)",
            display: "flex",
            gap: "1rem",
          }}
        >
          <span>↑↓ Navigate</span>
          <span>↩ Open</span>
          <span>Esc Close</span>
        </div>
      </div>
    </div>
  );
}
