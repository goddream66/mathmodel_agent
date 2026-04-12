import type { SessionSummary } from "../types";

type StatusPanelProps = {
  session: SessionSummary | null;
  busy: boolean;
  statusMessage: string;
};

export function StatusPanel(props: StatusPanelProps) {
  const { session, busy, statusMessage } = props;
  const state = session?.latest_state;
  const findings = state?.results.review_findings ?? [];

  return (
    <section className="panel status-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Run Status</p>
          <h2>Pipeline Snapshot</h2>
        </div>
        <span className={`status-dot ${busy ? "busy" : "idle"}`} />
      </div>

      <div className="status-grid">
        <div className="stat-card">
          <span>Subproblems</span>
          <strong>{state?.subproblem_count ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Solver Runs</span>
          <strong>{state?.solver_run_count ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Review Findings</span>
          <strong>{findings.length}</strong>
        </div>
        <div className="stat-card">
          <span>Status</span>
          <strong>{state?.results.status ?? "idle"}</strong>
        </div>
      </div>

      <div className="muted-block">{statusMessage}</div>

      {state?.subproblems?.length ? (
        <div className="status-subproblems">
          {state.subproblems.map((subproblem) => (
            <article className="subproblem-card" key={subproblem.title}>
              <h3>{subproblem.title}</h3>
              <p>{subproblem.objective ?? "Objective pending clarification."}</p>
              <div className="subproblem-tags">
                {subproblem.task_types.map((taskType) => (
                  <span className="mini-tag" key={taskType}>
                    {taskType}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
