import json
import tempfile
import unittest
from pathlib import Path

from research_reading_contract.installer import (
    doctor_checks,
    install_skills,
    skill_destination,
)


class InstallerTests(unittest.TestCase):
    def test_user_setup_installs_self_contained_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            results = install_skills(["codex", "claude"], home=home)

            self.assertEqual(["installed", "installed"], [item.action for item in results])
            for agent in ("codex", "claude"):
                destination = skill_destination(agent, scope="user", home=home)
                self.assertTrue((destination / "SKILL.md").is_file())
                self.assertTrue(
                    (destination / "references" / "reading-report.schema.json").is_file()
                )
                runtime = (destination / "references" / "runtime.md").read_text()
                self.assertIn("-m research_reading_contract", runtime)
                metadata = json.loads(
                    (destination / ".rrc-install.json").read_text(encoding="utf-8")
                )
                self.assertEqual(agent, metadata["agent"])
                self.assertEqual("0.2.0", metadata["version"])

            checks = doctor_checks(["codex", "claude"], home=home)
            required_checks = [
                check for check in checks if not check.name.endswith("_command")
            ]
            self.assertTrue(all(check.ok for check in required_checks))

    def test_setup_updates_its_own_install(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            install_skills(["codex"], home=home)
            result = install_skills(["codex"], home=home)

        self.assertEqual("updated", result[0].action)

    def test_setup_refuses_unknown_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            destination = skill_destination("codex", scope="user", home=home)
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("unrelated", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unrecognized directory"):
                install_skills(["codex"], home=home)

    def test_doctor_rejects_stale_install_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            install_skills(["codex"], home=home)
            destination = skill_destination("codex", scope="user", home=home)
            marker = destination / ".rrc-install.json"
            metadata = json.loads(marker.read_text(encoding="utf-8"))
            metadata["version"] = "0.1.0"
            marker.write_text(json.dumps(metadata), encoding="utf-8")

            checks = doctor_checks(["codex"], home=home)

        skill_check = next(check for check in checks if check.name == "codex_skill")
        self.assertFalse(skill_check.ok)
        self.assertIn("installed version 0.1.0", skill_check.detail)

    def test_project_destinations_use_agent_native_locations(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory).resolve()
            self.assertEqual(
                project / ".agents" / "skills" / "research-reading-contract",
                skill_destination("codex", scope="project", project_root=project),
            )
            self.assertEqual(
                project / ".claude" / "skills" / "research-reading-contract",
                skill_destination("claude", scope="project", project_root=project),
            )


if __name__ == "__main__":
    unittest.main()
