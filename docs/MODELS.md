# Models: sources and installation

References reviewed on October 24, 2026. Download weights separately; they are not included. These are the exact graph filenames, not a recommendation to replace models in an already working installation.

## Required files

Destinations are relative to Comfy's models directory or its equivalent extra-model-paths root.

| Stage | Destination | File / source |
|---|---|---|
| LTX generation | `models/diffusion_models/` | [ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors) |
| Text encoder | `models/text_encoders/` | [gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors) |
| Video VAE | `models/vae/` | [ltx-2.5-video-vae-conv-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/vae/ltx-2.5-video-vae-conv-bf16.safetensors) |
| Audio VAE | `models/vae/` | [ltx-2.5-audio-vae-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/vae/ltx-2.5-audio-vae-bf16.safetensors) |
| FILM interpolation | `models/frame_interpolation/` | [film_net_fp16.safetensors](https://huggingface.co/Comfy-Org/Frame-Interpolation/blob/main/frame_interpolation/film_net_fp16.safetensors) |
| RealESRGAN x2 upscale | `models/upscale_models/` | [RealESRGAN_x2plus.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth) |

### Source evidence

- The four LTX files are listed in the [official model card](https://huggingface.co/Lightricks/LTX-2.5) and [Comfy integration documentation](https://docs.ltx.io/open-source-model/integration-tools/comfy-ui/). This pipeline uses the conv-bf16 video VAE.
- FILM is hosted in [Comfy-Org/Frame-Interpolation](https://huggingface.co/Comfy-Org/Frame-Interpolation), which documents the frame_interpolation directory. It is a Comfy-packaged weight, not another plugin.
- The RealESRGAN x2 weight comes from the [author's v0.2.1 release](https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.1). The [official inference script](https://github.com/xinntao/Real-ESRGAN/blob/master/inference_realesrgan.py) references the same file URL.

## Download and organization

1. Open the file links. For LTX, sign in to Hugging Face and satisfy any provider access conditions. Public requests for individual LTX file details returned 401 during review; the public model card confirms the names. Avoid untrusted mirrors as a workaround.
2. Download these six files only, preserving names and extensions. Other LTX repository weights are not used here.
3. Place each under the indicated category. For external model storage, configure extra-model-paths with matching categories. Keep weights outside the Git clone.
4. Check Comfy loaders. Models should appear without arbitrary renaming. If you use a subdirectory, update the selected loader name and template consistently.
5. Test a new installation with one short job before enabling a full queue. A matching filename alone does not prove identical content.

Keep the INT8 ConvRot video model, INT8 ConvRot text encoder, and conv-bf16 video VAE. Similar names do not make full BF16 or another quantization interchangeable. The reference deployment's structure and memory behavior were validated with this combination.

## License declarations from sources

| Source | Observed declaration | Reference |
|---|---|---|
| Lightricks/LTX-2.5 | LTX-2.x Community License Agreement in model card | [Model card](https://huggingface.co/Lightricks/LTX-2.5), [license text](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x) |
| Comfy-Org/Frame-Interpolation | Package metadata: mit-and-apache-2.0; multiple model families | [Model card](https://huggingface.co/Comfy-Org/Frame-Interpolation) |
| Original FILM project | Apache-2.0 for source code | [Project license](https://github.com/google-research/frame-interpolation/blob/main/LICENSE) |
| Real-ESRGAN | BSD-3-Clause in project repository | [License](https://github.com/xinntao/Real-ESRGAN/blob/master/LICENSE) |

These are repository declarations, not a substitute for weight-specific terms, component/base-model licenses, or provider access conditions. This pipeline's code license does not relicense external models. No weights are redistributed.

## Integrity

The public FILM file page reports this SHA256:

```text
f226e51375dc839d4b40e5c3d63da560dd1ea1c962364ec78f5adf2d05db05c0
```

Source: [FILM file details](https://huggingface.co/Comfy-Org/Frame-Interpolation/blob/main/frame_interpolation/film_net_fp16.safetensors). This identifies the complete file; it is not the Xet hash shown on that page.

Check a local file with PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'LOCAL_MODEL_PATH'
```

Compare only against a trusted reference for the same file. A local hash without such a reference cannot prove provenance. No weights were downloaded for this review and production hashes were not compared. The other five checksums and exact repository revisions are not pinned; this is a source inventory, not a weight lockfile.

## Repository security

Keep Hugging Face tokens, Telegram tokens, the Job Control Bearer key, n8n credentials, and weights outside Git. Authenticate to Hugging Face locally; do not put tokens in URLs, commands, screenshots, or issues. Links here contain no credentials.
