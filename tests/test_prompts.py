import unittest

from mathagent.prompts import load_prompt, render_prompt


class PromptTemplateTest(unittest.TestCase):
    def test_load_prompt_from_templates(self) -> None:
        text = load_prompt("modeling_system")
        self.assertIn("mathematical modeling", text)

    def test_render_prompt_substitutes_variables(self) -> None:
        rendered = render_prompt("writing_user", problem_text="demo", subproblems_json="[]")
        self.assertIn("demo", rendered)
        self.assertIn("[]", rendered)


if __name__ == "__main__":
    unittest.main()
