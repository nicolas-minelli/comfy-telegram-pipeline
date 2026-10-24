# Revisão dos exports — 24/10/2026

## Escopo

Seis exports atuais: principal LTX, Telegram Bot, supervisor Automatic Recovery v2, Error Handler v2 e cópia de falha controlada T5. O Manual Recovery foi recebido e incluído depois da primeira remessa.

## Observações da entrada

- Sem pinData ou staticData preenchidos.
- Headers de autorização dos endpoints Comfy usam expressões; não havia token literal nesses campos.
- Havia referências locais a credenciais, identificadores de webhook, metadados da instância, usuário autorizado e domínio pessoal.
- A presença de um ID/nome de credencial não significa que o token correspondente estava no export. Os vínculos foram removidos mesmo assim para distribuir exemplos independentes da instalação.

## Alterações na cópia

- Removidos 31 vínculos a credenciais e 86 IDs de webhook.
- Removidos metadados da instância, IDs/version IDs dos workflows, tags e grupos exportados.
- Removidas associações locais a Error Workflow; precisarão ser reconfiguradas.
- Todos os templates desativados e sem dados fixados.
- IDs internos de nodes regenerados; nomes e conexões preservados.
- ID autorizado substituído por zero nas referências correlatas e domínio pessoal por exemplo inválido.
- T5 separado em tests/fixtures e mantido desativado.
- Não foram alterados os arquivos de produção, modelos ou segredos locais.

## Verificações

- Seis JSONs n8n válidos, 380 nodes e conexões com destinos existentes.
- Sintaxe de todos os blocos JavaScript jsCode validada com o construtor AsyncFunction do Node.js, sem executar os blocos.
- Ausência dos marcadores pessoais conhecidos, IDs raiz dos workflows de origem, padrões de token Telegram e literais hexadecimais de 64 caracteres nos templates finais.
- Sem vínculos a credenciais ou IDs de webhook remanescentes nos nodes.

## Limites e próximos passos

Esta revisão não garante detecção de todo formato possível de segredo. Não se deve colocar no mesmo commit nenhum export bruto, volume Docker, .env, chave ou log. Antes do primeiro push, revisar a lista exata de arquivos staged e executar um scanner de segredos sobre o repositório e o histórico que será enviado.

O snapshot ainda não inclui automação de configuração, scripts de build/operação nem uma licença. A integração desses componentes exige nova revisão de dados pessoais e de consistência. Não publique ainda como release instalável.

Na pasta Windows chamada production, mantenha somente arquivos privados da instalação. Esse nome não muda o armazenamento interno do n8n; ele só organiza os exports que você gravar ali.

## Complemento Comfy atualizado

Os exports antigos de referência de interpolação e upscale foram removidos. Os cinco grafos em comfy/api foram extraídos executando os builders atuais do n8n com dados sintéticos, para 9:16 e 16:9. O template LTX de entrada está em comfy/templates.

Verificados loader VHS_LoadVideoPath, batch8, áudio, dimensões por proporção, finalizador, conexões e IDs dinâmicos substitutos. O script de reprodução não executa o scheduler nem faz submissões à GPU. Não houve alteração da produção.

## Custom nodes confirmados

Ambos os arquivos recebidos são idênticos ao último pacote instalado. Job Control: substituído o ID Telegram pessoal por zero, sem alterar as validações/autenticação. Finalizador: conteúdo preservado. Diretórios E:\AI\media e E:\AI\media\final mantidos como defaults documentados para configuração local, não como segredos.

Corrigidos os dados sintéticos dos grafos: run_id tg-0-1-e1 e prefixo de saída por execução, conforme as restrições do finalizador. Isso corrige somente os exemplos de distribuição. Não houve mudança na instalação em produção.
