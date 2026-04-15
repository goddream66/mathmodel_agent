import rehypeKatex from "rehype-katex";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

type ReportViewerProps = {
  report: string;
};

export function ReportViewer(props: ReportViewerProps) {
  const { report } = props;

  return (
    <section className="panel report-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Paper Draft</p>
          <h2>Markdown Preview</h2>
        </div>
      </div>

      {report.trim() ? (
        <div className="markdown-shell">
          <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
            {report}
          </ReactMarkdown>
        </div>
      ) : (
        <div className="empty-state report-empty">
          Run the pipeline to generate a structured paper draft. The preview will render the selected report sections here.
        </div>
      )}
    </section>
  );
}
