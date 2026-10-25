# Comfy Telegram Pipeline setup

Technical reference for the published templates, based on the operator-reported Windows + Docker Desktop + n8n 2.43.7 installation. Also read [DEPENDENCIES.md](DEPENDENCIES.md), [MODELS.md](MODELS.md), and the step-by-step [TUTORIAL.md](TUTORIAL.md).

## 1. Scope and isolation

This guide prepares a new installation. Do not replace a working production deployment with sanitized templates. Earlier real tests validated the private deployment; a complete clean installation of the public templates has not yet been tested.

Public templates use Telegram ID `0`, domain `n8n.example.invalid`, and example paths. Do not activate them before configuration. Prefer `tools/Initialize-Pipeline.ps1`: it prepares local copies outside the clone. The following sections document configuration contracts rather than requiring manual editing of every field.

Separate Git code from operational data. A test installation needs its own bot, n8n database/volume, media root, and Comfy instance. Never connect two active supervisors to the same scheduler state or two Comfy integrations to the same media volume. Concurrent installations also need distinct ports and URLs.

Telegram registers one webhook per bot. Testing another Telegram Trigger with the production bot can replace its working webhook.

## 2. Architecture and paths

Telegram → n8n bot → authenticated submission → Comfy generation → preview/approval → interpolation → batch upscale → finalizer → notification.

| Data | Windows example | n8n container | Access |
|---|---|---|---|
| Media and integration state | E:/AI/media | /files | Read/write |
| Comfy output | ACTUAL_COMFY_OUTPUT | /comfy-output | Read-only for n8n |
| n8n database, credentials, binaries | Dedicated Docker volume | /home/node/.n8n | Persistent |

Actual Comfy output must match `windows_output_root` in Initialize Post Processing and the bind mount. A Windows path is not a container path; Windows Comfy cannot open `/comfy-output` as a host directory.

Under the media root:

- `current/`: received images, including Telegram first frames.
- `workflows/ltx.json`: LTX API input template.
- `final/`: final clips and receipts.
- `.telegram-ui/`: generated drafts, scheduler, incidents, submission receipts, and integration key.

Create only needed public folders. Do not invent an empty control.json or copy production state into a test. Runtime code initializes its own files.

## 3. Comfy and custom nodes

1. Prepare Comfy with the classes listed in DEPENDENCIES.md and six models in MODELS.md.
2. Install the documented VideoHelperSuite version. Its exact commit is unknown; do not infer a Git tag from a Manager version.
3. Install both `comfy/custom_nodes/` folders into your selected Comfy `custom_nodes/`, preserving names.
4. Set Job Control's `SHARED_MEDIA_ROOT` to the Windows root mounted at /files. The example default is E:/AI/media.
5. Set the finalizer's `FINAL_DIRECTORY` to that root's final subfolder. Recovery searches SHARED_MEDIA_ROOT/final.
6. Configure the Telegram ID consistently before loading Job Control.
7. Start the backend and check plugin imports. Keeping the Desktop application window open is unnecessary for this automation.

The Comfy process must survive SSH disconnection. The reference deployment uses scheduled-task control; those production service scripts are not included here. A foreground SSH process is not a configured persistent service.

The container must reach `http://host.docker.internal:8188`, or your actual endpoint. Check container connectivity before changing firewall/listening interfaces. If broader listening is needed, limit access with firewall rules. Do not publish Comfy to the Internet.

### Job Control key

On load, the plugin creates or reads `.telegram-ui/comfy-control.key`. n8n must see that same file at `/files/.telegram-ui/comfy-control.key`. Preserve it across restarts and keep it outside Git.

It supplies Bearer authentication for `/n8n/jobs/*` and X-N8N-Recovery-Key for internal recovery. It does not replace Header Auth for `/webhook/start`.

## 4. Correlated Telegram ID references

Prefer the preparer, which updates related markers together in a private copy. The current application supports one authorized user in a private chat; groups/multiple users have not been validated.

| Marker | Location / purpose |
|---|---|
| ALLOWED_CHAT_ID = '0' and ALLOWED_USER_ID = '0' | Authorize Telegram Update |
| tg-0- | Request ID regexes, prefixes, and job globs in n8n Code nodes and Python Job Control |
| /0-0.json | Draft path in Restore Rejected Draft |
| telegram_chat_id: '0' | Initialize Post Processing |
| chat_id:'0', chat_id: '0', chatId value 0 | Handler, supervisor, and notification recipients |

Common helpers are embedded in multiple nodes. Editing only the first bot node leaves recovery, cleanup, and alerts inconsistent. Check all five regular workflows and Job Control; configure T5 identically if testing it.

Never globally replace the character `0`: it would corrupt indices, numeric parameters, FPS, and validation. Use complete markers. Keep configured copies outside Git, for example in an ignored private production directory. Do not use another person's ID for published examples.

## 5. n8n container requirements

Use one n8n instance with filesystem binary mode. This project's file-based scheduler is not n8n distributed queue mode. Adding Redis, replicas, workers, or external runners changes lock/execution assumptions and requires design review.

Verify these local requirements without replacing a working production Compose file:

- Persist `/home/node/.n8n`. If N8N_ENCRYPTION_KEY is explicitly set, preserve it with database backups without publishing it.
- Mount media read/write at `/files`, and Comfy output read-only at `/comfy-output`.
- Set `N8N_DEFAULT_BINARY_DATA_MODE=filesystem`. This reduces binary-storage RAM pressure; it does not remove all node memory use.
- Set `N8N_RESTRICT_FILE_ACCESS_TO=/files;/comfy-output`, using semicolon-separated paths. This controls file nodes; it is not a universal sandbox for require('fs').
- Allow `NODE_FUNCTION_ALLOW_BUILTIN=fs` in the runtime actually executing Code nodes. No wildcard or external npm package permission is needed.
- Set TZ and GENERIC_TIMEZONE consistently, such as America/Sao_Paulo for the reference operator; adjust both for your location.
- Expose n8n HTTP only as needed by the local proxy, for example a host-loopback bind. The generated lab uses 127.0.0.1:5681:5678.
- Preserve waiting executions and integration state in your backup/retention policy.

### Code nodes, runners, and /proc

Code nodes use fs, /files, `/proc/sys/kernel/random/boot_id`, and `/proc/1/stat` to derive a mutex namespace per container incarnation.

For external task runners, module permissions must apply to the actual runner. Main-container variables alone may be insufficient. Validate mounts, permissions, and /proc identity on that executor. Changing runners requires revisiting locks, not merely copying an environment variable. This guide does not claim an external-runner topology is equivalent.

### Internal addresses

For one n8n container:

- Host Comfy: `http://host.docker.internal:8188`.
- Bot → generation and supervisor → generation: `http://127.0.0.1:5678/webhook/start`.
- Recovery wake: `http://127.0.0.1:5678/webhook/video-queue-reconcile`.

Update all corresponding HTTP nodes if topology changes. Do not replace internal URLs with public endpoints just to work around connectivity.

## 6. Import without publishing

Import new workflows in this order:

1. Error Handler.
2. LTX Generation.
3. Automatic Recovery.
4. Telegram Bot.
5. Manual Recovery, for exceptional manual execution only.

Do not publish T5 as a normal workflow. Moving workflows between n8n UI folders preserves existing workflow IDs; importing into another instance can create new IDs.

Install `comfy/templates/ltx.json` as media/workflows/ltx.json for Read Workflow LTX. Files in comfy/api are synthetic final-request examples. Operational interpolation/upscale graphs remain embedded in builders.

Review these fields:

- Initialize Post Processing: windows_output_root, container_output_root, telegram_chat_id, matching mounts/output.
- Send Review Link: your private HTTPS base; preserve resumeFormUrl path and signed query and avoid double slashes.
- HTTP Requests: actual backend address and port.
- Every credential-dependent node: select local credentials.

Do not rename nodes for appearance during setup; expressions and Code blocks reference names.

## 7. Three distinct credential roles

| Role | Configure in | Value |
|---|---|---|
| Telegram | Trigger, messages, download, callback nodes, including handler/supervisor | Installation bot's native Telegram credential |
| LTX entry | Receive Request, Start Video Workflow, Resume Video Workflow | Same Header Auth credential, e.g. LTX Start Auth, header X-LTX-Token, locally generated random value |
| Comfy integration / recovery | Existing expressions reading /files/.telegram-ui/comfy-control.key | Bearer for /n8n/jobs/* and X-N8N-Recovery-Key for wake/resume |

Receive Request must use Header Auth. Both callers of /start must select Generic Credential Type → Header Auth → the same credential. Preserve X-N8N-Recovery-Key on Resume Video Workflow in addition to X-LTX-Token.

The internal wake validates X-N8N-Recovery-Key in its authorization Code. Do not replace it with an unrelated static header.

In Settings → Error Workflow, select the imported handler for the main workflow, bot, and supervisor. Never bind the handler to itself. Error Trigger is not a scheduled trigger that needs publication. Test with an actual automatic execution failure; an editor's manual test is not equivalent.

Keep Manual Recovery outside automatic publication. Do not prefill its confirmation/execution as a default. It is an emergency tool, not a GPU resubmission path.

## 8. HTTPS, Telegram, and private approval

The reference deployment has two surfaces:

- Public HTTPS accepts only the actual Telegram Trigger's POST route through an explicit path/method proxy rule.
- UI and approval forms are private, reached by the operator's phone through Tailscale.

Use this installation's generated production Trigger URL. Do not reuse the author's webhook ID or expose wildcard /webhook/*, /webhook/start, the internal wake, UI, or /n8n/jobs/*.

For n8n 2.43.7, current configuration uses `N8N_WEBHOOK_URL`, replacing legacy WEBHOOK_URL. Confirm version documentation for a new deployment. Do not incidentally migrate a working legacy production setting without separate Telegram/form testing.

Set N8N_EDITOR_BASE_URL to the private UI base, and N8N_PROXY_HOPS to the real number of trusted proxies. Do not blindly copy a hops count. The last proxy must forward appropriate headers.

The Wait form has a per-execution URL, separate from the bot entry endpoint. The phone must reach the private base used by Send Review Link. User/chat IDs authorize incoming events but cannot prove the Internet POST originated from Telegram. Validate trigger/proxy origin protection, including preservation of X-Telegram-Bot-Api-Secret-Token for supported native Trigger versions.

Do not change an existing machine's Funnel/Serve rules merely to follow an example. Configure the routes generated for the specific installation.

## 9. Preflight and activation

Before publishing the bot, confirm:

1. Windows media and /files refer to the same root; key exists without displaying it.
2. GET /queue responds from the container's endpoint.
3. Authenticated GET /n8n/jobs/health reports protocol 2, expected plugin, correct roots, finalizer_available/finalizer_named_output true, and required capabilities.
4. All inventoried nodes exist in object_info. Health does not check available RAM/VRAM or every model file.
5. Credentials are selected; no operational ID zero, .invalid domain, or LOCAL_USER placeholder remains.
6. /files/workflows/ltx.json exists and models appear in loaders.
7. Error Workflow bindings point to the imported handler.
8. No duplicate supervisor/bot workflow controls the same bot/state.

Publish main LTX → supervisor → Telegram bot. Keep Manual Recovery/T5 out of normal activation. Publishing the supervisor starts its schedules, so finish root/key/state checks first.

The supervisor has 20 nodes and two independent minute schedules: Recovery Schedule and Error Alert Schedule. The second handles incident messages, not GPU submissions. Two lightweight runs per minute alone do not indicate repeated queue recovery.

## 10. First test

1. Send /start to the test bot; check commands and a button callback.
2. Submit one short first-frame job with an explicit aspect ratio and supported duration.
3. Check current/, Comfy submission, and status progression. Initial webhook acknowledgment is not GPU acceptance.
4. Open the preview/form on the phone's private network. Leave it waiting to verify approval is required.
5. Approve; check FILM, batch8 upscale, final filename, and receipt. Publication must wait for the complete video.
6. Check final notification and released reservation.
7. In separate tests, reject/retry, stop/status, then multiple jobs.
8. Run T5 separately: intentional pre-sampling HTTP400, classified incident, evidence-based reservation release, no blocked queue. Disable T5 afterward. Alert retries reuse the incident without regenerating video.

Do not force RAM exhaustion or crash the PC for basic validation. Restart recovery comes later with a controlled job and verified checkpoints.

## 11. Persistence and updates

Back up n8n's database/configuration and encryption key, /files state/receipts/integration key, and referenced media as a consistent set. Git does not replace operational backup. Never use `docker compose down -v` to update persistent data.

Control the queue and save private exports before changing production. Do not apply a sample Compose file to production volumes or overwrite configured plugins with inert public templates.

## 12. Official references

- [n8n Docker](https://docs.n8n.io/deploy/host-n8n/install-options/install-with-docker)
- [File access](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.readwritefile)
- [Code modules](https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/enable-modules-in-code-node)
- [Task runners](https://docs.n8n.io/deploy/host-n8n/configure-n8n/set-up-task-runners)
- [Binary data](https://docs.n8n.io/deploy/host-n8n/configure-n8n/scaling/handle-binary-data.md)
- [Reverse proxy](https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/configure-webhook-urls-with-reverse-proxy)
- [Telegram Trigger issues](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/common-issues)
- [Wait](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait)

References reviewed on October 24, 2026. Template-specific requirements were checked locally; the entire guide still needs a clean-install run. No real tokens, keys, or private production URLs are included.
