# Comfy: grafos usados pelo n8n

Os arquivos em api/ são gerados diretamente pelos builders do workflow n8n incluído no repositório, com dados fictícios de um job. Não são os exports antigos da interface. Não foram feitas requisições ao Comfy nem gerado vídeo para extraí-los.

## Arquivos

| Arquivo | Uso |
|---|---|
| api/ltx.json | Grafo final de geração 9:16 |
| api/ltx-16x9.json | Grafo final de geração 16:9 |
| api/interpolation.json | Grafo final de interpolação 2x |
| api/upscale.json | Grafo final de upscale 9:16, 1088x1920 |
| api/upscale-16x9.json | Grafo final de upscale 16:9, 1920x1088 |
| templates/ltx.json | Template de entrada usado por Build LTX Request |

Em produção, o n8n lê o template LTX de /files/workflows/ltx.json. Os templates de interpolação e upscale continuam embutidos em seus builders. A geração destes arquivos não alterou esse comportamento nem os workflows em produção.

Os IDs dos nodes API são preservados, pois o n8n usa esses IDs para alterar os inputs.

## Dados dinâmicos

Os exemplos usam tg-0-1, example-first-frame.png, tg-0-1-e1 e E:/COMFY_OUTPUT/. São substitutos explícitos para job, mídia e caminho locais. O n8n preenche os valores reais a cada job. Prompts e seed de exemplo também foram substituídos; não são dados de produção. Nenhum arquivo deve ser submetido sem preencher seus campos dinâmicos e configurar as dependências.

## Processamento

LTX: selector 2MP e geração em metade de cada dimensão, 30FPS e decode tiled 256. Os exemplos usam 6 segundos e seed 1; o n8n define duração e seed por pedido.

Interpolação: FILM 2x, FPS multiplicado e áudio conectado ao CreateVideo.

Upscale: VHS_LoadVideoPath, RealESRGAN x2, 8 frames por batch, 60FPS, CRF18, áudio conectado e N8NMoveFinalVideo com run_id e final_basename. Não há count=90 no grafo executado.

O VHS processa porções do vídeo e pode reenfileirar internamente o grafo enquanto há frames. A reserva de pós-processamento cobre a sequência inteira. A conclusão de um batch não significa que o arquivo final esteja pronto. O comportamento exato dos requeues depende da versão instalada do VideoHelperSuite, ainda a inventariar.

## Modelos

| Arquivo | Loader | Nome do modelo |
|---|---|---|
| ltx.json | UNETLoader | `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` |
| ltx.json | VAELoader | `ltx-2.5-video-vae-conv-bf16.safetensors` |
| ltx.json | VAELoader | `ltx-2.5-audio-vae-bf16.safetensors` |
| ltx.json | CLIPLoader | `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` |
| interpolation.json | FrameInterpolationModelLoader | `film_net_fp16.safetensors` |
| upscale.json | UpscaleModelLoader | `RealESRGAN_x2plus.pth` |


Os pesos não fazem parte do repositório. Nomes extraídos dos exports atuais. Fontes, licenças, checksums e versões instaladas ainda serão documentados antes da distribuição completa.

## Reprodução dos grafos

Na raiz do repositório, com Node.js:

```sh
node tools/export-runtime-graphs.cjs
```

O script executa somente o trecho de montagem de cada builder em um contexto isolado e com dados sintéticos. Não executa o prefixo do scheduler, não fornece require ao contexto e não acessa serviços externos. Verifica conexões, loader, batch, áudio, dimensões e finalizador. A saída é somente o grafo prompt; o envelope de submissão continua responsabilidade do n8n.

Essa verificação não substitui um teste real de geração em outro ambiente.

## Custom nodes próprios incluídos

- custom_nodes/n8n_job_control/__init__.py: arquivo confirmado contra a instalação, com o ID pessoal substituído por 0 na cópia pública.
- custom_nodes/n8n_video_finalizer/__init__.py: mesmo conteúdo da versão instalada.

Os diretórios E:\AI\media e E:\AI\media\final são exemplos de configuração. SHARED_MEDIA_ROOT no Job Control e FINAL_DIRECTORY no finalizador devem apontar para o mesmo volume de mídia: final deve ficar dentro desse volume. O diretório Windows deve corresponder ao /files do container n8n. Os defaults não são segredos.

Antes de instalar, configure o usuário Telegram de forma consistente nas validações do Job Control e nos workflows n8n. O valor 0 é inerte. Esta entrega ainda não centraliza essa configuração. Não substitua seus custom nodes de produção pelos templates limpos.

O Job Control cria ou lê .telegram-ui/comfy-control.key no volume compartilhado. O código de geração da chave é público; o arquivo real da chave jamais entra no repositório. Os endpoints mantêm autenticação Bearer e as validações originais de reserva/job.
