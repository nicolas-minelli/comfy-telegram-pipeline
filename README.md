# Comfy Telegram Pipeline

Automação local de geração e pós-processamento de vídeos com Telegram, n8n e Comfy.

Telegram → first frame e parâmetros → fila de geração LTX → prévia e aprovação → interpolação → upscale → arquivo final e notificação.

O supervisor organiza a recuperação da fila e o reenvio de alertas persistentes. O Error Handler registra incidentes e trata a reserva conforme a evidência disponível, sem reenviar automaticamente um POST de geração cujo resultado seja incerto.

## Estado desta entrega

Este snapshot contém somente os seis exports preparados como templates para revisão pública. Não é ainda uma instalação completa: scripts de operação e documentação completa serão integrados separadamente antes da publicação do projeto.

Os exports de produção recebidos foram usados como referência. A limpeza não foi aplicada à instalação em produção.

## Arquivos

- `workflows/ltx-generation.template.json`: geração, aprovação, interpolação e upscale.
- `workflows/telegram-bot.template.json`: interface do bot e controles de jobs.
- `workflows/automatic-recovery.template.json`: supervisor, incluindo a rota de alertas da v2.
- `workflows/error-handler.template.json`: handler de incidentes e notificações.
- `workflows/manual-recovery.template.json`: liberação manual de emergência, sem reenvio.
- `comfy/api/`: grafos de execução extraídos dos builders n8n; consulte `comfy/README.md`.
- `tests/fixtures/t5-controlled-failure.template.json`: teste que rejeita intencionalmente a submissão, usando um tipo de node inexistente. Não deve ser usado como workflow normal.

## Templates desativados

Todos os workflows estão desativados. Os vínculos a credenciais, IDs de webhook, IDs de workflows instalados, tags, metadados da instância e associações ao Error Workflow foram retirados. Os IDs dos nodes foram regenerados de modo determinístico.

As opções que exigem autenticação foram preservadas. Credenciais precisam ser selecionadas localmente depois da importação. Não desabilite a autenticação para contornar a falta de configuração.

O ID autorizado do Telegram foi substituído por `0` em todas as referências correlatas, inclusive validações de request_id e caminhos de rascunhos. É um valor inerte, não uma configuração operacional. A futura configuração deverá atualizar essas referências de forma consistente em todos os componentes; estes arquivos não são uma atualização para importar em produção.

O domínio pessoal foi substituído por `https://n8n.example.invalid`. As URLs locais `127.0.0.1` e `host.docker.internal`, bem como caminhos genéricos do container, foram mantidos porque descrevem a arquitetura, não credenciais.

## Segurança

Nunca versione chaves, tokens, senhas, volumes do n8n, backups da instalação ou exports de produção. Use credenciais locais do n8n e arquivos de segredo fora do repositório. A conta autorizada e os diretórios de mídia também precisam de configuração local consistente com os custom nodes.

O `.gitignore` é uma proteção contra inclusão acidental; não é um scanner e não remove arquivos já versionados. A verificação deste snapshot tem limites, descritos em `EXPORT-REVIEW.md`.

## Validação

Seis JSONs n8n, 380 nodes: parse JSON, integridade das conexões e compilação sintática dos blocos jsCode aprovados. A limpeza removeu 31 vínculos de credenciais e 86 IDs de webhook. Não foi feito teste de execução dos templates limpos em n8n ou na GPU. Os resultados de produção anteriores não equivalem a validar estes templates após a limpeza.


## Grafos Comfy

Os arquivos em comfy/api são produzidos pelos builders atuais do n8n para as duas proporções. Execute node tools/export-runtime-graphs.cjs para reproduzi-los. Inputs privados foram substituídos por dados sintéticos. A integração ainda não é uma instalação completa, pois faltam os scripts operacionais e a configuração completa.

Os custom nodes próprios confirmados estão em comfy/custom_nodes. Configure-os conforme comfy/README.md. Os arquivos de chave reais e dados do scheduler não são incluídos.
