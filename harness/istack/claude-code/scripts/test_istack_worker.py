import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("istack-worker")


def load_worker_module():
    loader = importlib.machinery.SourceFileLoader("istack_worker", str(SCRIPT))
    spec = importlib.util.spec_from_loader("istack_worker", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


worker = load_worker_module()

FAKE_HC = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    from pathlib import Path
    log = Path(os.environ["FAKE_HC_LOG"])
    with log.open("a") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")
    command = sys.argv[1]
    if command == "run":
        print(json.dumps({"address": "t9", "name": sys.argv[sys.argv.index("--name") + 1]}))
    elif command == "wait":
        replies = json.loads(os.environ["FAKE_HC_WAITS"])
        count = sum(1 for line in log.read_text().splitlines() if json.loads(line)[0] == "wait")
        reply = replies[min(count, len(replies)) - 1]
        if reply.get("write_report"):
            Path(os.environ["FAKE_HC_REPORT"]).write_text("report")
        print(json.dumps(reply["json"]))
        sys.exit(reply.get("code", 0))
    elif command == "read":
        print("screen tail")
    else:
        print(json.dumps({}))
""")


class RoleTableTest(unittest.TestCase):
    def test_reads_claude_pi_and_codex_entries(self):
        self.assertEqual(worker.build_command(worker.parse_entry("opus high")), ["claude", "--model", "opus", "--effort", "high"])
        self.assertEqual(worker.build_command(worker.parse_entry("pi opencode-go/deepseek-v4.1-flash high")),
                         ["pi", "--model", "opencode-go/deepseek-v4.1-flash", "--thinking", "high"])
        self.assertEqual(worker.build_command(worker.parse_entry("codex gpt-5.5 max")),
                         ["codex", "-m", "gpt-5.5", "-c", "model_reasoning_effort=xhigh"])
        self.assertEqual(worker.build_command(worker.parse_entry("inherit-parent")), ["claude"])

    def test_names_a_family_per_vendor(self):
        self.assertEqual(worker.parse_entry("pi opencode-go/deepseek-v4.1-flash high")["family"], "deepseek")
        self.assertEqual(worker.parse_entry("codex gpt-5.5 high")["family"], "gpt")
        self.assertEqual(worker.parse_entry("sonnet low")["family"], "claude")

    def test_rejects_an_entry_without_effort(self):
        with self.assertRaises(worker.WorkerError):
            worker.parse_entry("pi opencode-go/deepseek-v4.1-flash")

    def test_rule_lines_override_defaults_and_comma_roles_resolve_by_part(self):
        with tempfile.TemporaryDirectory() as directory:
            rule = Path(directory) / "rule.md"
            rule.write_text("# comment: ignored\nswarm workers: pi x/deepseek-v4 high\n"
                            "reflect judgment, divergent, synthesizer: sonnet low\n")
            original = worker.RULE_PATH
            worker.RULE_PATH = rule
            try:
                self.assertEqual(worker.resolve_role("swarm workers")[0]["harness"], "pi")
                self.assertEqual(worker.resolve_role("reflect divergent")[0]["effort"], "low")
                self.assertEqual(worker.resolve_role("refactoring")[0]["model"], "sonnet")
                self.assertEqual(len(worker.resolve_role("arena runners")), 2)
                with self.assertRaises(worker.WorkerError):
                    worker.resolve_role("no such role")
            finally:
                worker.RULE_PATH = original

    def test_turns_any_text_into_a_terminal_name(self):
        self.assertEqual(worker.convert_to_terminal_name("Arena: Candidate #1"), "arena-candidate-1")
        self.assertEqual(len(worker.convert_to_terminal_name("x" * 50)), 32)


class WorkerLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.hc = root / "hc"
        self.hc.write_text(FAKE_HC)
        self.hc.chmod(0o755)
        self.brief = root / "brief.md"
        self.brief.write_text("do it")
        self.report = root / "out" / "report.md"
        self.log = root / "hc.log"
        self.rule = root / "rule.md"
        self.rule.write_text("swarm workers: pi p/deepseek-v4 high\n")

    def tearDown(self):
        self.directory.cleanup()

    def run_worker(self, arguments, waits):
        environment = {**os.environ, "ISTACK_HC": str(self.hc), "ISTACK_MODELS_RULE": str(self.rule),
                       "FAKE_HC_LOG": str(self.log), "FAKE_HC_WAITS": json.dumps(waits),
                       "FAKE_HC_REPORT": str(self.report), "HC_TERMINAL_ID": "t1", "ISTACK_STARTUP_POLL_SECONDS": "0"}
        completed = subprocess.run([sys.executable, str(SCRIPT), *arguments], capture_output=True, text=True, env=environment)
        return completed.returncode, json.loads(completed.stdout or completed.stderr)

    def hc_calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def start_arguments(self):
        return ["start", "--role", "swarm workers", "--name", "Swarm 1", "--cwd", self.directory.name,
                "--brief", str(self.brief), "--report", str(self.report)]

    def run_and_wait(self, arguments, waits):
        code, started = self.run_worker(arguments, waits)
        self.assertEqual(code, 0, started)
        return self.run_worker(["wait", "--name", started["name"], "--report", str(self.report)], waits)

    def test_start_runs_the_role_command_and_wait_returns_the_report_once_done(self):
        code, result = self.run_and_wait(self.start_arguments(), [
            {"json": {"reason": "timeout", "status": "working"}},
            {"json": {"reason": "status", "status": "done", "turn": 1}, "write_report": True},
        ])
        self.assertEqual(code, 0)
        self.assertEqual((result["status"], result["name"], result["report_exists"]), ("done", "swarm-1", True))
        run_call = self.hc_calls()[0]
        self.assertEqual(run_call[run_call.index("--") + 1:run_call.index("--") + 5], ["pi", "--model", "p/deepseek-v4", "--thinking"])
        self.assertIn(str(self.brief), run_call[-1])

    def test_done_without_a_report_is_reported_with_the_screen_tail(self):
        code, result = self.run_and_wait(self.start_arguments(), [{"json": {"reason": "status", "status": "done", "turn": 1}}])
        self.assertEqual((result["status"], result["tail"]), ("no-report", "screen tail"))

    def test_stop_kills_and_removes_each_worker(self):
        code, result = self.run_worker(["stop", "swarm-1", "swarm-2"], [])
        self.assertEqual([call[0] for call in self.hc_calls()], ["kill", "rm", "kill", "rm"])
        self.assertEqual([entry["name"] for entry in result], ["swarm-1", "swarm-2"])

    def test_startup_idle_keeps_waiting(self):
        code, result = self.run_and_wait(self.start_arguments(), [
            {"json": {"reason": "status", "status": "idle", "turn": 0}},
            {"json": {"reason": "status", "status": "blocked", "turn": 1}, "code": 9},
        ])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(sum(1 for call in self.hc_calls() if call[0] == "wait"), 2)

    def test_a_finished_terminal_counts_as_exited(self):
        code, result = self.run_and_wait(self.start_arguments(), [{"json": {"error": {"kind": "finished"}}, "code": 11}])
        self.assertEqual(result["status"], "exited")

    def test_brief_text_is_saved_beside_the_report(self):
        arguments = [argument for argument in self.start_arguments() if argument != str(self.brief)]
        arguments[arguments.index("--brief")] = "--brief-text"
        arguments.insert(arguments.index("--brief-text") + 1, "judge the candidates")
        code, result = self.run_and_wait(arguments, [{"json": {"reason": "status", "status": "done", "turn": 1}, "write_report": True}])
        brief_path = self.report.with_name("report.brief.md")
        self.assertEqual((code, brief_path.read_text()), (0, "judge the candidates"))
        self.assertIn(str(brief_path), self.hc_calls()[0][-1])

    def test_claude_switch_moves_a_pi_seat_to_claude_code_with_its_effort(self):
        code, result = self.run_worker(self.start_arguments() + ["--claude"],
                                       [{"json": {"reason": "status", "status": "done", "turn": 1}, "write_report": True}])
        run_call = self.hc_calls()[0]
        self.assertEqual(run_call[run_call.index("--") + 1:run_call.index("--") + 6], ["claude", "--model", "opus", "--effort", "high"])
        self.assertEqual(result["family"], "claude")

    def test_start_refuses_outside_herdr(self):
        environment = {**os.environ, "ISTACK_HC": str(self.hc), "ISTACK_MODELS_RULE": str(self.rule)}
        environment.pop("HC_TERMINAL_ID", None)
        completed = subprocess.run([sys.executable, str(SCRIPT), *self.start_arguments()],
                                   capture_output=True, text=True, env=environment)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("HC_TERMINAL_ID", completed.stderr)


if __name__ == "__main__":
    unittest.main()
