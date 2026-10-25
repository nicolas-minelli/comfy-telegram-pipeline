# Contributing

Thanks for helping improve Comfy Telegram Pipeline. This is an MIT-licensed portfolio/community project based on a working personal deployment. A clean installation has not been validated. Contributions are reviewed as time permits; a report or pull request does not guarantee a response, acceptance, or release date.

## Choose the right channel

- **Bug:** use the bug report form with reproduction steps, expected/actual behavior, and sanitized environment details.
- **Improvement:** use the feature request form. Explain the problem before proposing implementation.
- **Security issue or leaked credential:** follow [SECURITY.md](SECURITY.md). Do not post exploit details, keys, or credentials in public issues or PRs.
- Search existing issues and pull requests before opening another report.

Documentation corrections and small bug fixes can go directly to a focused PR. Discuss significant protocol, scheduler, runner, or workflow redesigns in an issue before investing in a large implementation.

## Set up a contribution

Fork the repository, clone your fork, and create a branch from the repository's actual default branch. Replace the placeholders below; do not copy another user's paths or credentials.

```powershell
git clone https://github.com/YOUR-ACCOUNT/comfy-telegram-pipeline.git
Set-Location .\comfy-telegram-pipeline
git switch -c fix/short-description
```

Keep runtime data outside the clone. Never import unconfigured public templates over a working production installation. Live testing should use an isolated bot, database/volume, media state, and Comfy instance as appropriate; do not run two supervisors against the same scheduler files.

## Preserve integration contracts

When changing a workflow or custom node, assess the full path affected by the change:

- Telegram authorization, wizard commands, button callbacks, and recipients.
- Admission reservations, submission receipts, uncertain outcomes, cancellation, and recovery.
- Preview approval/rejection and all postprocessing stages.
- Checkpoint/run naming and finalizer publication/receipts.
- Error Handler and supervisor incident handling.

Do not rename nodes or change API node IDs without updating all expressions/builders that reference them. Do not blindly retry an uncertain GPU submission, remove reservation evidence to bypass a block, bypass approval, or expose internal endpoints to make a test pass.

If a change needs coordinated workflow/plugin updates, identify every affected file and the installation/update steps. Do not silently claim backward compatibility. Preserve the single-user and runner assumptions unless the PR intentionally changes and validates them.

## Validation

For changes that affect runtime behavior, run the relevant offline checks:

```powershell
.\tools\Test-Repository.ps1
```

Or run the underlying commands with your selected Python executable:

```powershell
node .\tools\export-runtime-graphs.cjs
python -B .\tests\test_custom_node_contracts.py
python -B .\tests\test_local_configuration.py
python -B .\tests\test_ingress_configuration.py
```

The exporter regenerates the five API examples from builders. Review any resulting graph changes. Offline checks do not establish GPU behavior, clean-install success, or concurrency correctness.

For documentation-only changes, verify local links, examples, and consistency; explain that no runtime code changed. Do not claim tests you did not run. If live tests are not feasible, state this clearly with the expected risk and proposed validation. Add meaningful regression coverage for behavior fixes when practical rather than tests that only mirror implementation text.

Maintain explicit UTF-8 encoding for Python text I/O and subprocess text transport. Windows locales differ. Keep public templates inactive, unpinned, and free of local credential bindings and identifiers.

## Public export hygiene

Before uploading a branch or attaching evidence:

- Review both staged content and newly added files, not only diff statistics.
- Exclude credentials, tokens, key files, n8n databases/volumes, scheduler state, raw private exports, and real customer/personal media.
- Remove signed approval URLs and personal user/chat IDs. Job IDs may contain Telegram IDs.
- Review video/image metadata: VHS video exports may embed workflows, prompts, and paths.
- Use synthetic first-frame names, example roots, and inactive placeholders.
- Scan files and the history being published; scanners are not complete privacy audits.

Useful inspection commands:

```powershell
git status --short --untracked-files=all
git diff --check
git diff --cached --check
git diff --cached --name-only
git diff --cached
```

See [docs/RELEASING.md](docs/RELEASING.md) for scanner commands and exact-tag packaging. Do not move an existing release tag to include your contribution; merge a new commit and let the maintainer decide whether to issue another release.

## Pull request expectations

Use English for public documentation, code-facing messages, issue reports, and PR descriptions where possible. Keep one coherent change per PR and complete the PR template:

1. Problem and resulting behavior.
2. Related issue, if any.
3. Affected components and compatibility/migration impact.
4. Checks actually performed and their results.
5. Remaining limitations or live tests not performed.

Push to your own branch/fork and open a PR targeting the actual default branch. Draft PRs are welcome. Do not include unrelated formatting or generated runtime data.

Original project contributions are made under the existing [MIT License](LICENSE). Preserve third-party attribution and license notices; do not include model weights or assume the project license relicenses dependencies.
