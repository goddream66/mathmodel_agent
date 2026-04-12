import type { ReportSection } from "../types";

type SectionSelectorProps = {
  sections: ReportSection[];
  selected: string[];
  busy: boolean;
  onToggle: (key: string) => void;
  onSelectAll: () => void;
};

export function SectionSelector(props: SectionSelectorProps) {
  const { sections, selected, busy, onToggle, onSelectAll } = props;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Report Shape</p>
          <h2>Section Control</h2>
        </div>
        <button className="ghost-button" disabled={busy} onClick={onSelectAll}>
          {selected.length === 0 ? "Using All" : "Reset to All"}
        </button>
      </div>

      <div className="section-grid">
        {sections.map((section) => {
          const active = selected.includes(section.key);
          return (
            <button
              className={`section-chip ${active ? "active" : ""}`}
              key={section.key}
              disabled={busy}
              onClick={() => onToggle(section.key)}
              type="button"
            >
              <span>{section.title}</span>
              <code>{section.key}</code>
            </button>
          );
        })}
      </div>
    </section>
  );
}
