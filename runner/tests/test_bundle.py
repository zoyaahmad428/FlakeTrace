import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runner.bundle import (BundleError, RESET_ASSUMPTIONS, assert_clean, clean_url, read_bundle, redact,
                           write_bundle)

REPO = Path(__file__).resolve().parents[2]
HOME = "C:\\Users\\alice"
PROJECT = HOME + "\\work\\proj"
RECORDS = HOME + "\\records"
KEYS = ["bundle_version", "kind", "tool", "subject", "victim", "command", "parameters", "environment",
        "reset_assumptions", "fresh_run", "run_date", "replay_of", "files"]


def header():
    return {"type": "header", "victim": "pkg.VictimTest#v", "n": 20, "project": PROJECT,
            "java_version": 'openjdk version "1.8.0_502"', "started": "2026-11-21T10:00:00+00:00",
            "project_commit": "abc", "project_dirty": False, "os": "Windows-11", "order_given": False,
            "shuffles": 31, "seed_base": 0, "tool_commit": "def", "tool_dirty": False, "maven_version": "3.9.9",
            "python_version": "3.11.9",
            "jvm": {"java.version": "1.8.0_502", "timezone": "UTC", "locale": "en_US", "file.encoding": "UTF-8",
                    "junit.version": "4.13.2"},
            "lifecycle": "class-grouped", "workspace": "copy", "container_image": None,
            "command": ["diagnose", "--project", PROJECT, "--victim", "pkg.VictimTest#v", "--records", RECORDS],
            "budget": {"limit_invocations": None, "limit_seconds": None, "reserve_invocations": 60},
            "policy": "original", "scope": "module"}


class TestBundle(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="flaketrace-bundle-test-"))
        self.record = self.tmp / "20261121T100000Z-pkg.VictimTest#v.jsonl"
        lines = [header(), {"type": "run", "step": "alone", "order": ["pkg.VictimTest#v"],
                            "outcomes": [{"test": "pkg.VictimTest#v", "passed": True}]}]
        self.record.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
        self.report = {"outcome": "VERIFIED", "victim": {"class": "pkg.VictimTest", "method": "v"},
                       "execution_record_reference": str(self.record), "limitations": [f"see {PROJECT}/x"]}

    def write(self, **kwargs):
        args = dict(paths={PROJECT: "<project>", RECORDS: "<records>"}, home=HOME, user="alice",
                    environment_text=f"Maven home: {HOME}\\maven\n", repository="fixture",
                    module_path="fixtures/od-fixture")
        args.update(kwargs)
        return write_bundle(self.tmp / "bundles", self.report, self.record, **args)

    def test_writes_exactly_five_files_with_lf_and_relative_record(self):
        folder = self.write()
        self.assertEqual(folder.name, "20261121T100000Z-pkg.VictimTest#v")
        self.assertEqual(sorted(p.name for p in folder.iterdir()),
                         ["environment.txt", "manifest.json", "record.jsonl", "replay.md", "report.json"])
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["execution_record_reference"], "record.jsonl")
        for path in folder.iterdir():
            self.assertNotIn(b"\r\n", path.read_bytes(), path.name)

    def test_manifest_has_every_contract_key(self):
        folder = self.write()
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(list(manifest), KEYS)
        self.assertEqual((manifest["bundle_version"], manifest["kind"], manifest["replay_of"]), (1, "diagnosis", None))
        self.assertEqual(manifest["tool"], {"commit": "def", "dirty": False})
        self.assertEqual(manifest["subject"], {"repository": "fixture", "commit": "abc", "dirty": False,
                                               "module_path": "fixtures/od-fixture"})
        self.assertEqual(manifest["victim"], "pkg.VictimTest#v")
        self.assertEqual(manifest["command"][2], "<project>")
        self.assertEqual(manifest["parameters"], {"n": 20, "shuffles": 31, "seed": 0,
                                                  "budget": {"limit_invocations": None, "limit_seconds": None},
                                                  "policy": "original", "scope": "module",
                                                  "lifecycle": "class-grouped", "workspace": "copy"})
        self.assertEqual(manifest["environment"], {"os": "Windows-11", "jdk": "1.8.0_502", "maven": "3.9.9",
                                                   "junit": "4.13.2", "python": "3.11.9", "timezone": "UTC",
                                                   "locale": "en_US", "encoding": "UTF-8", "container_image": None})
        self.assertEqual((manifest["fresh_run"], manifest["run_date"]), (True, "2026-11-21"))
        self.assertEqual(manifest["reset_assumptions"], RESET_ASSUMPTIONS)
        for name in ("report.json", "record.jsonl", "replay.md", "environment.txt"):
            self.assertEqual(manifest["files"][name], hashlib.sha256((folder / name).read_bytes()).hexdigest())

    def test_redacts_every_form_of_a_path(self):
        folder = self.write()
        text = "".join(p.read_text(encoding="utf-8") for p in folder.iterdir())
        for form in (PROJECT, PROJECT.replace("\\", "/"), PROJECT.replace("\\", "\\\\"), HOME, "alice"):
            self.assertNotIn(form, text)
        self.assertIn("<project>", text)
        self.assertIn("<records>", text)
        self.assertIn("<home>", text)
        self.assertEqual(redact(json.dumps({"p": PROJECT + "\\a"}), {PROJECT: "<project>"}, HOME, "alice"),
                         json.dumps({"p": "<project>\\a"}))

    def test_user_name_is_only_a_path_component(self):
        self.assertEqual(redact("pkg.VictimTest#v failed", {}, "C:\\Users\\pkg", "pkg"), "pkg.VictimTest#v failed")
        self.assertEqual(redact("D:\\data\\pkg\\x", {}, "C:\\Users\\pkg", "pkg"), "D:\\data\\<user>\\x")
        assert_clean("pkg.VictimTest#v", "C:\\Users\\pkg", "pkg")

    def test_a_remaining_home_path_is_refused(self):
        with self.assertRaises(BundleError):
            assert_clean(f"left over {HOME}\\x", HOME, "alice")
        with self.assertRaises(BundleError):
            assert_clean("E:/backup/alice/x", HOME, "alice")
        # The final check is a safety net behind redact(): with redaction switched off, nothing is written.
        with mock.patch("runner.bundle.redact", side_effect=lambda text, *args: text):
            with self.assertRaises(BundleError):
                self.write()
        self.assertFalse((self.tmp / "bundles" / self.record.stem).exists())

    def test_manifest_maven_is_the_version_number(self):
        lines = self.record.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        first["maven_version"] = "Apache Maven 3.10.0 (c43a36b8d67be7e0805a411bc0898af1a51f5472)"
        self.record.write_text("".join(line + "\n" for line in [json.dumps(first)] + lines[1:]), encoding="utf-8")
        manifest = json.loads((self.write() / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["environment"]["maven"], "3.10.0")

    # Final review findings (2026-11-21), each seen failing first.

    def test_malformed_manifest_is_a_bundle_error(self):
        folder = self.write()
        (folder / "manifest.json").write_text("[1, 2]", encoding="utf-8")
        with self.assertRaises(BundleError):
            read_bundle(folder)

    def test_home_is_replaced_only_at_a_path_boundary(self):
        self.assertEqual(redact("C:\\Users\\alice\\x", {}, "C:\\Users\\al", "zz"), "C:\\Users\\alice\\x")
        self.assertEqual(redact("C:\\Users\\al\\x", {}, "C:\\Users\\al", "zz"), "<home>\\x")

    def test_paths_are_replaced_whatever_their_case(self):
        self.assertEqual(redact("c:\\users\\alice\\work\\proj\\pom.xml", {PROJECT: "<project>"}, HOME, "alice"),
                         "<project>\\pom.xml")

    def test_a_local_origin_is_redacted_not_refused(self):
        manifest = json.loads((self.write(repository=HOME + "\\repo") / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["subject"]["repository"], "<home>\\repo")

    def test_a_very_short_user_name_is_not_treated_as_a_path_part(self):
        text = json.dumps({"m": "line\\nnext", "p": "src\\n\\x"})
        self.assertEqual(redact(text, {}, "C:\\Users\\n", "n"), text)
        assert_clean(text, "C:\\Users\\n", "n")

    def test_a_failed_write_leaves_no_bundle_folder(self):
        real = Path.write_bytes
        calls = []

        def flaky(path, data):
            calls.append(path)
            if len(calls) == 3:
                raise OSError("disk full")
            return real(path, data)
        with mock.patch.object(Path, "write_bytes", flaky):
            with self.assertRaises(OSError):
                self.write()
        self.assertEqual([p.name for p in (self.tmp / "bundles").iterdir()], [])

    def test_existing_folder_is_not_overwritten(self):
        self.write()
        with self.assertRaises(BundleError):
            self.write()

    def test_clean_url_strips_credentials(self):
        self.assertEqual(clean_url("https://u:t@github.com/a/b.git"), "https://github.com/a/b.git")
        self.assertEqual(clean_url("https://u:p@ss@host/x"), "https://host/x")
        self.assertEqual(clean_url("git@github.com:a/b.git"), "github.com:a/b.git")
        self.assertEqual(clean_url("https://github.com/a/b.git"), "https://github.com/a/b.git")
        self.assertIsNone(clean_url(None))

    def test_read_bundle_refuses_a_changed_file(self):
        folder = self.write()
        bundle = read_bundle(folder)
        self.assertEqual((bundle.manifest["kind"], bundle.report["outcome"], bundle.header["n"]),
                         ("diagnosis", "VERIFIED", 20))
        record = folder / "record.jsonl"
        record.write_bytes(record.read_bytes().replace(b"true", b"fals", 1))
        with self.assertRaisesRegex(BundleError, "record.jsonl"):
            read_bundle(folder)

    def test_replay_md_names_the_commands_and_commits(self):
        text = (self.write() / "replay.md").read_text(encoding="utf-8")
        for needed in ("python -m eval.bundle verify", "python -m runner replay", "def", "abc"):
            self.assertIn(needed, text)

    def test_reset_assumptions_is_the_adr_text(self):
        adr = next((REPO / "docs" / "03-Design" / "decisions").glob("ADR-012-*.md")).read_text(encoding="utf-8")
        for part in ("JVM state only: static fields, system properties, loaded classes, threads",
                     "Files anywhere, the working directory, environment variables, network and external services, "
                     "the system clock and timezone"):
            self.assertIn(part, adr)
            self.assertIn(part, RESET_ASSUMPTIONS)


if __name__ == "__main__":
    unittest.main()
