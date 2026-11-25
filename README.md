# crew-config-lint

Independent demo, not affiliated with CrewAI.

A small offline linter for `agents.yaml` and `tasks.yaml` files. These two files are the common way to describe a team of LLM agents: who the agents are, and which task each one does. A typo in them usually shows up late, as a failed run. This tool checks them before the run.

It does not import any agent framework and it does not call any API. It reads YAML and applies seven rules.

## Run it

```
pip install -e .
crew-config-lint path/to/project -i topic -i year
```

The folder needs `agents.yaml` and `tasks.yaml`, either in the folder itself or in `config/`. Each `-i` names an input you pass at run time. With at least one `-i` (or `-i` alone with a made-up name), the `{placeholder}` checks turn on. Without `-i`, they stay off. Add `--json` for JSON output and `--strict` to fail on warnings too. Exit code: 0 clean, 1 findings, 2 files not found.

Try the examples (invented data):

```
crew-config-lint examples/clean -i topic
crew-config-lint examples/broken -i topic -i unused
```

## Rules

| Code | Meaning |
|---|---|
| E001 | agent has no `role`, `goal` or `backstory` |
| E002 | task has no `description` or `expected_output` |
| E003 | task names an agent that does not exist |
| E004 | `{name}` appears in a prompt but is not a declared input |
| E005 | task `context` names an unknown task, or itself |
| E006 | tasks wait on each other in a loop |
| W001 | agent that no task uses |
| W002 | declared input that no prompt uses |
| W003 | task description under 5 words |

Doubled braces (`{{key}}`) are not treated as placeholders.

## What was tested

- 9 offline tests with pytest, run locally and in GitHub Actions: every rule, escaped braces, odd YAML shapes (a list or a string where a map is expected), the `config/` subfolder, and the CLI exit codes.
- The two example projects in `examples/`. They are invented. The "broken" one was written to trigger the rules.

## What was not tested

- Real projects. I did not run it on any real customer or company config.
- Whether the rules match what the CrewAI framework itself accepts. I wrote them from the common file layout, not from the framework source. A field the framework allows may show up here as a finding, and the reverse.
- Other YAML fields (tools, LLM names, `async_execution`, and so on). The tool ignores them.
- Very large files, YAML anchors in unusual places, and Windows paths.
