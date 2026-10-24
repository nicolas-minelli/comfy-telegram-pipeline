# Dependências e ambiente de referência

Inventário confirmado em 24/10/2026 pelo operador da instalação de produção. Este documento registra o ambiente e as classes observadas; não é um lockfile completo nem uma promessa de reprodução idêntica em qualquer hardware.

## Componentes necessários

| Componente | Referência | Evidência |
|---|---|---|
| Comfy | 0.42.3 | Último log fornecido; classes necessárias confirmadas via object_info |
| ComfyUI-VideoHelperSuite | v1.7.9 | Versão informada pelo operador; instalação sem metadados Git |
| n8n_job_control | protocolo 2, plugin 2026.10.24-aspect-1 | Arquivo instalado confirmado e incluído em comfy/custom_nodes |
| n8n_video_finalizer | Incluído neste repositório | Arquivo instalado confirmado; suporta final_basename |
| n8n | 2.43.7, self-hosted em Docker | Últimos resultados de execução fornecidos |
| Node.js | Necessário para o script offline de exportação | Versão local ainda não inventariada |

Fonte do VideoHelperSuite: https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite

A referência v1.7.9 identifica a versão instalada informada, não um tag Git verificado neste levantamento. Não usar git checkout v1.7.9 presumindo que esse tag exista. Para uma nova instalação, selecionar a versão correspondente no Comfy Manager quando disponível. O commit exato permanece desconhecido.

O hash inicialmente retornado igualmente para todos os diretórios foi descartado: o Git encontrou um repositório superior, não o repositório próprio de cada plugin.

## Dependências dos grafos

As 39 classes distintas dos grafos API foram consultadas em object_info na instalação em funcionamento. Nenhuma apareceu como ausente.

| Origem | Classes |
|---|---|
| Comfy nativo, modules nodes/comfy_extras | 35 classes, listadas abaixo |
| VideoHelperSuite | VHS_BatchManager, VHS_LoadVideoPath, VHS_VideoCombine |
| Finalizador próprio | N8NMoveFinalVideo |

O Job Control usa endpoints HTTP próprios, não um node de processamento: por isso ele é obrigatório mesmo sem uma classe correspondente no grafo.

Classes nativas confirmadas:

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

ComfyMathExpression, ComfySwitchNode, ResolutionSelector e os nodes FILM de interpolação são nativos nesta instalação. Não instalar plugins adicionais só por causa desses nomes.

AnimateDiff Evolved, Easy Use, KJNodes e rgthree não são necessários aos grafos atuais deste pipeline. Isso não avalia outros workflows pessoais da mesma instalação.

## Modelos

Os pesos não são distribuídos no repositório. Os nomes abaixo foram extraídos dos exports fornecidos. Cada arquivo deve estar disponível no tipo de pasta correspondente, inclusive quando configurado por extra-model-paths.

| Arquivo | Tipo de pasta do Comfy |
|---|---|
| ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors | diffusion_models |
| gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors | text_encoders |
| ltx-2.5-video-vae-conv-bf16.safetensors | vae |
| ltx-2.5-audio-vae-bf16.safetensors | vae |
| film_net_fp16.safetensors | frame_interpolation |
| RealESRGAN_x2plus.pth | upscale_models |

Fontes de download e declarações de licença estão em [MODELS.md](MODELS.md). Os checksums completos e as revisões exatas dos pesos ainda não estão todos fixados. Este inventário não presume que os pesos possam ser redistribuídos sob a licença do projeto.

## Ambiente reportado

Windows; Python 3.13.12; PyTorch 2.12.0+rocm7.14.0; GPU AMD Radeon RX 9060 XT com 16GB de VRAM; 16GB de RAM. Referência extraída dos logs do operador, não requisito mínimo universal. Não instalar esse build AMD em uma GPU NVIDIA por seguir este documento.

O runtime de vídeo depende das bibliotecas/encoders disponibilizados pelo Comfy e pelo VideoHelperSuite. Caminho e versão efetiva do FFmpeg ainda não foram inventariados.

Tailscale é usado no acesso remoto desta implantação. Telegram exige um bot configurado localmente. Tokens, chaves, volumes e configurações privadas de rede não são dependências a versionar.

## Verificação offline do repositório

```sh
node tools/export-runtime-graphs.cjs
python -B tests/test_custom_node_contracts.py
```

O primeiro comando gera os grafos com inputs fictícios usando os builders atuais do n8n. O segundo testa o escopo dos IDs públicos de exemplo e o contrato dos grafos de upscale com o finalizador, usando arquivos temporários. Nenhum deles submete tarefas à GPU ou envia mensagens. Não substituem uma validação da instalação completa.

## Antes de apresentar como instalação reproduzível

- Completar checksums e revisões exatas dos pesos; fontes e declarações observadas estão em MODELS.md.
- Documentar a configuração consistente de usuário, caminhos, credenciais, Docker, webhooks e Error Workflow.
- Inventariar Node.js e os encoders efetivos.
- Testar os templates após configuração em ambiente separado.
- Escolher e incluir a licença do código próprio, mantendo as licenças das dependências separadas.
