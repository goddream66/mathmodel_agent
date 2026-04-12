export type ReportSection = {
  key: string;
  title: string;
};

export type UploadSummary = {
  role: string;
  name: string;
  path: string;
  created_at: string;
};

export type SolverRunSummary = {
  subproblem_title: string;
  success: boolean;
  schema_valid: boolean;
  summary: string;
  structured_result: Record<string, unknown>;
  artifacts: string[];
};

export type TaskStateSummary = {
  stage: string;
  clarifications: string[];
  subproblem_count: number;
  subproblems: Array<{
    title: string;
    objective: string | null;
    chosen_method: string | null;
    task_types: string[];
  }>;
  solver_run_count: number;
  solver_runs: SolverRunSummary[];
  results: {
    status: string | null;
    solver_summary: string | null;
    review_findings: Array<Record<string, unknown>>;
    solved_subproblems: string[];
    partial_subproblems: string[];
  };
};

export type ReportPayload = {
  session_id: string;
  sections: string[];
  report_md: string;
  selected_report_md: string;
};

export type SessionSummary = {
  session_id: string;
  created_at: string;
  messages: string[];
  problem_files: UploadSummary[];
  data_files: UploadSummary[];
  selected_sections: string[];
  latest_state: TaskStateSummary | null;
  report_ready: boolean;
  report?: ReportPayload;
};
