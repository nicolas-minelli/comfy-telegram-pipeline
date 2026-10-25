# Comfy: graphs used by n8n

Files in `api/` are generated directly from this repository's n8n builders using synthetic job data. They are not old UI exports. Extracting them required no requests to Comfy and generated no video.

## Files

| File | Purpose |
|---|---|
| api/ltx.json | Final 9:16 generation graph |
| api/ltx-16x9.json | Final 16:9 generation graph |
| api/interpolation.json | Final 2x interpolation graph |
| api/upscale.json | Final 9:16 upscale graph, 1088x1920 |
| api/upscale-16x9.json | Final 16:9 upscale graph, 1920x1088 |
| templates/ltx.json | Input template used by Build LTX Request |

At runtime, n8n reads `/files/workflows/ltx.json`. Interpolation and upscale templates remain embedded in their builders. Exporting these examples does not change that behavior or production workflows.

API node IDs are preserved because n8n uses them to update inputs.

## Dynamic values

Examples use `tg-0-1`, `example-first-frame.png`, `tg-0-1-e1`, and `E:/COMFY_OUTPUT/`. These explicitly replace real job, media, and local path values. n8n fills them per job. Example prompts and seeds are synthetic too. Do not submit these files without configuring dependencies and replacing dynamic inputs.

## Processing

LTX uses a 2 MP selector, generates at half of each dimension, runs at 30 FPS, and uses tiled decode at 256. Examples use 6 seconds and seed 1; n8n sets both per request.

Interpolation uses FILM 2x, multiplies FPS, and connects audio to CreateVideo.

Upscale uses VHS_LoadVideoPath, RealESRGAN x2, 8 frames per batch, 60 FPS, CRF18, connected audio, and N8NMoveFinalVideo with run_id and final_basename. The executed graph has no count=90 setting.

VHS processes video chunks and may internally requeue the graph while frames remain. The postprocessing reservation covers the complete sequence. A finished batch is not a finished final clip. Requeue details depend on the installed VideoHelperSuite version; the reference operator reported 1.7.9 without Git metadata.

## Models

| File | Loader | Model filename |
|---|---|---|
| ltx.json | UNETLoader | `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` |
| ltx.json | VAELoader | `ltx-2.5-video-vae-conv-bf16.safetensors` |
| ltx.json | VAELoader | `ltx-2.5-audio-vae-bf16.safetensors` |
| ltx.json | CLIPLoader | `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` |
| interpolation.json | FrameInterpolationModelLoader | `film_net_fp16.safetensors` |
| upscale.json | UpscaleModelLoader | `RealESRGAN_x2plus.pth` |

Weights are excluded. See [model sources and licenses](../docs/MODELS.md) and [reference dependencies](../docs/DEPENDENCIES.md). Exact revisions/checksums are not fully pinned.

## Reproduce the graphs

From the repository root with Node.js:

```sh
node tools/export-runtime-graphs.cjs
```

The script runs only each builder's assembly section in an isolated context with synthetic inputs. It does not execute the scheduler prefix, expose require to the context, or access external services. It checks connections, loader, batch size, audio, dimensions, and finalizer. Output is only the prompt graph; n8n still builds the submission envelope.

This check does not replace real generation testing on another installation.

## Included project custom nodes

- `custom_nodes/n8n_job_control/__init__.py`: matched the installed file, with the personal ID replaced by 0 in the public copy.
- `custom_nodes/n8n_video_finalizer/__init__.py`: same implementation as the installed version.

`E:\AI\media` and `E:\AI\media\final` are configuration examples. Job Control's SHARED_MEDIA_ROOT and the finalizer's FINAL_DIRECTORY must refer to the same media volume, with final inside that root. The Windows directory must correspond to n8n's `/files` mount. Defaults are not secrets.

Configure the Telegram user consistently in Job Control and n8n before installation. Zero is inert. Use `tools/Initialize-Pipeline.ps1`, explained in [the tutorial](../docs/TUTORIAL.md), to prepare correlated local settings. Do not replace configured production plugins with public templates.

Job Control creates or reads `.telegram-ui/comfy-control.key` in the shared volume. Key-generation code is public; the real key file must never enter Git. Endpoints preserve Bearer authentication and the original reservation/job validation rules.
