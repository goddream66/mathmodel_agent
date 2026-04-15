import { startTransition, useDeferredValue, useEffect, useState } from "react";
import {
  addMessage,
  createSession,
  deleteSession,
  getMeta,
  getReport,
  getSession,
  listSessions,
  runSession,
  setSections,
  uploadFiles,
} from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { ReportViewer } from "./components/ReportViewer";
import { SectionSelector } from "./components/SectionSelector";
import { StatusPanel } from "./components/StatusPanel";
import { UploadPanel } from "./components/UploadPanel";
import type { ReportSection, SessionSummary } from "./types";

export default function App() {
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [sessionHistory, setSessionHistory] = useState<SessionSummary[]>([]);
  const [sections, setSectionOptions] = useState<ReportSection[]>([]);
  const [selectedSections, setSelectedSections] = useState<string[]>([]);
  const [draftMessage, setDraftMessage] = useState("");
  const [statusMessage, setStatusMessage] = useState("Create a session to start drafting.");
  const [errorMessage, setErrorMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [reportMarkdown, setReportMarkdown] = useState("");
  const deferredReport = useDeferredValue(reportMarkdown);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      setBusy(true);
      setErrorMessage("");
      try {
        const [meta, sessionsPayload] = await Promise.all([getMeta(), listSessions()]);
        if (cancelled) {
          return;
        }
        const nextSession =
          sessionsPayload.sessions[0] ?? (await createSession());
        const nextReport =
          nextSession.report_ready
            ? await getReport(nextSession.session_id, nextSession.selected_sections)
            : null;
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setSectionOptions(meta.sections);
          setSessionHistory(sessionsPayload.sessions.length > 0 ? sessionsPayload.sessions : [nextSession]);
          setSession(nextSession);
          setSelectedSections(nextSession.selected_sections);
          setReportMarkdown(nextReport?.selected_report_md ?? "");
          setStatusMessage("Session ready. Add the problem statement, upload files, then run the pipeline.");
        });
      } catch (error) {
        if (!cancelled) {
          setErrorMessage((error as Error).message);
        }
      } finally {
        if (!cancelled) {
          setBusy(false);
        }
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  async function syncSections(nextSections: string[]) {
    if (!session) {
      return;
    }
    setBusy(true);
    setErrorMessage("");
    try {
      const payload = await setSections(session.session_id, nextSections);
      const report =
        payload.report_ready ? await getReport(payload.session_id, payload.selected_sections) : null;
      startTransition(() => {
        syncSessionState(payload);
        setReportMarkdown(report?.selected_report_md ?? payload.latest_report_md ?? "");
        setStatusMessage(
          payload.selected_sections.length === 0
            ? "Report section filter reset to full draft."
            : `Report now focused on ${payload.selected_sections.join(", ")}.`,
        );
      });
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSendMessage() {
    if (!session || !draftMessage.trim()) {
      return;
    }
    setBusy(true);
    setErrorMessage("");
    try {
      const payload = await addMessage(session.session_id, draftMessage);
      startTransition(() => {
        syncSessionState(payload);
        setDraftMessage("");
        setStatusMessage("Message saved. Keep refining the task, or run the pipeline.");
      });
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(role: "problem" | "data", files: File[]) {
    if (!session) {
      return;
    }
    setBusy(true);
    setErrorMessage("");
    try {
      const payload = await uploadFiles(session.session_id, role, files);
      startTransition(() => {
        syncSessionState(payload);
        setStatusMessage(
          role === "problem"
            ? "Problem file uploaded. You can still add multi-turn clarifications in chat."
            : `Attached ${files.length} supporting data file${files.length > 1 ? "s" : ""}.`,
        );
      });
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleRun() {
    if (!session) {
      return;
    }
    setBusy(true);
    setErrorMessage("");
    try {
      const payload = await runSession(session.session_id, selectedSections);
      startTransition(() => {
        syncSessionState(payload);
        setReportMarkdown(payload.report?.selected_report_md ?? "");
        setStatusMessage("Pipeline finished. Review the paper draft and iterate with new messages or data.");
      });
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function toggleSection(key: string) {
    const nextSections = selectedSections.includes(key)
      ? selectedSections.filter((item) => item !== key)
      : [...selectedSections, key];
    void syncSections(nextSections);
  }

  async function handleCreateSession() {
    setBusy(true);
    setErrorMessage("");
    try {
      const payload = await createSession();
      startTransition(() => {
        syncSessionState(payload, { prepend: true });
        setDraftMessage("");
        setReportMarkdown("");
        setStatusMessage("New session created. Add the problem statement or upload files.");
      });
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSelectSession(sessionId: string) {
    setBusy(true);
    setErrorMessage("");
    try {
      const payload = await getSession(sessionId);
      const report =
        payload.report_ready ? await getReport(payload.session_id, payload.selected_sections) : null;
      startTransition(() => {
        syncSessionState(payload);
        setReportMarkdown(report?.selected_report_md ?? payload.latest_report_md ?? "");
        setStatusMessage("Restored a previous session.");
      });
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteSession(sessionId: string) {
    setBusy(true);
    setErrorMessage("");
    try {
      await deleteSession(sessionId);
      const payload = await listSessions();
      startTransition(() => {
        setSessionHistory(payload.sessions);
        if (session?.session_id === sessionId) {
          const nextSession = payload.sessions[0] ?? null;
          setSession(nextSession);
          setSelectedSections(nextSession?.selected_sections ?? []);
          setReportMarkdown(nextSession?.latest_report_md ?? "");
        }
        setStatusMessage("Session deleted.");
      });
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function syncSessionState(
    payload: SessionSummary,
    options: {
      prepend?: boolean;
    } = {},
  ) {
    setSession(payload);
    setSelectedSections(payload.selected_sections);
    setSessionHistory((current) => {
      const filtered = current.filter((item) => item.session_id !== payload.session_id);
      return options.prepend ? [payload, ...filtered] : [payload, ...filtered];
    });
    if (payload.latest_error?.message) {
      setErrorMessage(`[${payload.latest_error.stage}] ${payload.latest_error.message}`);
    } else {
      setErrorMessage("");
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">MathAgent Web</p>
          <h1>Turn your modeling workflow into a live drafting workspace.</h1>
          <p className="hero-copy">
            Chat with the system, upload tables, run the multi-agent pipeline, and inspect the paper draft without leaving the browser.
          </p>
        </div>
        <div className="hero-actions">
          <button className="accent-button" disabled={busy || !session} onClick={handleRun}>
            {busy ? "Working..." : "Generate Draft"}
          </button>
          <span className="hero-note">
            {session ? `Session ${session.session_id.slice(0, 8)}` : "Preparing session"}
          </span>
        </div>
      </section>

      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}

      <div className="dashboard-grid">
        <div className="left-stack">
          <HistoryPanel
            activeSessionId={session?.session_id ?? null}
            busy={busy}
            onCreate={() => void handleCreateSession()}
            onSelect={(sessionId) => void handleSelectSession(sessionId)}
            onDelete={(sessionId) => void handleDeleteSession(sessionId)}
            sessions={sessionHistory}
          />
          <ChatPanel
            messages={session?.messages ?? []}
            draftMessage={draftMessage}
            busy={busy}
            onDraftChange={setDraftMessage}
            onSend={handleSendMessage}
          />
          <UploadPanel
            problemFiles={session?.problem_files ?? []}
            dataFiles={session?.data_files ?? []}
            busy={busy}
            onUpload={handleUpload}
          />
        </div>

        <div className="right-stack">
          <StatusPanel busy={busy} session={session} statusMessage={statusMessage} />
          <SectionSelector
            busy={busy}
            sections={sections}
            selected={selectedSections}
            onToggle={toggleSection}
            onSelectAll={() => void syncSections([])}
          />
          <ReportViewer report={deferredReport} />
        </div>
      </div>
    </main>
  );
}
