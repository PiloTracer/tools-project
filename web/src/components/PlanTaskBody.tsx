"use client";

import { MarkdownBody } from "@/components/MarkdownBody";
import { parseTaskText } from "@/shared/plan-text";

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div
      aria-hidden="true"
      style={{
        background: "var(--muted-bg, #e5e7eb)",
        borderRadius: 999,
        height: 6,
        width: "100%",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          background: "var(--accent, #2563eb)",
          height: "100%",
          width: `${percent}%`,
        }}
      />
    </div>
  );
}

/**
 * Reads a plan-imported task the human way: a plain "what this delivers" summary, the
 * acceptance criteria as a checklist, and the original technical text one click away.
 *
 * The stored description stays untouched (it is the plan's source of truth and remains
 * editable in the editor), this is presentation only — so it works for tasks imported
 * before the plan-sync skill was adjusted.
 */
export function PlanTaskBody({
  title,
  description,
}: {
  title: string;
  description: string | null;
}) {
  const parsed = parseTaskText(title, description);
  const hasContent = parsed.acceptance.length > 0 || parsed.hasTech || Boolean(parsed.plainFallback);

  return (
    <div className="stack" style={{ gap: "0.85rem" }}>
      <div>
        <h3 style={{ margin: "0 0 0.35rem", fontSize: "0.95rem" }}>What this delivers</h3>
        {parsed.remainder ? (
          <div className="muted text-sm" style={{ marginTop: 0 }}>
            <MarkdownBody text={parsed.remainder} />
          </div>
        ) : null}
        {parsed.acceptance.length > 0 ? (
          <>
            <p className="muted text-sm" style={{ marginBottom: "0.25rem" }}>
              Done when:
            </p>
            <ul className="stack" style={{ margin: 0, paddingLeft: "1.1rem", gap: "0.2rem" }}>
              {parsed.acceptance.map((item, i) => (
                <li key={i} className="text-sm">
                  {item}
                </li>
              ))}
            </ul>
          </>
        ) : !parsed.plainFallback ? (
          <p className="muted text-sm" style={{ marginBottom: 0 }}>
            No acceptance criteria recorded for this task.
          </p>
        ) : null}
      </div>

      {parsed.plainFallback ? <MarkdownBody text={parsed.plainFallback} /> : null}

      {!hasContent ? <p className="muted text-sm">No description.</p> : null}

      {parsed.hasTech ? (
        <details>
          <summary className="muted text-sm" style={{ cursor: "pointer" }}>
            Technical details (plan source)
          </summary>
          <div className="stack" style={{ gap: "0.35rem", marginTop: "0.5rem" }}>
            {parsed.tech.planRef ? (
              <p className="text-sm" style={{ margin: 0 }}>
                <span className="muted">Plan ref:</span>{" "}
                <code>{parsed.tech.planRef}</code>
                {parsed.tech.planVersion ? (
                  <>
                    {" "}
                    <span className="muted">· plan version:</span> {parsed.tech.planVersion}
                  </>
                ) : null}
              </p>
            ) : null}
            {parsed.tech.complexity ? (
              <p className="text-sm" style={{ margin: 0 }}>
                <span className="muted">Complexity:</span> {parsed.tech.complexity}
              </p>
            ) : null}
            {parsed.tech.frNfr.length > 0 ? (
              <p className="text-sm" style={{ margin: 0 }}>
                <span className="muted">Traces:</span> {parsed.tech.frNfr.join(", ")}
              </p>
            ) : null}
            {parsed.tech.files.length > 0 ? (
              <p className="text-sm" style={{ margin: 0 }}>
                <span className="muted">Files:</span>{" "}
                {parsed.tech.files.map((f, i) => (
                  <span key={i}>
                    {i > 0 ? ", " : ""}
                    <code>{f}</code>
                  </span>
                ))}
              </p>
            ) : null}
            {parsed.tech.source ? (
              <p className="text-sm" style={{ margin: 0 }}>
                <span className="muted">Source:</span> <code>{parsed.tech.source}</code>
              </p>
            ) : null}
          </div>
          <details style={{ marginTop: "0.5rem" }}>
            <summary className="muted text-sm" style={{ cursor: "pointer" }}>
              Original stored description (markdown)
            </summary>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontSize: "0.8rem",
                marginTop: "0.4rem",
              }}
            >
              {description}
            </pre>
          </details>
        </details>
      ) : null}

      {description ? (
        <details>
          <summary className="muted text-sm" style={{ cursor: "pointer" }}>
            Original (technical) text
          </summary>
          <div className="stack" style={{ gap: "0.5rem", marginTop: "0.5rem" }}>
            <p className="muted text-sm" style={{ margin: 0 }}>
              Plan title, exactly as imported:
            </p>
            <MarkdownBody text={parsed.fullTitle} />
            <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>
              Plan description, exactly as imported:
            </p>
            <MarkdownBody text={description} />
          </div>
        </details>
      ) : null}
    </div>
  );
}

export { ProgressBar };
