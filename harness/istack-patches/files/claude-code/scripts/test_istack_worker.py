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

MUX_VARIABLES = ("HC_TERMINAL_ID", "REX_BLOCK", "ISTACK_MUX")

# The start of every fake multiplexer tool: it logs its arguments, and answer_wait() gives the scripted replies of
# FAKE_WAITS in order, one per call of the wait command.
FAKE_TOOL_START = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    from pathlib import Path
    log = Path(os.environ["FAKE_LOG"])
    with log.open("a") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")

    def answer_wait(command):
        replies = json.loads(os.environ["FAKE_WAITS"])
        count = sum(1 for line in log.read_text().splitlines() if json.loads(line)[0] == command)
        reply = replies[min(count, len(replies)) - 1]
        if reply.get("write_report"):
            Path(os.environ["FAKE_REPORT"]).write_text("report")
        print(json.dumps(reply["json"]))
        sys.exit(reply.get("code", 0))

""")

FAKE_HC = FAKE_TOOL_START + textwrap.dedent("""\
    command = sys.argv[1]
    if command == "run":
        print(json.dumps({"address": "t9", "name": sys.argv[sys.argv.index("--name") + 1]}))
    elif command == "wait":
        answer_wait("wait")
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


class FakeMuxTestCase(unittest.TestCase):
    """Runs istack-worker against a fake multiplexer tool that logs its calls."""

    FAKE_TOOL = ""
    ROLE_LINE = ""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.tool = root / "tool"
        self.tool.write_text(self.FAKE_TOOL)
        self.tool.chmod(0o755)
        self.report = root / "out" / "report.md"
        self.log = root / "tool.log"
        self.rule = root / "rule.md"
        self.rule.write_text(self.ROLE_LINE)

    def run_script(self, arguments, waits=(), **environment):
        """Run istack-worker with only the multiplexer variables given in `environment`."""
        base = {key: value for key, value in os.environ.items() if key not in MUX_VARIABLES}
        base.update({"ISTACK_MODELS_RULE": str(self.rule), "FAKE_LOG": str(self.log), "FAKE_WAITS": json.dumps(list(waits)),
                     "FAKE_REPORT": str(self.report), "ISTACK_STARTUP_POLL_SECONDS": "0", **environment})
        completed = subprocess.run([sys.executable, str(SCRIPT), *arguments], capture_output=True, text=True, env=base)
        return completed.returncode, json.loads(completed.stdout or completed.stderr)

    def read_calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]


class WorkerLifecycleTest(FakeMuxTestCase):
    FAKE_TOOL = FAKE_HC
    ROLE_LINE = "swarm workers: pi p/deepseek-v4 high\n"

    def setUp(self):
        super().setUp()
        self.brief = Path(self.directory.name) / "brief.md"
        self.brief.write_text("do it")

    def run_worker(self, arguments, waits):
        return self.run_script(arguments, waits, ISTACK_HC=str(self.tool), HC_TERMINAL_ID="t1")

    def build_start_arguments(self):
        return ["start", "--role", "swarm workers", "--name", "Swarm 1", "--cwd", self.directory.name,
                "--brief", str(self.brief), "--report", str(self.report)]

    def run_and_wait(self, arguments, waits):
        code, started = self.run_worker(arguments, waits)
        self.assertEqual(code, 0, started)
        return self.run_worker(["wait", "--name", started["name"], "--report", str(self.report)], waits)

    def test_start_runs_the_role_command_and_wait_returns_the_report_once_done(self):
        code, result = self.run_and_wait(self.build_start_arguments(), [
            {"json": {"reason": "timeout", "status": "working"}},
            {"json": {"reason": "status", "status": "done", "turn": 1}, "write_report": True},
        ])
        self.assertEqual(code, 0)
        self.assertEqual((result["status"], result["name"], result["report_exists"]), ("done", "swarm-1", True))
        run_call = self.read_calls()[0]
        self.assertEqual(run_call[run_call.index("--") + 1:run_call.index("--") + 5], ["pi", "--model", "p/deepseek-v4", "--thinking"])
        self.assertIn(str(self.brief), run_call[-1])

    def test_done_without_a_report_is_reported_with_the_screen_tail(self):
        code, result = self.run_and_wait(self.build_start_arguments(), [{"json": {"reason": "status", "status": "done", "turn": 1}}])
        self.assertEqual((result["status"], result["tail"]), ("no-report", "screen tail"))

    def test_stop_kills_and_removes_each_worker(self):
        code, result = self.run_worker(["stop", "swarm-1", "swarm-2"], [])
        self.assertEqual([call[0] for call in self.read_calls()], ["kill", "rm", "kill", "rm"])
        self.assertEqual([entry["name"] for entry in result], ["swarm-1", "swarm-2"])

    def test_startup_idle_keeps_waiting(self):
        code, result = self.run_and_wait(self.build_start_arguments(), [
            {"json": {"reason": "status", "status": "idle", "turn": 0}},
            {"json": {"reason": "status", "status": "blocked", "turn": 1}, "code": 9},
        ])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(sum(1 for call in self.read_calls() if call[0] == "wait"), 2)

    def test_a_finished_terminal_counts_as_exited(self):
        code, result = self.run_and_wait(self.build_start_arguments(), [{"json": {"error": {"kind": "finished"}}, "code": 11}])
        self.assertEqual(result["status"], "exited")

    def test_brief_text_is_saved_beside_the_report(self):
        arguments = [argument for argument in self.build_start_arguments() if argument != str(self.brief)]
        arguments[arguments.index("--brief")] = "--brief-text"
        arguments.insert(arguments.index("--brief-text") + 1, "judge the candidates")
        code, result = self.run_and_wait(arguments, [{"json": {"reason": "status", "status": "done", "turn": 1}, "write_report": True}])
        brief_path = self.report.with_name("report.brief.md")
        self.assertEqual((code, brief_path.read_text()), (0, "judge the candidates"))
        self.assertIn(str(brief_path), self.read_calls()[0][-1])

    def test_claude_switch_moves_a_pi_seat_to_claude_code_with_its_effort(self):
        code, result = self.run_worker(self.build_start_arguments() + ["--claude"],
                                       [{"json": {"reason": "status", "status": "done", "turn": 1}, "write_report": True}])
        run_call = self.read_calls()[0]
        self.assertEqual(run_call[run_call.index("--") + 1:run_call.index("--") + 6], ["claude", "--model", "opus", "--effort", "high"])
        self.assertEqual(result["family"], "claude")

    def test_start_refuses_outside_rex_and_herdr(self):
        code, result = self.run_script(self.build_start_arguments(), ISTACK_HC=str(self.tool))
        self.assertEqual(code, 2)
        self.assertIn("HC_TERMINAL_ID", result["error"])

    def test_a_session_is_refused_under_herdr(self):
        code, result = self.run_worker(self.build_start_arguments() + ["--session", "AG-7 fix"], [])
        self.assertEqual(code, 2)
        self.assertIn("--session is for Rex", result["error"])

    def test_read_returns_the_screen(self):
        code, result = self.run_worker(["read", "--name", "swarm-1"], [])
        self.assertEqual(result, {"name": "swarm-1", "screen": "screen tail"})


FAKE_REX = FAKE_TOOL_START + textwrap.dedent("""\
    state = json.loads(os.environ["FAKE_REX_STATE"])
    arguments = sys.argv[1:]
    # Like Rex, a block is found only in the session that -s names, or else in the caller's own session.
    if "-b" in arguments:
        block = arguments[arguments.index("-b") + 1]
        home = next((key for key, value in state.items() if block in ["block:" + label for label in value["windows"]]), None)
        scope = arguments[arguments.index("-s") + 1] if "-s" in arguments else "session:own"
        if home is not None and home != scope:
            print(f'Error: block target "{block}" not found')
            sys.exit(1)
    if arguments[:2] == ["ls", "--json"]:
        listings = sum(1 for line in log.read_text().splitlines() if json.loads(line)[:1] == ["ls"])
        print(json.dumps({"sessions": [{"session_id": key, "label": value["label"]} for key, value in state.items()
                                       if listings == 1 or not value.get("ends_after_first_listing")]}))
    elif arguments[:2] == ["window", "ls"]:
        session = state[arguments[arguments.index("-s") + 1]]
        if session.get("unlistable"):
            print("Error: request timed out")
            sys.exit(1)
        print(json.dumps({"windows": [
            {"window_id": "window:" + label, "label": label, "layers": [{"blocks": [{"block_id": "block:" + label}]}]}
            for label in session["windows"]]}))
    elif arguments[0] == "new":
        print(json.dumps({"session_id": "session:new", "initial_windows": [{"window_id": "window:w", "block_ids": ["block:b"]}]}))
    elif arguments[:2] == ["window", "new"]:
        print(json.dumps({"window_id": "window:w", "block_ids": ["block:b"]}))
    elif arguments[:2] == ["block", "inspect"]:
        print(json.dumps({"session_id": "session:own"}))
    elif arguments[0] == "do":
        answer_wait("do")
    elif arguments[0] == "send" and arguments[-1].startswith("-") and "--" not in arguments:
        print(f"Error: unknown shorthand flag: ' ' in {arguments[-1]}")
        sys.exit(2)
    elif arguments[0] == "send" and os.environ.get("FAKE_SEND_FAILS"):
        print("Error: no such block")
        sys.exit(1)
    elif arguments[0] == "capture" and os.environ.get("FAKE_CAPTURE_FAILS"):
        print("Error: request timed out")
        sys.exit(1)
    elif arguments[0] == "capture":
        print(os.environ.get("FAKE_SCREEN", "rex screen tail"))
""")


class RexWorkerTest(FakeMuxTestCase):
    FAKE_TOOL = FAKE_REX
    ROLE_LINE = "swarm workers: haiku high\n"
    SESSIONS = {"session:own": {"label": "hq", "windows": ["esh"]},
                "session:ticket": {"label": "AG-7 fix", "windows": ["impl"]}}

    def run_worker(self, arguments, waits=(), **environment):
        """Run inside a Rex terminal, unless `environment` names another multiplexer setup."""
        return self.run_script(arguments, waits, ISTACK_REX=str(self.tool), FAKE_REX_STATE=json.dumps(self.SESSIONS),
                               ISTACK_REX_STATE=str(Path(self.directory.name) / "state"),
                               **(environment or {"REX_BLOCK": "block:esh"}))

    def build_start_arguments(self, name, *extra):
        return ["start", "--role", "swarm workers", "--name", name, "--cwd", self.directory.name,
                "--brief-text", "do it", "--report", str(self.report), *extra]

    def test_first_worker_of_a_ticket_creates_its_session(self):
        code, result = self.run_worker(self.build_start_arguments("review", "--session", "AG-9 new ticket"))
        self.assertEqual((code, result["terminal"], result["session"]), (0, "block:b", "session:new"))
        created = self.read_calls()[-1]
        self.assertEqual(created[:created.index("--")],
                         ["new", "AG-9 new ticket", "--window", "review", "--cwd", str(Path(self.directory.name).resolve()),
                          "--keep-open", "--json"])
        self.assertEqual(created[created.index("--") + 1:created.index("--") + 4], ["claude", "--model", "haiku"])

    def test_next_worker_of_a_ticket_is_a_tab_in_its_session(self):
        code, result = self.run_worker(self.build_start_arguments("review", "--session", "AG-7 fix"))
        self.assertEqual((code, result["session"]), (0, "session:ticket"))
        self.assertEqual(self.read_calls()[-1][:6], ["window", "new", "-s", "session:ticket", "review", "--focus=false"])

    def test_without_a_session_the_worker_joins_the_callers_session(self):
        code, result = self.run_worker(self.build_start_arguments("panel-1"))
        self.assertEqual((code, result["session"]), (0, "session:own"))

    def test_without_a_session_and_outside_rex_start_is_refused(self):
        code, result = self.run_worker(self.build_start_arguments("panel-1"), ISTACK_MUX="rex")
        self.assertEqual(code, 2)
        self.assertIn("--session", result["error"])

    def test_a_missing_cwd_is_refused(self):
        arguments = self.build_start_arguments("review")
        arguments[arguments.index("--cwd") + 1] = str(Path(self.directory.name) / "no-such-worktree")
        code, result = self.run_worker(arguments)
        self.assertEqual(code, 2)
        self.assertIn("is not a directory", result["error"])
        self.assertFalse(self.log.exists())

    def test_a_live_name_is_refused(self):
        code, result = self.run_worker(self.build_start_arguments("impl", "--session", "AG-7 fix"))
        self.assertEqual(code, 2)
        self.assertIn("already open", result["error"])

    def test_wait_returns_the_report_once_the_turn_is_done(self):
        waits = [{"json": {"status": "working"}}, {"json": {"status": "done"}, "write_report": True}]
        self.report.parent.mkdir()
        code, result = self.run_worker(["wait", "--name", "impl", "--report", str(self.report)], waits)
        self.assertEqual((code, result["status"], result["report_exists"]), (0, "done", True))
        waited = [call for call in self.read_calls() if call[0] == "do"]
        self.assertEqual(len(waited), 2)
        self.assertEqual(waited[0][1:5], ["-s", "session:ticket", "-b", "block:impl"])

    def test_wait_reports_an_exit_with_the_screen_tail(self):
        code, result = self.run_worker(["wait", "--name", "impl", "--report", str(self.report)],
                                       [{"json": {"status": "exited", "exit_code": 7}}])
        self.assertEqual((result["status"], result["tail"]), ("exited", "rex screen tail"))

    def test_an_agent_that_sits_idle_counts_as_a_turn_without_a_report(self):
        code, result = self.run_worker(["wait", "--name", "impl", "--report", str(self.report)],
                                       [{"json": {"status": "idle", "at": "T1"}}])
        self.assertEqual((result["status"], result["tail"]), ("no-report", "rex screen tail"))

    def test_wait_for_a_closed_window_is_exited(self):
        code, result = self.run_worker(["wait", "--name", "gone", "--report", str(self.report)])
        self.assertEqual((code, result["status"]), (0, "exited"))

    def test_a_failed_window_listing_is_an_error_not_exited(self):
        self.SESSIONS = {**self.SESSIONS, "session:slow": {"label": "AG-8 slow", "windows": [], "unlistable": True}}
        code, result = self.run_worker(["wait", "--name", "impl", "--report", str(self.report)])
        self.assertEqual(code, 2)
        self.assertIn("could not list the windows of session AG-8 slow", result["error"])

    def test_a_session_that_ended_since_the_listing_has_no_windows(self):
        self.SESSIONS = {**self.SESSIONS, "session:ended": {"label": "AG-8 old", "windows": [], "unlistable": True,
                                                            "ends_after_first_listing": True}}
        code, result = self.run_worker(["wait", "--name", "gone", "--report", str(self.report)])
        self.assertEqual((code, result["status"]), (0, "exited"))

    def test_a_failed_wait_is_an_error_not_working(self):
        code, result = self.run_worker(["wait", "--name", "impl", "--report", str(self.report)],
                                       [{"json": {"text": "Error: process: no such block"}, "code": 1}])
        self.assertEqual(code, 2)
        self.assertIn("rex wait for impl failed", result["error"])

    def test_send_makes_the_next_wait_ignore_the_turn_before(self):
        waits = [{"json": {"status": "done", "at": "T1"}}, {"json": {"status": "done", "at": "T2"}}]
        code, result = self.run_worker(["send", "--name", "impl", "one more thing"], waits)
        self.assertEqual((code, result["sent"]), (0, True))
        self.assertEqual([call[:1] for call in self.read_calls()[-2:]], [["send"], ["send-key"]])
        self.run_worker(["wait", "--name", "impl", "--report", str(self.report)], waits)
        baseline_read, wait = [call for call in self.read_calls() if call[0] == "do"]
        self.assertEqual(baseline_read[-1], "timeout=0")
        self.assertEqual(wait[-1], "after=T1")

    def test_send_types_a_message_that_starts_with_a_dash(self):
        code, result = self.run_worker(["send", "--name", "impl", "- and the tests"], [{"json": {"status": "done", "at": "T1"}}])
        self.assertEqual((code, result["sent"]), (0, True))

    def test_a_failed_send_leaves_the_next_wait_on_the_current_turn(self):
        waits = [{"json": {"status": "done", "at": "T1"}}]
        code, result = self.run_worker(["send", "--name", "impl", "one more thing"], waits, REX_BLOCK="block:esh",
                                       FAKE_SEND_FAILS="1")
        self.assertEqual(code, 2)
        self.assertIn("rex send to impl failed", result["error"])
        self.run_worker(["wait", "--name", "impl", "--report", str(self.report)], waits)
        wait = [call for call in self.read_calls() if call[0] == "do"][-1]
        self.assertFalse(any(argument.startswith("after=") for argument in wait))

    def test_read_returns_the_screen(self):
        code, result = self.run_worker(["read", "--name", "impl"])
        self.assertEqual(result, {"name": "impl", "screen": "rex screen tail"})

    def test_read_returns_a_screen_of_json_as_text(self):
        code, result = self.run_worker(["read", "--name", "impl"], REX_BLOCK="block:esh", FAKE_SCREEN="[1, 2]")
        self.assertEqual(result, {"name": "impl", "screen": "[1, 2]"})

    def test_a_failed_capture_is_not_shown_as_the_screen(self):
        code, result = self.run_worker(["read", "--name", "impl"], REX_BLOCK="block:esh", FAKE_CAPTURE_FAILS="1")
        self.assertEqual(result["screen"], "(rex could not read the worker's screen: Error: request timed out)")

    def test_stop_closes_the_workers_window(self):
        code, result = self.run_worker(["stop", "impl", "gone"])
        self.assertEqual(result, [{"name": "impl", "removed": True}, {"name": "gone", "removed": False}])
        closed = [call for call in self.read_calls() if call[:2] == ["window", "close"]]
        self.assertEqual(closed, [["window", "close", "window:impl", "-s", "session:ticket"]])


if __name__ == "__main__":
    unittest.main()
