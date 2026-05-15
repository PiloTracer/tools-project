import Link from "next/link";

export function DashboardSystem({
  apiOk,
  authLabel,
  showUserAdmin,
}: {
  apiOk: boolean;
  authLabel: string;
  showUserAdmin: boolean;
}) {
  return (
    <div className="dashboard-tile dashboard-tile--system">
      <h2>System</h2>
      <ul className="status-list">
        <li className="status-row">
          <span className={`status-dot ${apiOk ? "status-dot--ok" : "status-dot--bad"}`} />
          <div>
            <span className="status-row-label">API</span>
            <span className={`status-row-value ${apiOk ? "" : "err"}`}>
              {apiOk ? "Reachable" : "Check stack / ports"}
            </span>
          </div>
        </li>
        <li className="status-row">
          <span className="status-dot status-dot--neutral" />
          <div>
            <span className="status-row-label">Auth</span>
            <span className="status-row-value muted">{authLabel}</span>
          </div>
        </li>
      </ul>
      {showUserAdmin ? (
        <div className="dashboard-system-footer">
          <Link href="/admin/users" className="dashboard-footer-link">
            User admin
            <span className="muted"> · superusers</span>
          </Link>
        </div>
      ) : null}
    </div>
  );
}
