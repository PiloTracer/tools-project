"use client";

/**
 * Renders persisted attachment images (from meta_json.attachment_ids) as
 * bounded thumbnails. Clicking opens the full-size file in a new tab.
 * URLs are same-origin BFF routes, so the session cookie authenticates them.
 */
export function AttachmentImages({
  ids,
  maxWidth = 720,
}: {
  ids: string[];
  maxWidth?: number;
}) {
  if (!ids.length) return null;
  return (
    <div className="stack" style={{ gap: "0.5rem" }}>
      {ids.map((id) => (
        <a key={id} href={`/api/attachments/${id}`} target="_blank" rel="noopener noreferrer">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`/api/attachments/${id}`}
            alt=""
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
      ))}
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
