"use client";

import { useEffect, useRef, useState } from "react";

type AttachmentMeta = {
  id: string;
  filename: string;
  mime: string;
  size_bytes: number;
};

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Renders persisted attachments from meta_json.attachment_ids.
 *
 * Images are shown as bounded thumbnails; PDFs, office documents, and text
 * files are shown as download links (the composer accepts all of them, so they
 * must not be rendered as broken <img> elements). URLs are same-origin BFF
 * routes, so the session cookie authenticates them.
 */
export function AttachmentImages({
  ids,
  maxWidth = 720,
}: {
  ids: string[];
  maxWidth?: number;
}) {
  const idsKey = ids.join(",");
  const [metas, setMetas] = useState<Record<string, AttachmentMeta | null>>({});
  const loadedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const currentIds = idsKey ? idsKey.split(",") : [];
    const missing = currentIds.filter((id) => !loadedRef.current.has(id));
    if (!missing.length) return;
    let cancelled = false;

    // The API accepts at most 50 ids per request; meta_json can carry more.
    const batches: string[][] = [];
    for (let index = 0; index < missing.length; index += 50) {
      batches.push(missing.slice(index, index + 50));
    }

    Promise.all(
      batches.map(async (batch) => {
        try {
          const response = await fetch(
            `/api/attachments?ids=${encodeURIComponent(batch.join(","))}`,
          );
          if (!response.ok) return [] as AttachmentMeta[];
          return (await response.json()) as AttachmentMeta[];
        } catch {
          return [] as AttachmentMeta[];
        }
      }),
    )
      .then((results) => {
        if (cancelled) return;
        const rows = results.flat();
        const found = new Map(rows.map((row) => [row.id, row]));
        setMetas((prev) => {
          const next = { ...prev };
          for (const id of missing) {
            next[id] = found.get(id) ?? null;
            loadedRef.current.add(id);
          }
          return next;
        });
      })
      .catch(() => {
        if (cancelled) return;
        setMetas((prev) => {
          const next = { ...prev };
          for (const id of missing) {
            next[id] = null;
            loadedRef.current.add(id);
          }
          return next;
        });
      });

    return () => {
      cancelled = true;
    };
  }, [idsKey]);

  if (!ids.length) return null;

  return (
    <div className="stack" style={{ gap: "0.5rem" }}>
      {ids.map((id) => {
        const meta = metas[id];
        if (meta === undefined) {
          return (
            <a
              key={id}
              href={`/api/attachments/${id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="muted text-sm"
              style={{ textDecoration: "none" }}
            >
              Loading attachment…
            </a>
          );
        }
        const isImage = meta === null ? true : meta.mime.startsWith("image/");
        if (isImage) {
          return (
            <a key={id} href={`/api/attachments/${id}`} target="_blank" rel="noopener noreferrer">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/api/attachments/${id}`}
                alt={meta?.filename ?? ""}
                loading="lazy"
                style={{
                  maxWidth: `min(100%, ${maxWidth}px)`,
                  height: "auto",
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                  cursor: "zoom-in",
                  display: "block",
                }}
              />
            </a>
          );
        }
        return (
          <a
            key={id}
            href={`/api/attachments/${id}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.5rem 0.75rem",
              border: "1px solid var(--border)",
              borderRadius: 8,
              textDecoration: "none",
              color: "var(--text)",
              maxWidth: "100%",
            }}
          >
            <span aria-hidden style={{ fontSize: "1.1rem" }}>📄</span>
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              <span style={{ fontWeight: 600 }}>{meta?.filename ?? "Attachment"}</span>
              {meta ? <span className="muted text-sm"> · {formatBytes(meta.size_bytes)}</span> : null}
            </span>
          </a>
        );
      })}
    </div>
  );
}

/** Extract attachment ids from an activity meta_json payload. */
export function attachmentIds(meta: Record<string, unknown> | null | undefined): string[] {
  if (meta == null) return [];
  const raw = meta.attachment_ids;
  if (!Array.isArray(raw)) return [];
  return raw.filter((x): x is string => typeof x === "string");
}
