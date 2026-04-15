from mathagent.reporting import select_report_sections


def test_select_report_sections_accepts_numbered_headings() -> None:
    markdown = "\n".join(
        [
            "# 1. Abstract",
            "summary",
            "",
            "# 2. Problem Statement",
            "problem",
            "",
            "# 5. Results and Analysis",
            "results",
            "",
            "# 6. Conclusion",
            "conclusion",
        ]
    )

    report = select_report_sections(markdown, ["abstract", "problem"])
    assert "summary" in report
    assert "problem" in report
    assert "results" not in report
    assert "conclusion" not in report
