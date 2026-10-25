# Portfolio and community maintenance

The repository is an open-source portfolio/community preview under MIT, not a supported product with guaranteed delivery dates. Keep the README honest about the working personal deployment, passing offline checks, and unvalidated clean installation.

## Apply community files

Review and commit README.md, CONTRIBUTING.md, SECURITY.md, .github/ISSUE_TEMPLATE, .github/PULL_REQUEST_TEMPLATE.md, this guide, and the updated project review. Merge/push them to the actual default branch for issue templates to be available to contributors.

Existing releases and source ZIPs remain snapshots of their original tags. Do not move v1.0.0-preview.1 to include these files. This change can live on the default branch without creating a new release immediately.

## Repository settings to verify manually

Adding files does not change GitHub repository settings.

1. Confirm the intended repository and actual default branch.
2. Enable Issues if you want public bug reports and suggestions.
3. If the repository is intended for public open-source collaboration, confirm its visibility is Public. A public-facing license or a release does not itself change repository visibility. Review tracked files, history, and any repository data that will become visible before changing visibility.
4. For public repositories where supported, enable Private vulnerability reporting in the repository's code-security settings. Confirm contributors can find the report action in Security → Advisories. Until then, SECURITY.md instructs reporters to request a private contact without publishing details.
5. Optionally configure a branch ruleset for the default branch: require PRs where practical and block force pushes/deletions. Choose review requirements that a solo maintainer can actually satisfy; requiring another approval can block your own work. Do not require nonexistent CI checks.

Read-only status commands:

```powershell
gh repo view nicolas-minelli/comfy-telegram-pipeline `
    --json nameWithOwner,visibility,hasIssuesEnabled,defaultBranchRef
```

If Issues are disabled and you intend to enable them:

```powershell
gh repo edit nicolas-minelli/comfy-telegram-pipeline --enable-issues
if ($LASTEXITCODE -ne 0) { throw 'Could not enable Issues.' }
```

This command changes a repository setting. It does not configure private reporting, rulesets, or visibility. No authenticated GitHub setting was changed while generating these files.

## Lightweight issue handling

- Reproducible bug: clarify affected version/stage and minimal steps; reproduce when time permits.
- Unclear report: ask for selected sanitized evidence, not the entire private runtime/export.
- Feature: evaluate usefulness, resource cost, architectural impact, and simpler alternatives before accepting work.
- Duplicate: link the existing issue and close with a short explanation.
- Vulnerability: move the conversation to the private reporting process without repeating sensitive details publicly.

Labels such as bug, enhancement, documentation, and needs-information are optional manual organization. Templates do not assume those labels already exist.

## Pull request review

Check intent, all affected components, public-export hygiene, and tests appropriate to the change. A passing offline suite does not validate live GPU behavior or every scheduler race. Ask for evidence where it matters and keep unperformed tests explicit.

For workflow changes, review names/IDs, expressions, embedded helpers, generated graphs, Job Control/finalizer compatibility, and error/recovery paths. Avoid merging a change that fixes one path while bypassing a reservation or approval elsewhere.

No new CI/CD, automatic merge, scheduled support, or clean-install commitment is introduced by this community package. Contributors can propose these separately.

## Publication checklist

- README links to contribution and security policies.
- Bug and feature forms appear under New issue on the default branch.
- A new PR shows the PR template.
- Private-reporting status matches the wording of the security policy.
- Current files and history have been reviewed/scanned before changing visibility.
- Published tags are preserved.

Official references: [issue template configuration](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository), [GitHub CLI repository editing](https://cli.github.com/manual/gh_repo_edit).
