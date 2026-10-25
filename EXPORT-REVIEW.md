# Export review — October 24, 2026

## Scope

Six exports: main LTX, Telegram Bot, Automatic Recovery v2 supervisor, Error Handler v2, controlled-failure T5, and Manual Recovery. Manual Recovery was included after the initial batch.

## Input observations

- No populated pinData or staticData.
- Authorization headers for Comfy endpoints used expressions, without literal tokens in those fields.
- Exports contained local credential references, webhook identifiers, instance metadata, an authorized user, and a personal domain.
- Credential IDs/names do not imply the associated token was present in the export. Bindings were removed to distribute installation-independent examples.

## Changes to the distribution copy

- Removed 31 credential bindings and 86 webhook IDs.
- Removed instance metadata, root workflow/version IDs, exported tags, and groups.
- Removed local Error Workflow associations; configure these after import.
- Disabled all templates and cleared pinned data.
- Regenerated internal node IDs, preserving node names and connections.
- Replaced the authorized ID with zero in related references, and the personal domain with an invalid example.
- Isolated T5 under `tests/fixtures`, disabled.
- Left production files, models, and local secrets untouched.

## Checks

- Six valid n8n JSON files; 380 nodes with valid connection targets.
- All JavaScript jsCode blocks syntax-checked with Node's AsyncFunction constructor, without executing them.
- Checked the final templates for known personal markers, original root workflow IDs, Telegram token patterns, and 64-character hexadecimal literals.
- No remaining node credential bindings or webhook IDs.

## Limits and next steps

This review cannot detect every possible secret format. Never include raw exports, Docker volumes, `.env`, keys, or logs in the same commit. Before pushing, review the exact staged files and scan both repository contents and the history being published.

The package includes local configuration preparation, diagnostics, and a tutorial. Original project material is licensed under MIT; dependency licenses remain separate. A complete production service/update system is not included. See `docs/PROJECT-REVIEW.md` for additional review and tests. Windows parser/offline checks have since passed. Validate setup-helper execution and a clean installation before advertising a stable installable release.

Keep private installation files in your Windows `production` folder. That name only organizes exported files; it does not change n8n's internal storage.

## Updated Comfy graphs

Old reference interpolation/upscale exports were replaced. The five graphs in `comfy/api` come from the current n8n builders executed with synthetic inputs for 9:16 and 16:9. The LTX input template is in `comfy/templates`.

Checked VHS_LoadVideoPath, batch size 8, audio, aspect-specific dimensions, finalizer, connections, and substitute dynamic IDs. The reproduction script neither runs the scheduler nor submits GPU work. Production was not changed.

## Confirmed custom nodes

Both received files matched the installed package. Job Control's personal Telegram ID was replaced with zero without changing authorization/validation behavior. The finalizer was preserved. `E:\AI\media` and `E:\AI\media\final` remain documented local defaults, not secrets.

Synthetic graph inputs now use run_id `tg-0-1-e1` and an execution-specific output prefix, satisfying finalizer constraints. This fixes distribution examples only.

## Tutorial and automation

Includes an operational guide, FAQ examples, SVG/PNG infographic, and scripts that prepare local copies only. No key/token is embedded. The ID-discovery helper requests a new test bot's token with hidden input and refuses to replace an existing webhook. It has not been run with real credentials during this review.

## English distribution

Documentation, tutorials, infographic labels, Telegram messages, help text, status descriptions, and script prompts are provided in English. Functional identifiers, node names, connections, commands, and protocol fields are preserved. Translation is not a production deployment or a change to the integration protocol.
