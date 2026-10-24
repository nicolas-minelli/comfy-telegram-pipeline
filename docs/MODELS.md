# Modelos: fontes e instalação

Referências consultadas em 24/10/2026. Os pesos são baixados separadamente; não fazem parte deste repositório. Estes são os nomes exatos usados nos grafos do pipeline, não uma recomendação para trocar os modelos da instalação já funcionando.

## Arquivos necessários

O destino é relativo à pasta models do Comfy, ou à raiz equivalente configurada por extra-model-paths.

| Etapa | Destino | Arquivo / fonte |
|---|---|---|
| Geração LTX | `models/diffusion_models/` | [ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors) |
| Text encoder | `models/text_encoders/` | [gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors) |
| VAE de vídeo | `models/vae/` | [ltx-2.5-video-vae-conv-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/vae/ltx-2.5-video-vae-conv-bf16.safetensors) |
| VAE de áudio | `models/vae/` | [ltx-2.5-audio-vae-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/blob/main/vae/ltx-2.5-audio-vae-bf16.safetensors) |
| Interpolação FILM | `models/frame_interpolation/` | [film_net_fp16.safetensors](https://huggingface.co/Comfy-Org/Frame-Interpolation/blob/main/frame_interpolation/film_net_fp16.safetensors) |
| Upscale RealESRGAN x2 | `models/upscale_models/` | [RealESRGAN_x2plus.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth) |

### Evidência das fontes

- Os quatro arquivos LTX estão listados no [model card oficial](https://huggingface.co/Lightricks/LTX-2.5) e nas referências de [integração com Comfy](https://docs.ltx.io/open-source-model/integration-tools/comfy-ui/). O VAE usado aqui é a variante conv-bf16.
- O FILM está no repositório [Comfy-Org/Frame-Interpolation](https://huggingface.co/Comfy-Org/Frame-Interpolation), que documenta a pasta frame_interpolation. É um peso reempacotado para Comfy, não um plugin adicional.
- O peso RealESRGAN x2 é publicado pela [release v0.2.1 do autor](https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.1). O próprio [script de inferência oficial](https://github.com/xinntao/Real-ESRGAN/blob/master/inference_realesrgan.py) referencia a URL desse arquivo.

## Download e organização

1. Abra os links dos arquivos. Para LTX, entre na sua conta Hugging Face e cumpra as condições de acesso apresentadas pelo provedor, se solicitado. A consulta pública aos detalhes individuais desses quatro pesos retornou 401 durante esta revisão; o model card público confirma seus nomes. Não contorne a restrição com espelhos desconhecidos.
2. Baixe apenas os seis arquivos relacionados nesta página. Preserve nomes e extensões. A lista do repositório LTX tem outros pesos que não são utilizados por este pipeline.
3. Coloque cada arquivo na categoria de pasta indicada. Para modelos externos à instalação, configure extra-model-paths com as mesmas categorias. Não copie pesos para dentro do clone Git.
4. Confira os loaders do Comfy: os nomes devem aparecer sem renomear arbitrariamente os pesos. Se um modelo estiver em subpasta, ajuste o nome selecionado e o template de maneira consistente.
5. Valide uma instalação nova com um único job curto antes de habilitar a fila completa. Baixar o mesmo nome de arquivo não comprova, por si só, que o conteúdo local é idêntico ao publicado.

O modelo de vídeo permanece INT8 ConvRot; o text encoder também permanece INT8 ConvRot; o VAE de vídeo permanece conv-bf16. Não substitua por BF16 completo ou outra quantização só por terem nomes parecidos. A estrutura e a memória disponível da implantação original foram validadas com a combinação documentada.

## Licenças declaradas pelas fontes

| Fonte | Declaração observada | Referência |
|---|---|---|
| Lightricks/LTX-2.5 | LTX-2.x Community License Agreement no model card | [Model card](https://huggingface.co/Lightricks/LTX-2.5), [texto da licença](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x) |
| Comfy-Org/Frame-Interpolation | Metadados do pacote: mit-and-apache-2.0; inclui mais de uma família de modelos | [Model card](https://huggingface.co/Comfy-Org/Frame-Interpolation) |
| Projeto original FILM | Apache-2.0 no código de origem | [Licença do projeto](https://github.com/google-research/frame-interpolation/blob/main/LICENSE) |
| Real-ESRGAN | BSD-3-Clause no repositório do projeto | [Licença](https://github.com/xinntao/Real-ESRGAN/blob/master/LICENSE) |

Esta tabela identifica as declarações dos repositórios consultados; não substitui os termos específicos dos pesos, de seus componentes/base models ou do acesso solicitado pelo provedor. A licença do código deste pipeline não relicencia os modelos externos. Não há redistribuição de pesos nesta entrega.

## Integridade

A página pública do FILM informa SHA256:

```text
f226e51375dc839d4b40e5c3d63da560dd1ea1c962364ec78f5adf2d05db05c0
```

Fonte: [detalhes do arquivo FILM](https://huggingface.co/Comfy-Org/Frame-Interpolation/blob/main/frame_interpolation/film_net_fp16.safetensors). Esse SHA256 identifica o arquivo completo; não confundir com o Xet hash mostrado na mesma página.

Para verificar um arquivo local no PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'CAMINHO_LOCAL_DO_MODELO'
```

Só compare com uma referência confiável do arquivo correspondente. Gerar um hash local sem referência não comprova a origem. Não foram baixados os pesos para esta revisão e não foram comparados os hashes da instalação de produção. Os outros cinco checksums e as revisões exatas dos repositórios ainda não estão fixados; este documento é um inventário de fontes, não um lockfile de pesos.

## Segurança do repositório

Tokens Hugging Face, tokens Telegram, chave Bearer do Job Control, credenciais n8n e pesos devem ficar fora do Git. A autenticação no Hugging Face deve ocorrer localmente; não inclua tokens em URLs, exemplos de comando, capturas ou issues. Os links desta página não contêm credenciais.
