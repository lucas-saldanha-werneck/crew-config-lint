from pathlib import Path

from crew_config_lint import lint_data, lint_dir
from crew_config_lint.cli import main

EX = Path(__file__).parent.parent / "examples"


def codes(fs):
    return sorted(f.code for f in fs)


def test_clean_example_has_no_findings():
    assert lint_dir(EX / "clean", ["topic"]) == []


def test_broken_example_findings():
    c = codes(lint_dir(EX / "broken", ["topic", "unused"]))
    assert c.count("E001") == 1      # writer has no backstory
    assert "E003" in c               # agent 'editor'
    assert "E004" in c               # {year}
    assert "E006" in c               # context cycle
    assert "W001" in c               # reviewer unused
    assert "W002" in c               # 'unused' input
    assert "W003" in c               # "Write a report"


def test_missing_fields():
    fs = lint_data({"a": {"role": "x"}}, {"t": {"agent": "a"}})
    assert codes(fs).count("E001") == 2
    assert codes(fs).count("E002") == 2


def test_context_self_and_unknown():
    tasks = {"t": {"description": "one two three four five", "expected_output": "x", "context": ["t", "nope"]}}
    assert codes(lint_data({}, tasks)).count("E005") == 2


def test_escaped_braces_are_not_placeholders():
    agents = {"a": {"role": "r", "goal": "json like {{key}}", "backstory": "b"}}
    tasks = {"t": {"description": "one two three four five", "expected_output": "x", "agent": "a"}}
    assert lint_data(agents, tasks, []) == []


def test_inputs_check_is_optional():
    agents = {"a": {"role": "{x}", "goal": "g", "backstory": "b"}}
    tasks = {"t": {"description": "one two three four five", "expected_output": "x", "agent": "a"}}
    assert lint_data(agents, tasks) == []
    assert codes(lint_data(agents, tasks, [])) == ["E004"]


def test_garbage_yaml_shapes_do_not_crash():
    assert isinstance(lint_data([1, 2], "text"), list)


def test_config_subfolder(tmp_path):
    (tmp_path / "config").mkdir()
    for n in ("agents.yaml", "tasks.yaml"):
        (tmp_path / "config" / n).write_text("{}")
    assert lint_dir(tmp_path) == []


def test_cli_exit_codes(capsys):
    assert main([str(EX / "clean"), "-i", "topic"]) == 0
    assert main([str(EX / "broken")]) == 1
    assert main([str(EX / "nope")]) == 2
    assert main([str(EX / "broken"), "--json"]) == 1
    assert '"code"' in capsys.readouterr().out
