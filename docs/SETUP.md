# Configuração do Comfy Telegram Pipeline

Guia dos templates publicados, baseado na instalação Windows + Docker Desktop + n8n 2.43.7 reportada pelo operador. Leia também [DEPENDENCIES.md](DEPENDENCIES.md) e [MODELS.md](MODELS.md).

## 1. Escopo e isolamento

Este guia configura uma instalação nova a partir dos templates. Não é uma instrução para substituir a produção existente por arquivos sanitizados. Os testes reais anteriores validaram a instalação privada; ainda não foi realizado um teste completo de instalação limpa desses templates públicos.

Os templates contêm ID Telegram `0`, domínio `n8n.example.invalid` e caminhos de exemplo. Não devem ser ativados antes da configuração. O projeto ainda exige edição manual desses valores; não há configurador centralizado nesta entrega.

Mantenha o clone Git separado dos dados operacionais. Uma instalação de teste deve ter bot, banco/volume n8n e diretórios de mídia próprios. Não conecte dois supervisors ativos ao mesmo estado do scheduler, nem duas instâncias do Comfy ao mesmo volume de integração. Se usar duas instalações simultâneas na mesma máquina, configure também portas, URLs e instâncias Comfy independentes.

Não use o bot de produção para testar outro Telegram Trigger: o Telegram registra somente um webhook por bot e um teste pode substituir o webhook que já funciona.

## 2. Arquitetura e caminhos

Telegram → bot n8n → submissão autenticada → geração Comfy → prévia e aprovação → interpolação → upscale por batches → finalizador → notificação.

| Dado | Windows, exemplo | Container n8n | Acesso |
|---|---|---|---|
| Mídia e estado da integração | E:/AI/media | /files | Leitura e escrita |
| Saída do Comfy | OUTPUT_REAL_DO_COMFY | /comfy-output | Somente leitura pelo n8n |
| Banco, credenciais e binários n8n | Volume Docker dedicado | /home/node/.n8n | Persistente |

O diretório real de saída precisa coincidir com o usado pelo Comfy e com `windows_output_root` no node Initialize Post Processing. O endereço Windows não é um caminho de container; /comfy-output não é um endereço que o Comfy Windows possa abrir.

No volume de mídia:

- `current/`: imagens recebidas pelo bot, incluindo first frames enviados pelo Telegram.
- `workflows/ltx.json`: template API de entrada do LTX.
- `final/`: clipes finais e recibos.
- `.telegram-ui/`: rascunhos, scheduler, incidentes, recibos de submissão e chave da integração, gerados durante o uso.

Crie somente as pastas públicas necessárias. Não gere um control.json vazio por conta própria nem copie estado de produção para testar. O código inicializa seus arquivos conforme necessário.

## 3. Comfy e custom nodes

1. Prepare uma instalação Comfy compatível com o inventário de nodes em DEPENDENCIES.md e disponibilize os seis modelos de MODELS.md.
2. Instale o VideoHelperSuite na versão documentada. O commit não foi identificado; não invente um tag Git a partir da versão do Manager.
3. Copie as duas pastas de `comfy/custom_nodes/` para `custom_nodes/` da instalação escolhida, preservando seus nomes.
4. No Job Control, configure `SHARED_MEDIA_ROOT` para a raiz Windows montada como /files. O default de exemplo é E:/AI/media.
5. No finalizador, configure `FINAL_DIRECTORY` como a subpasta final dessa mesma raiz. A recuperação do Job Control procura os clipes em SHARED_MEDIA_ROOT/final.
6. Configure o ID Telegram conforme a seção seguinte antes de carregar o Job Control da nova instalação.
7. Inicie o backend Comfy e confirme os logs de importação dos custom nodes. Para essa automação, não é necessário manter a janela Desktop aberta.

O processo Comfy deve continuar vivo após desconectar uma sessão SSH. Na implantação original isso é feito pelo controle via tarefa agendada; os scripts dessa operação ainda não fazem parte deste guia. Não confunda um processo iniciado na sessão SSH com um serviço persistente configurado.

O backend deve ser alcançável pelo container em `http://host.docker.internal:8188`, ou no endereço/porta efetivamente configurados. Se ele escutar apenas na interface loopback do Windows, verifique a conectividade pelo container antes de alterar firewall ou interfaces. Ao habilitar escuta em outra interface, limite o acesso necessário no firewall; não publique a porta Comfy na Internet.

### Chave do Job Control

Ao carregar, o plugin gera ou lê `.telegram-ui/comfy-control.key` na raiz compartilhada. O arquivo deve ser o mesmo visto em /files/.telegram-ui/comfy-control.key pelo n8n. Não recrie a chave a cada inicialização e não a coloque no Git.

A chave é usada como Bearer nos endpoints /n8n/jobs/* e como X-N8N-Recovery-Key no canal interno de recuperação. Ela não substitui a credencial Header Auth do webhook /start.

## 4. ID Telegram: configure todas as referências correlatas

O template atual atende um usuário em conversa privada. Configure user ID e chat ID correspondentes à mesma conversa autorizada; grupos/múltiplos usuários não foram validados neste projeto.

Na cópia local de implantação, substitua de forma consistente:

| Marcador | Local / uso |
|---|---|
| ALLOWED_CHAT_ID = '0' e ALLOWED_USER_ID = '0' | Authorize Telegram Update no bot |
| tg-0- | Regex de request_id, prefixos e glob de jobs nos Codes n8n e no Job Control Python |
| /0-0.json | Caminho do rascunho em Restore Rejected Draft |
| telegram_chat_id: '0' | Initialize Post Processing |
| chat_id:'0', chat_id: '0' e parâmetros chatId com valor 0 | Destinatários do handler, supervisor e demais notificações |

As funções comuns estão embutidas em vários nodes: configurar só o primeiro node do bot deixa recuperação, limpeza e alertas inconsistentes. Inspecione todos os cinco workflows normais e o Job Control. O fixture T5, se utilizado, também deve receber os mesmos ajustes na cópia de teste.

Não faça uma substituição global do caractere `0`: isso corromperia parâmetros numéricos, índices de saídas, FPS e outras validações. Use os marcadores completos e confirme as ocorrências antes de substituir. Mantenha a cópia configurada fora do Git, por exemplo em um diretório local production/ ignorado. Não use um ID fictício de outra pessoa para publicar exemplos.

## 5. Container n8n: requisitos de configuração

Mantenha n8n em uma única instância, com filesystem binary mode. A fila de jobs deste projeto é própria e não é o queue mode distribuído do n8n. Não adicionar Redis, múltiplos workers ou réplicas como se fossem equivalentes: os locks e reservas atuais dependem do contexto de execução configurado.

Requisitos a verificar na configuração local Docker, sem substituir um compose de produção que já funciona:

- Volume persistente em /home/node/.n8n para banco, configurações, credenciais e binários. Se houver N8N_ENCRYPTION_KEY explicitamente configurada, preservar seu valor no ciclo de backup/restauração, sem publicá-lo.
- Bind mount da raiz de mídia em /files com escrita e saída Comfy em /comfy-output somente leitura.
- `N8N_DEFAULT_BINARY_DATA_MODE=filesystem` para não manter clipes grandes inteiros no modo binário de memória. Isso não elimina todo o consumo de RAM dos nodes.
- `N8N_RESTRICT_FILE_ACCESS_TO=/files;/comfy-output` para os nodes de arquivo, respeitando a sintaxe de lista separada por ponto e vírgula. Essa variável não deve ser tratada como sandbox universal para require('fs').
- `NODE_FUNCTION_ALLOW_BUILTIN=fs` no runtime que efetivamente executa os Code nodes. Não é necessário liberar todos os módulos ou pacotes npm externos para estes templates.
- TZ e GENERIC_TIMEZONE coerentes com o operador, por exemplo America/Sao_Paulo.
- Porta HTTP do n8n acessível ao proxy local, sem uma publicação direta desnecessária na rede externa. Um exemplo de bind local é 127.0.0.1:5678:5678 quando o proxy roda no host.
- Uma política de persistência e backup que mantenha as execuções em espera e os arquivos de estado necessários à retomada.

### Code nodes, runners e /proc

Os Codes deste projeto usam o módulo fs, arquivos em /files e leituras de /proc/sys/kernel/random/boot_id e /proc/1/stat para construir um namespace de mutex por encarnação do container.

Se houver task runners externos, a permissão de módulos deve estar na configuração efetiva dos runners; definir a variável apenas no container principal pode não bastar. Também é necessário validar volumes, permissões e o significado do namespace /proc no executor. Uma mudança de arquitetura dos runners exige rever a estratégia de locks, não apenas copiar uma variável de ambiente.

Este guia não migra uma implantação funcionando para runners externos nem fornece um compose substituto presumidamente equivalente. A topologia atual é uma premissa a validar antes dessa mudança.

### Endereços internos

Na topologia de um container n8n:

- Comfy do host: http://host.docker.internal:8188.
- Bot → geração e supervisor → geração: http://127.0.0.1:5678/webhook/start.
- Wake de recuperação: http://127.0.0.1:5678/webhook/video-queue-reconcile.

Se mudar portas ou topologia, ajuste todos os HTTP Request correspondentes. Não troque URLs internas por um endpoint público só para resolver conectividade.

## 6. Importe os workflows sem publicar

Importe os cinco templates normais em workflows novos:

1. Error Handler.
2. LTX Generation.
3. Automatic Recovery.
4. Telegram Bot.
5. Manual Recovery, usado somente por execução manual em emergência.

Não publique T5 como workflow normal. Uma pasta organizacional na interface n8n não altera os IDs dos workflows movidos, mas a importação em outra instalação pode gerar novos IDs.

Copie `comfy/templates/ltx.json` para a pasta de mídia `workflows/ltx.json`. Esse é o arquivo lido por Read Workflow LTX. Os grafos em comfy/api são exemplos de requests finais com inputs sintéticos; a interpolação e o upscale operacionais continuam montados pelos builders embutidos no n8n.

Configure também:

- **Initialize Post Processing:** windows_output_root, container_output_root e telegram_chat_id. Os caminhos devem coincidir com os mounts e a saída do Comfy.
- **Send Review Link:** substitua https://n8n.example.invalid/ pela base HTTPS privada usada pelo telefone para abrir o formulário. Preserve o caminho e a query assinada de resumeFormUrl; não remova a assinatura nem gere uma barra duplicada.
- Demais HTTP Requests: porta e endereço do backend, se diferentes do padrão.
- Todos os nodes com credencial sem seleção: vincule as credenciais locais conforme a próxima seção.

Não renomeie nodes por estética durante a configuração: há referências por nome nas expressões e Codes.

## 7. Credenciais: não confundir as três funções

| Função | Onde configurar | Conteúdo |
|---|---|---|
| Telegram | Telegram Trigger, nodes de mensagem, download e callback, inclusive handler e supervisor | Credencial Telegram local do bot dessa instalação |
| Entrada LTX | Receive Request, Start Video Workflow e Resume Video Workflow | Mesma credencial Header Auth, por exemplo nome LTX Start Auth, header X-LTX-Token e valor aleatório local |
| Integração Comfy e recuperação | Headers já expressos a partir de /files/.telegram-ui/comfy-control.key | Bearer para /n8n/jobs/* e X-N8N-Recovery-Key no wake/retomada |

No Receive Request, mantenha Authentication=Header Auth. Nos dois HTTP Requests que chamam /start, selecione Generic Credential Type → Header Auth → a mesma credencial. No Resume Video Workflow, mantenha também X-N8N-Recovery-Key: ele é adicional, não substituto de X-LTX-Token.

O wake interno já valida X-N8N-Recovery-Key no Code de autorização. Não acrescente por engano um header estático que fique diferente do arquivo de chave.

Selecione o Error Handler importado em Settings → Error Workflow no principal, bot e supervisor. Não configure o handler para chamar a si próprio. O Error Trigger não precisa ser publicado como um trigger agendado. Testes do handler devem provocar uma falha em uma execução automática real; um teste manual no editor não equivale a essa condição.

O Manual Recovery permanece sem publicação automática. Não habilite sua confirmação nem preencha uma execução por padrão: é uma ferramenta de emergência, sem reenvio de GPU.

## 8. HTTPS, Telegram e aprovação privada

A implantação original separa duas superfícies:

- Endpoint HTTPS público que recebe somente os eventos do Telegram Trigger, por um proxy com rota/método explícitos.
- Interface e formulários privados acessados pelo telefone via Tailscale.

No seu proxy, permita no caminho público somente o POST da URL de produção efetiva do Telegram Trigger importado. A URL possui um identificador próprio dessa instalação. Não reutilize IDs de webhook do autor e não exponha genericamente /webhook/*, /webhook/start, o wake interno, a UI ou /n8n/jobs/*.

O n8n 2.43.7 está depois da mudança documentada para `N8N_WEBHOOK_URL`, que substitui a antiga WEBHOOK_URL. Em configuração nova, consulte a documentação da versão e defina a base pública HTTPS correta. Se a produção já funciona com a variável antiga, não migre incidentalmente só para seguir este guia; a mudança precisa de uma validação separada do Telegram e dos formulários.

Configure N8N_EDITOR_BASE_URL de acordo com a base privada da interface e N8N_PROXY_HOPS conforme o número real de proxies confiáveis. Não copie um número de hops sem conferir o caminho da requisição. O último proxy deve passar os headers encaminhados adequados.

Depois de importar, confira no próprio Telegram Trigger a URL de produção registrada e permita exatamente essa rota no proxy. O formulário do Wait usa URL por execução e não o endpoint de entrada do bot. O telefone precisa alcançar a base privada configurada em Send Review Link para aprovar.

Os IDs de usuário/chat validados no primeiro Code autorizam os eventos que chegam ao workflow; isso não deve ser apresentado como prova de autenticidade criptográfica de um POST recebido pela Internet. A proteção do recebimento no proxy/trigger deve ser validada na implantação. Não declare o endpoint seguro somente porque o JSON contém o ID autorizado.

Não altere as regras atuais de Funnel/Serve da máquina para executar um exemplo de documentação. A configuração do proxy deve ser feita para a instalação correspondente, com os caminhos gerados nela.

## 9. Pré-verificação e ativação

Antes de publicar o bot, confirme:

1. Mesmo diretório de mídia visto no Windows e em /files; chave existente sem exibir seu conteúdo.
2. GET /queue responde no endereço visto pelo container.
3. GET /n8n/jobs/health responde com Authorization Bearer local e informa protocolo 2, plugin esperado, roots corretos, finalizer_available e finalizer_named_output true, além das capabilities utilizadas pelo projeto.
4. Todos os nodes do inventário aparecem no object_info. Health do Job Control não é teste de disponibilidade de RAM/VRAM nem de todos os modelos.
5. As credenciais foram selecionadas; nenhum ID Telegram 0 operacional, domínio .invalid ou LOCAL_USER ficou configurado por engano.
6. O template LTX existe em /files/workflows/ltx.json e os nomes de modelos existem nos loaders.
7. O Error Workflow de cada componente aponta ao handler importado.
8. Não há outro supervisor nem outro bot workflow operando sobre o mesmo bot/estado.

Publicação sugerida: principal LTX → supervisor → bot Telegram. O handler usa Error Trigger, e Manual Recovery/T5 ficam fora da publicação normal. A publicação do supervisor inicia seus agendamentos: execute-a somente com mounts, roots, chave e estado já conferidos.

O supervisor atualizado possui 20 nodes e duas rotas de agendamento independentes: Recovery Schedule e Error Alert Schedule. A segunda trata incidentes/alertas; não submete GPU. Duas execuções leves por minuto, por si só, não significam que a fila esteja sendo recuperada repetidamente.

## 10. Primeiro teste

1. No bot de teste, envie /start. Confira comandos e callback de botão.
2. Envie um first frame e crie um único job curto, com duração suportada e proporção explícita.
3. Confira o arquivo recebido em current, a submissão ao Comfy e a evolução do job. A resposta de recebimento do webhook não é confirmação de que a GPU aceitou o prompt.
4. Abra a prévia e o formulário no telefone conectado à rede privada. Deixe o job aguardando para confirmar que não avança sem sua decisão.
5. Aprove. Confira interpolação, upscale batch8 e finalização no diretório final com o nome do job. O finalizador só deve publicar depois da conclusão do vídeo.
6. Confira que a notificação final chegou uma vez e que a reserva foi liberada.
7. Em outro teste, rejeite e recupere o rascunho via retry; confira também stop e status antes de usar múltiplos jobs.
8. T5 é um teste separado: rejeição HTTP400 intencional antes do sampling, incidente classificado, reserva liberada por evidência e fila sem bloqueio. Despublique-o depois. A retentativa de alerta deve reutilizar o mesmo incidente, sem reenviar geração.

Não force falta de RAM nem derrube o computador para validar a instalação básica. Cenários de recuperação após reinício são testes posteriores, com um job controlado e checkpoints conferidos.

## 11. Dados persistentes e atualização

Um backup operacional precisa tratar como conjunto o banco/configuração do n8n, sua chave de criptografia, o volume /files com estado/recibos/chave e os arquivos de vídeo referenciados. O repositório Git não substitui esse backup. Não use docker compose down -v para atualizar uma instância que precisa preservar dados.

Atualize com a fila controlada e export privado antes da mudança. Não rode um compose de exemplo sobre o volume de produção nem sobrescreva os custom nodes configurados com os templates públicos inertes.

## 12. Referências oficiais

- Docker n8n: https://docs.n8n.io/deploy/host-n8n/install-options/install-with-docker
- Acesso a arquivos no n8n: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.readwritefile
- Módulos dos Code nodes: https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/enable-modules-in-code-node
- Task runners: https://docs.n8n.io/deploy/host-n8n/configure-n8n/set-up-task-runners
- Binários em filesystem: https://docs.n8n.io/deploy/host-n8n/configure-n8n/scaling/handle-binary-data.md
- Proxy e webhook URL: https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/configure-webhook-urls-with-reverse-proxy
- Telegram Trigger: https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/common-issues
- Wait: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait

Referências consultadas em 24/10/2026. Os requisitos ligados aos templates foram conferidos nos arquivos; o guia inteiro ainda precisa de uma execução em instalação limpa. Não contém tokens, chaves reais ou URLs privadas de produção.
