"use client";

import ReactMarkdown from "react-markdown";

/**
 * Renders user-authored markdown text (ticket/task descriptions).
 *
 * The create/edit flows embed pasted attachments as markdown images
 * (`![name](/api/attachments/<id>)`), so the read view must render markdown
 * for those images to be visible. Images render as bounded thumbnails;
 * clicking opens the full-size file in a new tab. Attachment URLs are
 * same-origin BFF routes, so the session cookie authenticates them.
 */
export function MarkdownBody({ text }: { text: string }) {
  // Preserve the line breaks users typed (the previous plain-text rendering
  // used white-space: pre-wrap): turn single newlines into hard breaks.
  const md = text.replace(/\n(?!\n)/g, "  \n");
  return (
    <div className="markdown-body text-sm" style={{ lineHeight: 1.6 }}>
      <ReactMarkdown
        components={{
          img: ({ src, alt }) => {
            const href = typeof src === "string" ? src : "";
            return (
              <a href={href} target="_blank" rel="noopener noreferrer">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={href}
                  alt={alt ?? ""}
                  style={{
                    maxWidth: "min(100%, 480px)",
                    maxHeight: 320,
                    height: "auto",
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    cursor: "zoom-in",
                    display: "inline-block",
                    margin: "0.35rem 0",
                  }}
                />
              </a>
            );
          },
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {md}
      </ReactMarkdown>
    </div>
  );
}
