# Plano de Desenvolvimento e Acompanhamento: Sistema de Transcrição

Este documento detalha o roteiro de desenvolvimento em etapas lógicas e incrementais, baseado na especificação do MVP. Cada tarefa inclui passos de implementação e validação. Marque com um `[x]` ao concluir, testar e validar cada item.

## Etapa 1: Fundação do Backend e Infraestrutura Inicial
- [x] Inicializar o projeto Python (venv) e configurar o `requirements.txt` (FastAPI, Uvicorn, Pydantic, SQLAlchemy, etc.).
- [x] Configurar variáveis de ambiente (`.env.example` e classe de configuração Pydantic).
- [x] Configurar a estrutura de diretórios (`app/`, `tests/`, `data/`).
- [x] Configurar o banco de dados SQLite e os modelos/tabelas (`transcription_jobs`).
- [x] Criar o endpoint de saúde (`GET /api/health`) e de configuração (`GET /api/config`).
- [x] **Validação:** Rodar o servidor localmente, acessar `/api/health` e garantir que o banco `transcriber.db` é criado.

## Etapa 2: Gerenciamento de Arquivos e Upload
- [x] Implementar a lógica de salvamento seguro de arquivos (UUIDs, diretórios temporários).
- [x] Criar o endpoint de recepção de arquivos (`POST /api/jobs`).
- [x] Adicionar validações estritas (extensão, MIME type, tamanho limite).
- [x] Criar e persistir o registro do Job no banco de dados com status `queued`.
- [x] **Validação:** Enviar um arquivo via cURL/Postman, verificar se ele é salvo corretamente no disco com UUID e se o registro aparece no SQLite. Testar rejeição de arquivos inválidos.

## Etapa 3: Processamento de Mídia (FFmpeg/FFprobe)
- [x] Criar serviço (`media_service.py`) para interagir com o `ffprobe` (obter duração e validar se possui áudio).
- [x] Adicionar validação de duração máxima baseada na configuração.
- [x] Implementar extração/conversão de áudio via `ffmpeg` (para .wav, mono, 16kHz) de forma segura (sem `shell=True`).
- [x] **Validação:** Escrever um script simples ou teste automatizado para enviar um `.mp4` e verificar se o `.wav` resultante foi criado com as especificações corretas.

## Etapa 4: Transcrição Base (faster-whisper)
- [x] Configurar o `TranscriptionService` integrado à biblioteca `faster-whisper`.
- [x] Implementar a lógica de carregamento dinâmico de modelos (`tiny`, `base`, `small`, etc.) e suporte à detecção de CPU/GPU.
- [x] Formatar o retorno da transcrição (texto completo e segmentos).
- [x] **Validação:** Escrever um teste que injeta um áudio curto e real em português, validando se o serviço retorna o texto corretamente (teste isolado do endpoint).

## Etapa 5: Worker e Ciclo de Vida do Job
- [x] Criar o serviço de background/worker (`process_job.py`) para unir as etapas anteriores.
- [x] Implementar a máquina de estados do Job (`queued` -> `processing` (extração -> transcrição) -> `completed` ou `failed`).
- [x] Adicionar tratamento global de exceções no worker (atualizando o banco para `failed` com mensagem segura).
- [x] Criar endpoints de consulta (`GET /api/jobs/{id}`) e cancelamento (`DELETE /api/jobs/{id}`).
- [x] **Validação:** Enviar uma requisição de upload completa. Acompanhar pelo banco ou log o job transitando até `completed` com a transcrição salva no banco.

## Etapa 6: Exportação de Resultados
- [x] Criar o serviço de exportação (`export_service.py`) para converter os segmentos/JSON para TXT, SRT e VTT.
- [x] Criar o endpoint de download (`GET /api/jobs/{id}/download?format=...`).
- [x] **Validação:** Processar um arquivo, realizar o download nos 4 formatos suportados e abrir os arquivos localmente para garantir a formatação (ex: timestamps do SRT).

## Etapa 7: Estruturação do Frontend (React + Vite)
- [x] Inicializar o projeto Vite (React + TS) e configurar o TailwindCSS.
- [x] Criar o esqueleto da interface principal responsiva.
- [x] Implementar a área de arrastar/soltar e seleção de arquivos.
- [x] Implementar seletores de idioma e modelo.
- [x] **Validação:** Executar o frontend, testar a interface de seleção e validar se as opções refletem o `GET /api/config`.

## Etapa 8: Integração Front/Back e Progresso
- [x] Conectar o envio do formulário (Upload) ao endpoint `/api/jobs`.
- [x] Implementar sistema de *polling* (ex: a cada 2 segundos) para consultar o status do Job após o upload.
- [x] Desenvolver o componente visual de progresso (barra de carregamento e status).
- [x] **Validação:** Fazer um upload pela UI e ver a barra de progresso avançar até a conclusão. Testar também o fluxo de erro (ex: simular erro no backend).

## Etapa 9: Interface de Resultados e Limpeza
- [x] Construir o componente de exibição do texto transcrito (com pesquisa interna de palavras).
- [x] Adicionar os botões de download e exclusão visual, integrados à API.
- [x] Implementar no backend o *cron* interno ou lógica para expiração e limpeza de jobs e arquivos antigos.
- [x] **Validação:** Concluir uma transcrição, pesquisar no texto pela UI, baixar os arquivos e depois clicar em "Excluir". Verificar se o job e os arquivos sumiram do disco e do banco.

## Etapa 10: Dockerização e Polimentos
- [x] Escrever o `Dockerfile` do backend (instalando dependências do sistema como `ffmpeg`).
- [x] Escrever o `Dockerfile` do frontend (build estático com Nginx).
- [x] Criar o `docker-compose.yml` para orquestração geral.
- [x] Ocultar *stack traces* completos da interface, garantindo mensagens *user-friendly*.
- [x] **Validação:** Derrubar os ambientes locais, rodar `docker compose up --build` e fazer um fluxo completo no sistema usando as portas expostas pelos containers.

## Etapa 11: Bateria de Testes Finais e Documentação
- [x] Implementar/Refatorar os testes unitários (Pytest) para serviços críticos.
- [x] Escrever um teste de integração de ponta a ponta.
- [x] Redigir o arquivo `README.md` detalhando instruções de instalação (local e docker), configuração de GPU opcional e limites.
- [x] **Validação Final:** Executar a suíte completa de testes (`pytest`), subir o projeto usando apenas as instruções do `README` e processar um áudio e um vídeo longos para validar a estabilidade do MVP.

## Etapa 12: Melhorias Rápidas e de Alto Impacto
- [x] **Tradução Automática:** Adicionar suporte na API para a task de tradução do Whisper (para o inglês) e incluir um botão correspondente no frontend.
- [x] **Importação Direta do YouTube:** Adicionar integração com `yt-dlp` para permitir colar um link de vídeo e baixar/transcrever o áudio automaticamente, sem remover o upload de arquivos locais.
- [x] **Progresso em Tempo Real (WebSockets):** Substituir o *polling* por conexões WebSocket no FastAPI e frontend para exibir o andamento exato em tempo real.
- [x] **Upload em Lote (Batch Upload):** Alterar a área de envio e o controle de estado para permitir arrastar e enfileirar múltiplos arquivos de uma vez.
- [ ] **Validação:** Enviar uma lista de arquivos de áudio, acompanhar o progresso via WebSocket sem travamentos, e baixar um resultado traduzido.

## Etapa 13: Recursos de Inteligência Avançada (Complexidade Média)
- [ ] **Diarização (Identificação de Locutores):** Integrar uma ferramenta como `pyannote.audio` ao pipeline para separar o texto por quem está falando (Ex: Locutor 1, Locutor 2).
- [ ] **Geração de Resumo / Ata Inteligente:** Integrar um LLM (local ou API) no pipeline final para ler a transcrição gerada e extrair os pontos-chave e decisões.
- [ ] **Embutir Legendas no Vídeo:** Criar um serviço no backend que usa o FFmpeg para sobrepor (hardcode) a legenda gerada no `.mp4` original e oferecer o download do vídeo.
- [ ] **Validação:** Processar um vídeo de reunião real, verificar o download do vídeo já com legendas, a listagem dos participantes falando separados e gerar a ata resumida da reunião.

## Etapa 14: Bateria de Testes de QA e Segurança
- [ ] **Testes de Regressão:** Executar novamente toda a suíte de testes unitários e de integração (`pytest`) criada na Etapa 11 para garantir que as novas funcionalidades (WebSockets, LLM, Diarização) não quebraram o MVP.
- [ ] **Testes de Segurança (Pen-Test Básico):** Realizar testes contra as novas rotas de upload em lote, manipulação de arquivos de legenda e processamento de LLM (testando injeção de prompt, path traversal e denial of service com arquivos muito grandes).
- [ ] **Testes de Qualidade (QA Models):** Criar casos de teste automatizados usando modelos padrão de QA na indústria (ex: Cypress, Selenium ou Playwright) para validar as interações do usuário no Frontend (upload em lote, visualização em tempo real do WebSocket).
- [ ] **Validação:** Obter 100% de passagem nos testes de QA E2E (End-to-End) automatizados e elaborar um relatório simples atestando a segurança da aplicação para rodar localmente ou exposta.
