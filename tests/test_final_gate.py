import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "final_gate.py"


class FinalGateTest(unittest.TestCase):
    def run_gate(self, path: Path):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    def make_article(self, content: str) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="v2a-final-gate-test-"))
        article = temp_dir / "article.md"
        article.write_text(content, encoding="utf-8")
        return article

    def test_normalizes_tw_text_dash_double_commas_and_passes(self):
        article = self.make_article(
            "---\n"
            "title: 測試\n"
            "---\n\n"
            "这是测试语句——以及连续，，逗号。这个软件需要优化，用户权限有竞争力，誰有優勢，誰有劣势。\n\n"
            "![第一張](/tmp/a.png)\n\n"
            "中間有一段文字。\n\n"
            "![第二張](/tmp/b.png)\n"
        )

        result = self.run_gate(article)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK: final article gate passed", result.stdout)
        text = article.read_text(encoding="utf-8")
        self.assertNotIn("这是", text)
        self.assertNotIn("连续", text)
        self.assertNotIn("续", text)
        self.assertNotIn("劣势", text)
        self.assertNotIn("—", text)
        self.assertNotIn("―", text)
        self.assertNotIn("，，", text)
        self.assertIn("這個軟體需要最佳化", text)
        self.assertIn("使用者權限", text)

    def test_fails_on_continuous_images(self):
        article = self.make_article(
            "---\n"
            "title: 測試\n"
            "---\n\n"
            "前文。\n\n"
            "![第一張](/tmp/a.png)\n\n"
            "![第二張](/tmp/b.png)\n"
        )

        result = self.run_gate(article)

        self.assertEqual(result.returncode, 1)
        self.assertIn("continuous images", result.stdout)

    def test_allows_frontmatter_divider_but_fails_body_divider(self):
        article = self.make_article(
            "---\n"
            "title: 測試\n"
            "---\n\n"
            "前文。\n\n"
            "---\n\n"
            "後文。\n"
        )

        result = self.run_gate(article)

        self.assertEqual(result.returncode, 1)
        self.assertIn("body divider line", result.stdout)

    def test_fails_on_html_tag_and_zh_en_spacing(self):
        article = self.make_article(
            "---\n"
            "title: 測試\n"
            "---\n\n"
            "這段有<span>HTML</span>。\n"
            "這段有中的High-level 黏連問題。\n"
        )

        result = self.run_gate(article)

        self.assertEqual(result.returncode, 1)
        self.assertIn("html tag", result.stdout)
        self.assertIn("zh-en spacing", result.stdout)

    def test_allows_complete_english_sentence_residue(self):
        article = self.make_article(
            "---\n"
            "title: 測試\n"
            "---\n\n"
            "這段引用一句英文原話：Surrounding a single engineer with an army of agents is the model.\n"
        )

        result = self.run_gate(article)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK: final article gate passed", result.stdout)

    def test_frontmatter_with_dashes_preserved_intact(self):
        """Frontmatter containing em dashes must NOT be modified by normalization."""
        frontmatter = (
            '---\n'
            'title: "YC Diana Hu：AI 原生公司"\n'
            'hamster_note: "封閉迴路——這三件事加在一起"\n'
            '---\n'
        )
        article = self.make_article(
            frontmatter + "\n正文內容。\n"
        )

        result = self.run_gate(article)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = article.read_text(encoding="utf-8")
        # Frontmatter must be byte-identical
        self.assertTrue(text.startswith(frontmatter),
                        f"Frontmatter was corrupted:\n{text[:200]}")
        # Body em dash would be converted, but frontmatter's should survive
        self.assertIn('封閉迴路——這三件事加在一起', text)


if __name__ == "__main__":
    unittest.main()
