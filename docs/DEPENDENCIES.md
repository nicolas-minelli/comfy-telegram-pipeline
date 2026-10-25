# Dependencies and reference environment

Inventory confirmed by the production operator on October 24, 2026. This records observed versions and classes; it is not a complete lockfile or a promise of identical behavior on every machine.

## Required components

| Component | Reference | Evidence |
|---|---|---|
| Comfy | 0.42.3 | Latest supplied log; required classes checked through object_info |
| ComfyUI-VideoHelperSuite | v1.7.9 | Operator-reported version; installation has no Git metadata |
| n8n_job_control | Protocol 2, plugin 2026.10.24-aspect-1 | Installed file confirmed and included under comfy/custom_nodes |
| n8n_video_finalizer | Included in this repository | Installed file confirmed; supports final_basename |
| n8n | 2.43.7, self-hosted in Docker | Latest supplied execution results |
| Node.js | Required for offline graph export | Local version not yet inventoried |

VideoHelperSuite source: https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite

The v1.7.9 reference identifies the reported installed version, not a verified Git tag. Do not assume `git checkout v1.7.9` will work. For a new installation, select the matching version in Comfy Manager when available. The exact commit remains unknown.

An earlier hash returned identically for every plugin directory was discarded: Git had resolved a parent repository rather than each plugin's own repository.

## Graph dependencies

All 39 distinct API graph classes were found in object_info on the working installation.

| Source | Classes |
|---|---|
| Native Comfy, modules nodes/comfy_extras | 35 classes below |
| VideoHelperSuite | VHS_BatchManager, VHS_LoadVideoPath, VHS_VideoCombine |
| Project finalizer | N8NMoveFinalVideo |

Job Control provides HTTP endpoints rather than a processing node. It is required even though it has no corresponding class in the graph.

Confirmed native classes:

- `CLIPLoader`
- `CLIPTextEncode`
- `ComfyMathExpression`
- `ComfySwitchNode`
- `CreateVideo`
- `EmptyLTXVLatentVideo`
- `FrameInterpolate`
- `FrameInterpolationModelLoader`
- `GetVideoComponents`
- `ImageScale`
- `ImageUpscaleWithModel`
- `KSamplerSelect`
- `LTXVAudioVAEDecode`
- `LTXVConcatAVLatent`
- `LTXVConditioning`
- `LTXVDualCFGGuider`
- `LTXVEmptyLatentAudio`
- `LTXVImgToVideoInplace`
- `LTXVPreprocess`
- `LTXVSeparateAVLatent`
- `LoadImage`
- `LoadVideo`
- `ManualSigmas`
- `PrimitiveBoolean`
- `PrimitiveInt`
- `PrimitiveStringMultiline`
- `RandomNoise`
- `ResizeImageMaskNode`
- `ResolutionSelector`
- `SamplerCustomAdvanced`
- `SaveVideo`
- `UNETLoader`
- `UpscaleModelLoader`
- `VAEDecodeTiled`
- `VAELoader`

ComfyMathExpression, ComfySwitchNode, ResolutionSelector, and FILM interpolation nodes are native in this installation. Do not install extra plugins based only on these names.

AnimateDiff Evolved, Easy Use, KJNodes, and rgthree are not required by these pipeline graphs. Other personal workflows may still depend on them.

## Models

Weights are not distributed. These exact names come from the supplied exports and must be available under their corresponding folder types, including when using extra-model-paths.

| Filename | Comfy folder type |
|---|---|
| ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors | diffusion_models |
| gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors | text_encoders |
| ltx-2.5-video-vae-conv-bf16.safetensors | vae |
| ltx-2.5-audio-vae-bf16.safetensors | vae |
| film_net_fp16.safetensors | frame_interpolation |
| RealESRGAN_x2plus.pth | upscale_models |

Download sources and license declarations are in [MODELS.md](MODELS.md). Not all checksums or exact weight revisions are pinned. This inventory does not imply permission to redistribute weights under this project's MIT license.

## Reported environment

Windows; Python 3.13.12; PyTorch 2.12.0+rocm7.14.0; AMD Radeon RX 9060 XT with 16 GB VRAM; 16 GB system RAM. This is the operator's reference environment, not a universal minimum requirement. Do not install this AMD build on NVIDIA hardware merely to match the document.

Video processing depends on libraries/encoders available to Comfy and VideoHelperSuite. The effective FFmpeg path and version have not been inventoried.

Tailscale provides remote access in the reference deployment. Telegram requires a locally configured bot. Tokens, keys, volumes, and private network settings are not dependencies to commit.

## Offline repository verification

```sh
node tools/export-runtime-graphs.cjs
python -B tests/test_custom_node_contracts.py
python -B tests/test_local_configuration.py
```

The exporter uses synthetic inputs and current n8n builders. Tests verify public ID scope, finalizer contracts, and local configuration using temporary files. They neither submit GPU tasks nor send messages, and do not replace end-to-end installation testing.

## Before claiming reproducible installation

- Complete weight checksums and exact revisions; see MODELS.md for sources.
- Validate assisted setup in TUTORIAL.md and SETUP.md on a clean installation.
- Inventory Node.js and effective encoders.
- Test configured templates in an isolated environment.
- Preserve the MIT notice for original project material and separate notices/terms for dependencies.

## Preview pinning status

| Component | What is recorded | Still required |
|---|---|---|
| n8n | Image tag 2.43.7 | Record the actual deployed image digest for a reproducible deployment |
| Comfy | Operator-reported 0.42.3 | Exact source commit/distribution build |
| VideoHelperSuite | Operator-reported 1.7.9 | Exact upstream commit, if recoverable; do not use a parent repository hash |
| Project custom nodes | Source included in the release | Git tag/commit identifies the distributed source |
| Python / PyTorch | Reported 3.13.12 / 2.12.0+rocm7.14.0 | Complete environment/encoder inventory |
| Six model weights | Exact filenames and sources | Local checksums, trusted-reference comparison, and exact source revisions |

These gaps are disclosed in v1.0.0-preview.1. They do not become verified merely because a release tag exists. Keep any private runtime inventory outside the repository until reviewed and sanitized.
