import type { UploadSummary } from "../types";

type UploadPanelProps = {
  problemFiles: UploadSummary[];
  dataFiles: UploadSummary[];
  busy: boolean;
  onUpload: (role: "problem" | "data", files: File[]) => void;
};

function FileList({ files, emptyText }: { files: UploadSummary[]; emptyText: string }) {
  if (files.length === 0) {
    return <div className="muted-block">{emptyText}</div>;
  }

  return (
    <ul className="file-list">
      {files.map((file) => (
        <li key={file.path}>
          <span>{file.name}</span>
          <code>{file.role}</code>
        </li>
      ))}
    </ul>
  );
}

export function UploadPanel(props: UploadPanelProps) {
  const { problemFiles, dataFiles, busy, onUpload } = props;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Files</p>
          <h2>Upload Problem and Data</h2>
        </div>
      </div>

      <div className="upload-grid">
        <label className="upload-box">
          <span className="upload-title">Problem File</span>
          <span className="upload-copy">Upload a `.txt`, `.md`, or `.pdf` problem statement.</span>
          <input
            disabled={busy}
            type="file"
            accept=".txt,.md,.pdf"
            onChange={(event) => {
              const files = Array.from(event.target.files ?? []);
              if (files.length > 0) {
                onUpload("problem", files);
                event.currentTarget.value = "";
              }
            }}
          />
        </label>

        <label className="upload-box">
          <span className="upload-title">Supporting Data</span>
          <span className="upload-copy">Attach `.csv`, `.json`, or `.xlsx` data tables.</span>
          <input
            disabled={busy}
            type="file"
            accept=".csv,.json,.xlsx,.xlsm"
            multiple
            onChange={(event) => {
              const files = Array.from(event.target.files ?? []);
              if (files.length > 0) {
                onUpload("data", files);
                event.currentTarget.value = "";
              }
            }}
          />
        </label>
      </div>

      <div className="upload-lists">
        <div>
          <h3>Problem File</h3>
          <FileList files={problemFiles} emptyText="No problem file uploaded yet." />
        </div>
        <div>
          <h3>Data Files</h3>
          <FileList files={dataFiles} emptyText="No data files uploaded yet." />
        </div>
      </div>
    </section>
  );
}
