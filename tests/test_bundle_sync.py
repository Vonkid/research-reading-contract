import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src" / "research_reading_contract" / "bundled_skill"
PUBLIC_SKILL = ROOT / "skills" / "research-reading-contract"


class BundleSyncTests(unittest.TestCase):
    def test_public_and_packaged_skill_files_match(self):
        pairs = [
            (PUBLIC_SKILL / "SKILL.md", BUNDLE / "SKILL.md"),
            (
                PUBLIC_SKILL / "references" / "protocol.md",
                BUNDLE / "references" / "protocol.md",
            ),
            (
                PUBLIC_SKILL / "references" / "reading-report.schema.json",
                BUNDLE / "references" / "reading-report.schema.json",
            ),
            (
                PUBLIC_SKILL / "agents" / "openai.yaml",
                BUNDLE / "agents" / "openai.yaml",
            ),
        ]
        for public_file, bundled_file in pairs:
            with self.subTest(file=public_file.name):
                self.assertEqual(public_file.read_bytes(), bundled_file.read_bytes())

    def test_packaged_schema_matches_root_schema(self):
        self.assertEqual(
            (ROOT / "schemas" / "reading-report.schema.json").read_bytes(),
            (BUNDLE / "references" / "reading-report.schema.json").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
