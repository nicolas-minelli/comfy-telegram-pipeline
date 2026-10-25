# Continuous integration

GitHub Actions runs the public source checks on pushes, pull requests, and manual requests. It uses GitHub-hosted Windows and Linux machines, not the operator's computer. No repository secrets are required. This workflow does not install, start, or change n8n, Comfy, Docker services, Tailscale, or Telegram in your deployment.

## Checks

| Job | What it checks |
|---|---|
| Offline tests (windows-2022) | Windows PowerShell 5.1 parsing and the existing 11 offline tests through `tools/Test-Repository.ps1` |
| Offline tests (ubuntu-24.04) | The same 11 Python tests and five API graph builders on Linux |
| Both test jobs | Python 3.13, Node.js 22, tracked JSON parsing, Python syntax, and exact agreement between generated API graphs and committed `comfy/api` files |
| Secret scan | Gitleaks v8.30.1 on the working tree and all Git refs available in the full checkout, with fully redacted findings |

The secret scanner image is pinned by digest. It is pulled with network access, then both scans run in containers with networking disabled and a read-only source mount. Findings are not uploaded as artifacts. A successful scan is not proof that a repository contains no sensitive information; review exports and commit contents before pushing.

The checked-in T5 fixture is deliberately invalid for Comfy submission. CI parses it but does not submit it. A green run does not validate video quality, GPU/ROCm behavior, real credentials, live recovery, or a clean installation.

## Enable it

1. Add `.github/workflows/ci.yml`, `.github/dependabot.yml`, and this guide to your repository and push them. The first push starts CI if Actions is enabled.
2. Open the repository's **Actions** tab and select **CI**. Expect three jobs: Windows offline tests, Linux offline tests, and secret scanning.
3. In **Settings > Actions > General**, keep workflow token permissions read-only. Do not add your bot token, Comfy key, Tailscale credentials, or production configuration to Actions secrets for this CI.
4. Require approval for external contributors' workflow runs where available. Review workflow modifications before approving runs.
5. Once the initial run succeeds, optionally create a branch ruleset for your default branch and require the exact check names displayed by GitHub. Require all three jobs. Rulesets protect merges; merely adding CI does not block merges or pushes.
6. In **Actions > CI > Run workflow**, manually run the default branch when needed. Manual dispatch becomes available after the workflow is on the default branch.

Example from the Windows clone:

```powershell
Set-Location 'E:\AI\repos\comfy-telegram-pipeline'
git status --short
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Fix whitespace errors before continuing.' }
git add -- .github/workflows/ci.yml .github/dependabot.yml docs/CI.md
if ($LASTEXITCODE -ne 0) { throw 'Could not stage the CI files.' }
git diff --cached --stat
git commit -m "ci: add Windows and Linux offline validation"
if ($LASTEXITCODE -ne 0) { throw 'Commit failed; review the output.' }
git push
if ($LASTEXITCODE -ne 0) { throw 'Push failed; review the remote and branch.' }
gh run list --workflow ci.yml --limit 5
```

Do not blindly commit unrelated staged files: inspect `git diff --cached --name-only` before committing.

## How to respond to failures

- **Generated graphs differ:** run `node tools/export-runtime-graphs.cjs` locally, review `git diff -- comfy/api`, and commit the intended graph changes together with builder changes. Do not remove the check to hide drift.
- **Windows-only failure:** inspect the PowerShell step and locale/path handling. Linux passing does not demonstrate Windows compatibility.
- **Secret detected:** do not paste raw findings into public issues. Revoke/rotate any real exposed credential first. Removing it from the latest file does not remove it from Git history. Review `SECURITY.md` and the export checklist.
- **Action/image download failure:** check GitHub's logs and service status, then retry if it was transient. This is separate from a test assertion failure.
- **Fork pull request awaiting approval:** the maintainer must review the changes before approving the workflow run; this is expected.

Use `gh run view RUN_ID --log-failed` for logs and `gh run watch RUN_ID --exit-status` to wait for a particular run. Replace `RUN_ID` with the ID shown by `gh run list`.

## Security and maintenance

The workflow uses `pull_request`, not `pull_request_target`, has `contents: read`, disables persisted checkout credentials, bounds job runtime, and cancels superseded runs of the same event/ref. No self-hosted runner or production network access is configured. Third-party actions are pinned to immutable commits. Dependabot proposes monthly action updates; review and merge those PRs after successful checks.

Dependabot's GitHub Actions ecosystem does not update the Gitleaks digest embedded in the shell command. Update that digest deliberately after reviewing a new scanner release. Python and Node.js runtime lines are also explicit maintenance choices. The workflow does not publish a release or deploy production; CD remains a separate future step.

## Validation status

The authoring environment ran the 11 existing offline tests and graph generation. Windows PowerShell, Docker-based secret scanning, and execution on GitHub-hosted runners must be confirmed by the first CI run. No live service or GPU test was performed during CI preparation.
