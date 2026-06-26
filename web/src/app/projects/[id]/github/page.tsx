import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { DateDisplay } from "@/components/DateDisplay";
import { ProjectSubNav } from "../ProjectSubNav";

type GithubLinkRow = {
  id: string;
  owner: string;
  repo: string;
  last_synced_at: string | null;
  created_at: string;
};

type CommitRow = {
  id: string;
  short_sha: string;
  message_preview: string;
  html_url: string;
  committed_at: string;
  author_name: string | null;
  owner: string;
  repo: string;
};

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

export default async function ProjectGithubPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }
  const { id } = await params;

  const pr = await apiServerFetch(`/v1/projects/${id}`);
  if (pr.status === 404) {
    notFound();
  }
  if (!pr.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load project.</p>
        <Link href="/projects">← Projects</Link>
      </div>
    );
  }
  const project = (await pr.json()) as ProjectRow;

  const [linksRes, commitsRes] = await Promise.all([
    apiServerFetch(`/v1/projects/${id}/github/links`),
    apiServerFetch(`/v1/projects/${id}/github/commits?limit=50`),
  ]);

  const links: GithubLinkRow[] = linksRes.ok ? await linksRes.json() : [];
  const commits: CommitRow[] = commitsRes.ok
    ? (await commitsRes.json()).items
    : [];

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem" }}>GitHub</h1>
        <ProjectSubNav projectId={id} current="github" />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Linked Repositories</h2>
        {links.length === 0 ? (
          <p className="muted text-sm">No repositories linked yet.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
                <th style={{ padding: "0.5rem 0" }}>Repository</th>
                <th>Last synced</th>
                <th>Synced commits</th>
              </tr>
            </thead>
            <tbody>
              {links.map((l) => (
                <tr key={l.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "0.35rem 0" }}>
                    <a
                      href={`https://github.com/${l.owner}/${l.repo}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {l.owner}/{l.repo}
                    </a>
                  </td>
                  <td>{l.last_synced_at ? <DateDisplay date={l.last_synced_at} /> : "—"}</td>
                  <td>{commits.filter((c) => c.owner === l.owner && c.repo === l.repo).length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Recent Commits</h2>
        {commits.length === 0 ? (
          <p className="muted text-sm">No commits found.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
                <th style={{ padding: "0.5rem 0" }}>SHA</th>
                <th>Message</th>
                <th>Author</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {commits.map((c) => (
                <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "0.35rem 0" }}>
                    <a href={c.html_url} target="_blank" rel="noopener noreferrer">
                      <code>{c.short_sha}</code>
                    </a>
                  </td>
                  <td>{c.message_preview}</td>
                  <td>{c.author_name ?? "—"}</td>
                  <td><DateDisplay date={c.committed_at} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
