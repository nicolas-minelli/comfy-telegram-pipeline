# Publishing v1.0.0-preview.1

Run this from your actual Windows Git clone, after reviewing the updated files. The distributed source snapshot does not contain your .git history or authenticated GitHub session. These commands do not modify the production n8n/Comfy runtime.

## 1. Review and commit the release documents

Confirm LICENSE exists. The preview is intentionally not a stable clean-install certification. The operator has already confirmed Windows parser checks and all six offline tests passing.

```powershell
Set-Location 'E:\AI\repos\comfy-telegram-pipeline'
git status --short --untracked-files=all
git diff --check
git diff -- README.md EXPORT-REVIEW.md docs
```

After reviewing the expected changes only:

```powershell
git add -- LICENSE README.md EXPORT-REVIEW.md docs/DEPENDENCIES.md docs/MODELS.md docs/PROJECT-REVIEW.md docs/TUTORIAL.md docs/RELEASING.md docs/releases/v1.0.0-preview.1.md
git diff --cached --check
git diff --cached --name-only
git commit -m "Prepare MIT-licensed v1.0.0 preview release"
if ($LASTEXITCODE -ne 0) { throw 'Commit failed; resolve before continuing.' }
```

If all intended changes were already committed, do not create an empty commit; continue after confirming a clean tree.

## 2. Fetch available history and check scope

```powershell
git fetch origin --tags
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
$shallow = git rev-parse --is-shallow-repository
if ($LASTEXITCODE -ne 0) { throw 'Not a Git repository.' }
if ($shallow -eq 'true') {
    git fetch --unshallow origin --tags
    if ($LASTEXITCODE -ne 0) { throw 'Could not retrieve full history.' }
}
git branch -r
git log --all --oneline -10
```

The scan covers commits reachable from local refs, including fetched branches/tags. Check `git config --get-all remote.origin.fetch`: a restricted single-branch refspec may not fetch every remote branch. Deleted/unfetched remote history, unreachable objects, other clones, and GitHub caches are not certified by this scan.

## 3. Scan files and Git history

Use the pinned scanner image already used by the operator. The bind is read-only; network is disabled while scanning; values are redacted. Git's safe.directory option is scoped to this container process to avoid Docker ownership mismatch without changing host Git configuration.

```powershell
$repoPath = (Get-Location).Path
$scanImage = 'ghcr.io/gitleaks/gitleaks:v8.30.1'

docker run --rm --network none `
    --mount "type=bind,source=$repoPath,target=/repo,readonly" `
    $scanImage dir /repo --redact=100 --no-banner
if ($LASTEXITCODE -ne 0) { throw 'Working-tree scan failed. Do not publish.' }

docker run --rm --network none `
    --env GIT_CONFIG_COUNT=1 `
    --env GIT_CONFIG_KEY_0=safe.directory `
    --env GIT_CONFIG_VALUE_0=/repo `
    --mount "type=bind,source=$repoPath,target=/repo,readonly" `
    $scanImage git /repo --log-opts="--all" --redact=100 --no-banner
if ($LASTEXITCODE -ne 0) { throw 'History scan failed. Do not publish.' }
```

Read scanner output as well as its exit code; investigate a zero-commit scan. Review staged/tracked paths for private data scanners cannot recognize. If a real secret is found, revoke/rotate it first. Removing a current file does not remove it from old commits. Do not force-push rewritten history without a separate recovery/review plan.

## 4. Create a fixed release tag and exact-commit asset

Continue only after both scans pass and the tree contains no uncommitted files. These checks prevent accidentally packaging a different working-tree state.

```powershell
if (@(git status --porcelain).Count -ne 0) { throw 'Working tree must be clean.' }
$releaseTag = 'v1.0.0-preview.1'
git show-ref --verify --quiet "refs/tags/$releaseTag"
if ($LASTEXITCODE -eq 0) { throw 'Tag already exists. Inspect it; do not move or overwrite it.' }
if ($LASTEXITCODE -ne 1) { throw 'Tag lookup failed.' }
$releaseCommit = git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve HEAD.' }
git tag -a $releaseTag -m 'Comfy Telegram Pipeline v1.0.0 preview 1' $releaseCommit
if ($LASTEXITCODE -ne 0) { throw 'Tag creation failed.' }

$assetDir = Join-Path $env:TEMP 'comfy-pipeline-release'
New-Item -ItemType Directory -Path $assetDir -Force | Out-Null
$asset = Join-Path $assetDir "comfy-telegram-pipeline-$releaseTag.zip"
if (Test-Path -LiteralPath $asset) { throw 'Asset already exists. Inspect it or use another temporary directory.' }
git archive --format=zip --prefix='comfy-telegram-pipeline/' --output=$asset $releaseTag
if ($LASTEXITCODE -ne 0) { throw 'Archive creation failed.' }
$assetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $asset).Hash.ToLowerInvariant()
$checksumFile = Join-Path $assetDir 'SHA256SUMS.txt'
$checksumLine = $assetHash + '  ' + [IO.Path]::GetFileName($asset) + "`n"
[IO.File]::WriteAllText($checksumFile, $checksumLine, (New-Object Text.UTF8Encoding($false)))
$releaseCommit
$asset
```

Do not reuse an existing tag by deleting/moving it. If interrupted after tag creation, inspect `git rev-parse "$releaseTag^{commit}"` and resume from the correct step. A checksum detects changes relative to a trusted reference; it is not a digital signature.

## 5. Push and publish the prerelease

GitHub CLI must be installed and authenticated. If missing, install it through your normal trusted package process; for Windows, `winget install --id GitHub.cli --exact` is one option. Reopen PowerShell if PATH changed. Authenticate using its interactive browser flow, never a token pasted into a command.

```powershell
gh --version
gh auth status
```

If not authenticated, run `gh auth login` and follow the browser prompts. Do not print credentials or use `gh auth token` for support.

Check the remote before publishing:

```powershell
git remote get-url origin
```

It must be your intended repository. Then:

```powershell
git push origin HEAD
if ($LASTEXITCODE -ne 0) { throw 'Branch push failed.' }
git push origin $releaseTag
if ($LASTEXITCODE -ne 0) { throw 'Tag push failed.' }

gh release create $releaseTag $asset $checksumFile `
    --repo nicolas-minelli/comfy-telegram-pipeline `
    --verify-tag `
    --prerelease `
    --title 'Comfy Telegram Pipeline v1.0.0-preview.1' `
    --notes-file '.\docs\releases\v1.0.0-preview.1.md'
if ($LASTEXITCODE -ne 0) { throw 'Release creation failed. Inspect existing releases before retrying.' }

gh release view $releaseTag --repo nicolas-minelli/comfy-telegram-pipeline
git status --short
```

`--verify-tag` requires the pushed tag to exist. `--prerelease` records preview status. Publishing a release does not change a private repository into a public one. Repository visibility is a separate decision; do not change it as an incidental step.

## 6. Remaining reproducibility work

See DEPENDENCIES.md and MODELS.md. Do not manufacture missing revisions/hashes or silently claim a local hash was verified against upstream. The preview explicitly records these limitations.

Official references: [Gitleaks](https://github.com/gitleaks/gitleaks), [GitHub release create](https://cli.github.com/manual/gh_release_create).
