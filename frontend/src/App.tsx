import { startTransition, useDeferredValue, useEffect, useState } from "react";
import { addMessage, createSession, getMeta, runSession, setSections, uploadFiles } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { ReportViewer } from "./components/ReportViewer";
import { SectionSelector } from "./components/SectionSelector";
import { StatusPanel } from "./components/StatusPanel";
import { UploadPanel } from "./components/UploadPanel";
import type { ReportSection, SessionSummary } from "./types";

export default function App() {
  const [session, setSession] = useState<SessionSummary | null>(null);
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
        const [meta, nextSession] = await Promise.all([getMeta(), createSession()]);
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setSectionOptions(meta.sections);
          setSession(nextSession);
          setSelectedSections(nextSession.selected_sections);
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
      startTransition(() => {
        setSession(payload);
        setSelectedSections(payload.selected_sections);
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
        setSession(payload);
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
        setSession(payload);
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
        setSession(payload);
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
