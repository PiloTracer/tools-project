import Link from "next/link";
import { readFileSync } from "fs";
import { join } from "path";
import ReactMarkdown from "react-markdown";

export default function AboutPage() {
  let changelog = "";
  try {
    changelog = readFileSync(join(process.cwd(), "src/app/about/CHANGELOG.md"), "utf-8");
  } catch {
    changelog = "*Changelog not available.*";
  }

  return (
    <div className="page-inner stack-lg" style={{ maxWidth: "48rem" }}>
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Home
        </Link>
        <h1 style={{ marginTop: "0.25rem" }}>About</h1>
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Release Notes</h2>
        <p className="muted text-sm">
          Recent improvements and changes to the tools-project platform.
        </p>
      </div>

      <div className="card wide markdown-body">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h2 style={{ marginTop: "1.5rem", marginBottom: "0.5rem" }}>{children}</h2>,
            h2: ({ children }) => <h3 style={{ marginTop: "1.25rem", marginBottom: "0.35rem" }}>{children}</h3>,
            ul: ({ children }) => <ul style={{ paddingLeft: "1.25rem", lineHeight: 1.7 }}>{children}</ul>,
            a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
            code: ({ children }) => <code style={{ background: "var(--surface)", padding: "0.1rem 0.3rem", borderRadius: "3px", fontSize: "0.85em" }}>{children}</code>,
          }}
        >
          {changelog}
        </ReactMarkdown>
      </div>
    </div>
  );
}
