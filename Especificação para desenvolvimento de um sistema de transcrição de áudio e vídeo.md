# Especificação para desenvolvimento de um sistema de transcrição de áudio e vídeo

## 1. Objetivo

Desenvolver uma aplicação web local, executável em computador próprio, que permita ao usuário enviar um arquivo de áudio ou vídeo, escolher o idioma e receber uma transcrição pesquisável. O sistema deve usar o mesmo fluxo de processamento para os dois tipos de mídia: quando o arquivo for um vídeo, o sistema deve extrair o áudio com FFmpeg antes de enviá-lo ao mecanismo de transcrição.

A aplicação deve priorizar privacidade, baixo custo operacional, processamento local, boa experiência de uso e arquitetura preparada para evolução futura. O usuário não deve precisar escolher tecnologias diferentes para áudio e vídeo. A interface deve identificar ou permitir selecionar o tipo de arquivo e encaminhar ambos para um único pipeline de transcrição.

## 2. Escopo da primeira versão

A primeira versão, chamada MVP, deve oferecer:

- Upload de arquivos de áudio e vídeo.
- Validação de extensão, MIME type, tamanho e duração.
- Seleção de idioma, com opção de detecção automática.
- Seleção do modelo Whisper instalado no servidor.
- Extração de áudio de vídeos com FFmpeg.
- Transcrição local usando faster-whisper.
- Exibição do status do processamento.
- Resultado com texto, segmentos, timestamps e confiança quando disponível.
- Busca dentro da transcrição.
- Download em TXT, SRT, VTT e JSON.
- Exclusão manual dos arquivos e resultados.
- Limpeza automática de arquivos temporários após um período configurável.
- Tratamento de erros sem expor caminhos internos, comandos ou segredos.

A primeira versão não deve incluir autenticação, cobrança, publicação automática, tradução automática, identificação biométrica de pessoas, diarização obrigatória ou edição colaborativa. Esses recursos podem ser adicionados posteriormente sem comprometer a arquitetura.

## 3. Stack recomendada

Use a seguinte stack, salvo impedimento técnico documentado:

| Camada | Tecnologia | Motivo |
|---|---|---|
| Backend | Python 3.11 ou superior | Excelente ecossistema para IA, áudio e vídeo |
| API | FastAPI | Tipagem, validação, documentação OpenAPI e bom desempenho |
| Transcrição | faster-whisper | Execução local eficiente baseada no Whisper |
| Vídeo e áudio | FFmpeg | Extração, normalização e conversão de mídia |
| Validação | Pydantic | Contratos claros entre API e frontend |
| Banco | SQLite no MVP | Simples, local e suficiente para uso individual |
| ORM | SQLAlchemy 2 ou SQLModel | Persistência organizada e evolutiva |
| Fila MVP | Processamento assíncrono controlado no backend | Evita dependências desnecessárias no primeiro release |
| Fila de produção | Redis + Celery ou RQ | Recomendado quando houver múltiplos usuários ou jobs paralelos |
| Frontend | React + TypeScript + Vite | Interface moderna e tipada |
| Estilo | Tailwind CSS ou CSS modular | Componentes consistentes e manutenção simples |
| Testes frontend | Vitest e Testing Library | Testes rápidos de componentes e lógica |
| Testes backend | Pytest | Testes unitários e de integração |
| Conteinerização | Docker e Docker Compose | Instalação reproduzível com FFmpeg e dependências |
| Proxy opcional | Nginx ou Caddy | HTTPS e limite de upload em implantação de rede |

Não use Node.js para executar a transcrição. O Node.js deve ficar restrito ao frontend e às ferramentas de build. O processamento de mídia e IA deve permanecer no backend Python.

## 4. Arquitetura lógica

O sistema deve seguir esta sequência:

```text
Usuário
  |
  v
Frontend React
  |
  | POST /api/jobs com multipart/form-data
  v
FastAPI
  |
  +--> Valida extensão, MIME, tamanho e duração
  |
  +--> Salva arquivo em diretório temporário isolado por job
  |
  +--> Registra job no banco com status queued
  |
  v
Worker de processamento
  |
  +--> Se vídeo: FFmpeg extrai áudio mono PCM 16 kHz
  |
  +--> Se áudio: normaliza o áudio com FFmpeg quando necessário
  |
  +--> faster-whisper transcreve o áudio
  |
  +--> Salva segmentos, texto e metadados
  |
  v
Banco SQLite/PostgreSQL
  |
  v
Frontend consulta GET /api/jobs/{id}
  |
  v
Usuário visualiza, pesquisa e baixa a transcrição
```

O backend deve separar claramente quatro responsabilidades: API HTTP, gerenciamento de jobs, processamento de mídia e transcrição. Não coloque o código do Whisper diretamente dentro dos endpoints HTTP de upload.

## 5. Estrutura de diretórios

Use uma estrutura semelhante a esta:

```text
transcriber/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── api/
│   │   │   ├── routes_health.py
│   │   │   ├── routes_jobs.py
│   │   │   └── routes_downloads.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── models.py
│   │   │   └── migrations/
│   │   ├── schemas/
│   │   │   └── jobs.py
│   │   ├── services/
│   │   │   ├── job_service.py
│   │   │   ├── media_service.py
│   │   │   ├── transcription_service.py
│   │   │   └── export_service.py
│   │   └── workers/
│   │       └── process_job.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── App.tsx
│   ├── tests/
│   ├── package.json
│   └── Dockerfile
├── data/
│   ├── uploads/
│   ├── work/
│   └── results/
├── docker-compose.yml
├── .env.example
├── README.md
└── LICENSE
```

Os diretórios `uploads`, `work` e `results` devem ser configuráveis por variável de ambiente. Nunca use nomes de arquivo fornecidos diretamente pelo usuário como caminho final.

## 6. Modelo de dados

Crie uma tabela `transcription_jobs` com os seguintes campos:

| Campo | Tipo | Regra |
|---|---|---|
| id | UUID ou string segura | Identificador público do job |
| original_filename | string | Apenas para exibição |
| stored_filename | string | Nome interno gerado pelo sistema |
| media_type | enum | `audio` ou `video` |
| mime_type | string | MIME validado |
| file_size_bytes | integer | Tamanho recebido |
| duration_seconds | float opcional | Duração detectada pelo FFprobe |
| language | string opcional | Idioma escolhido ou detectado |
| model_name | string | Modelo utilizado |
| status | enum | `queued`, `processing`, `completed`, `failed`, `cancelled` |
| progress | integer | Valor entre 0 e 100 |
| error_code | string opcional | Código interno controlado |
| error_message | string opcional | Mensagem segura para o usuário |
| full_text | text opcional | Texto completo |
| segments_json | JSON opcional | Segmentos com início, fim e texto |
| created_at | datetime | UTC |
| started_at | datetime opcional | UTC |
| completed_at | datetime opcional | UTC |
| expires_at | datetime opcional | Data de limpeza |

Se o resultado for salvo em JSON separado, o banco deve armazenar apenas a referência segura ao arquivo e os metadados essenciais. O MVP pode armazenar o texto e os segmentos no SQLite.

## 7. Contrato da API

### `GET /api/health`

Retorna o estado da API, a versão e se FFmpeg está disponível. Não deve expor segredos ou informações sensíveis do sistema.

### `GET /api/config`

Retorna apenas opções públicas, como modelos habilitados, formatos aceitos e limites de upload.

Exemplo:

```json
{
  "models": ["tiny", "base", "small", "medium"],
  "default_model": "small",
  "languages": ["auto", "pt", "en", "es"],
  "max_file_size_mb": 1024,
  "max_duration_minutes": 180
}
```

### `POST /api/jobs`

Recebe `multipart/form-data`:

- `file`: arquivo de áudio ou vídeo.
- `language`: `auto`, `pt`, `en`, `es` ou outro idioma suportado.
- `model`: nome de um modelo permitido.
- `task`: inicialmente apenas `transcribe`.

Retorna HTTP 202:

```json
{
  "id": "job-id",
  "status": "queued",
  "progress": 0
}
```

O endpoint deve rejeitar arquivos inválidos antes de criar o job. Deve usar streaming ou escrita em blocos para não carregar arquivos grandes inteiros na memória.

### `GET /api/jobs/{id}`

Retorna status, progresso, duração, idioma detectado, modelo e, quando concluído, o resultado.

### `DELETE /api/jobs/{id}`

Cancela um job em andamento quando possível e remove os arquivos associados. Deve ser idempotente.

### `GET /api/jobs/{id}/download?format=txt`

Formatos obrigatórios: `txt`, `srt`, `vtt` e `json`. O servidor deve definir `Content-Disposition` com um nome seguro e não deve permitir path traversal.

## 8. Processamento de mídia

Use `ffprobe` para descobrir duração, streams e formato. Não confie somente na extensão do arquivo.

Para vídeo, extraia apenas o áudio com uma chamada equivalente a:

```bash
ffmpeg -i entrada.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le saida.wav
```

Para áudio, normalize de forma semelhante quando o formato ou codec exigir:

```bash
ffmpeg -i entrada_audio -vn -ac 1 -ar 16000 -c:a pcm_s16le saida.wav
```

O código deve executar subprocessos sem `shell=True`, usar timeout, capturar stdout e stderr de forma limitada e verificar o código de saída. Nunca monte comandos concatenando texto não confiável.

Extensões iniciais permitidas:

- Áudio: `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.opus`.
- Vídeo: `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`.

O MIME type e o conteúdo real devem ser validados. O sistema deve bloquear arquivos sem stream de áudio, duração acima do limite e arquivos excessivamente grandes.

## 9. Transcrição com faster-whisper

Implemente um `TranscriptionService` com interface estável:

```python
class TranscriptionService:
    def transcribe(
        self,
        audio_path: str,
        language: str | None,
        model_name: str,
    ) -> TranscriptionResult:
        ...
```

Use carregamento sob demanda e cache dos modelos para não carregar o mesmo modelo repetidamente. O modelo deve ser configurável:

- `tiny`: mais rápido e menos preciso.
- `base`: equilíbrio para máquinas modestas.
- `small`: melhor qualidade com maior consumo.
- `medium`: qualidade superior, exige mais recursos.

O padrão do MVP deve ser `small` se houver GPU suficiente e `base` em CPU. A aplicação deve detectar CPU ou CUDA e escolher `compute_type` compatível. Não presuma que todos os usuários possuem GPU NVIDIA.

O resultado deve preservar:

```json
{
  "language": "pt",
  "language_probability": 0.98,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.2,
      "text": "Texto do segmento"
    }
  ],
  "text": "Texto completo"
}
```

O progresso pode ser estimado pelo tempo processado em relação à duração total. Se a biblioteca não fornecer progresso confiável, use estágios explícitos: `validating`, `extracting_audio`, `transcribing`, `saving_result` e `completed`.

## 10. Interface do usuário

Crie uma página principal simples e responsiva com:

1. Área de arrastar e soltar.
2. Botão para selecionar arquivo.
3. Indicação explícita de que áudio e vídeo são aceitos.
4. Campo de idioma com detecção automática.
5. Campo de modelo com explicação de velocidade e qualidade.
6. Botão `Iniciar transcrição`.
7. Cartão de progresso com status, percentual e mensagens compreensíveis.
8. Área de resultado com texto e timestamps.
9. Busca por palavra dentro da transcrição.
10. Botões de download em TXT, SRT, VTT e JSON.
11. Botão de excluir o job.
12. Mensagens de erro com ação sugerida.

A interface não deve fingir que o processamento é instantâneo. Ela deve informar que a velocidade depende da duração, do modelo e do hardware.

Para jobs longos, use polling controlado a cada 1 ou 2 segundos no MVP. Pare o polling ao receber `completed`, `failed`, `cancelled` ou ao atingir timeout. Se o sistema evoluir para múltiplos usuários, substitua ou complemente o polling com WebSocket ou Server-Sent Events.

## 11. Segurança e privacidade

A aplicação deve tratar todos os arquivos como não confiáveis. Implemente:

- Limite de tamanho e duração.
- Lista explícita de extensões e MIME types.
- Nomes internos gerados com UUID.
- Diretórios isolados por job.
- Bloqueio de path traversal.
- Timeout para FFmpeg e transcrição.
- Limite de jobs simultâneos.
- Limpeza de temporários em sucesso e falha.
- Expiração configurável dos resultados.
- Logs sem conteúdo completo do áudio, vídeo ou transcrição.
- Mensagens de erro genéricas para o usuário.
- CORS restrito ao frontend configurado.
- Segredos somente em variáveis de ambiente.
- HTTPS quando exposto fora da máquina local.

O sistema deve deixar claro na interface se os arquivos permanecem somente no computador do usuário. Caso seja instalado em servidor remoto, a política de retenção deve ser exibida e respeitada.

## 12. Configuração por ambiente

Crie `.env.example` com:

```env
APP_ENV=development
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./data/transcriber.db
DATA_DIR=./data
MAX_FILE_SIZE_MB=1024
MAX_DURATION_MINUTES=180
MAX_CONCURRENT_JOBS=1
DEFAULT_MODEL=base
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=auto
JOB_RETENTION_HOURS=24
CORS_ORIGINS=http://localhost:5173
```

O código deve validar as configurações na inicialização e falhar com uma mensagem clara quando uma configuração essencial estiver incorreta.

## 13. Docker e execução local

Forneça um `docker-compose.yml` com serviços `backend` e `frontend`. O backend deve conter FFmpeg. Monte `./data` como volume persistente. Não inclua GPU como requisito obrigatório; ofereça uma configuração opcional documentada para NVIDIA Container Toolkit.

Também forneça execução sem Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

No frontend:

```bash
npm install
npm run dev
```

O README deve explicar a instalação do FFmpeg em Linux, macOS e Windows sem presumir um sistema operacional único.

## 14. Testes obrigatórios

Crie testes para:

- Upload válido de áudio.
- Upload válido de vídeo.
- Rejeição de extensão não permitida.
- Rejeição de arquivo acima do tamanho máximo.
- Rejeição de vídeo sem áudio.
- Extração de áudio com FFmpeg.
- Falha controlada quando FFmpeg não estiver instalado.
- Seleção de idioma e modelo.
- Persistência dos estados do job.
- Cancelamento e exclusão idempotentes.
- Geração correta de TXT, SRT, VTT e JSON.
- Caminhos que tentem usar `../`.
- Falha do modelo de transcrição.
- Limpeza automática de arquivos expirados.
- Renderização e atualização de progresso no frontend.

Inclua pelo menos um teste de integração que envie um arquivo pequeno real e valide o resultado final. Use arquivos de teste curtos e livres de restrições de direitos autorais.

## 15. Critérios de aceitação

O desenvolvimento só estará concluído quando:

- O projeto iniciar com Docker Compose seguindo o README.
- O usuário conseguir selecionar áudio ou vídeo na mesma tela.
- Um vídeo tiver o áudio extraído automaticamente.
- O backend não bloquear a API durante todo o processamento.
- O status do job for atualizado corretamente.
- A transcrição puder ser visualizada e baixada nos quatro formatos.
- Erros de arquivo, FFmpeg e Whisper forem tratados sem stack trace na interface.
- Os testes automatizados passarem.
- Nenhum segredo estiver versionado.
- Os arquivos temporários forem removidos conforme a política configurada.
- O código estiver formatado, tipado quando possível e acompanhado de documentação de operação.

## 16. Ordem recomendada de implementação

Implemente em etapas verificáveis:

1. Criar backend, configuração, banco e endpoint de saúde.
2. Implementar upload seguro e criação de jobs.
3. Implementar FFprobe e FFmpeg.
4. Implementar o `TranscriptionService` com faster-whisper.
5. Implementar o worker e o ciclo de vida dos jobs.
6. Implementar exportação de resultados.
7. Criar o frontend de upload e progresso.
8. Criar a tela de resultado e downloads.
9. Adicionar limpeza, limites e logs.
10. Escrever testes e documentação.
11. Executar uma validação completa com áudio e vídeo reais de teste.
12. Corrigir todos os erros antes de declarar o MVP pronto.

## 17. Prompt para a IA desenvolvedora

Você é um engenheiro de software sênior. Desenvolva o sistema descrito neste documento de forma funcional, segura e testável. Não entregue apenas exemplos ou pseudocódigo.

Use Python com FastAPI no backend, React com TypeScript no frontend, SQLite no MVP, FFmpeg para processamento de mídia e faster-whisper para transcrição local. O usuário deve usar uma única interface e escolher ou enviar um arquivo de áudio ou vídeo. Para vídeo, extraia o áudio antes da transcrição. Separe API, serviços, worker, persistência e interface.

Implemente primeiro a estrutura do projeto e depois cada etapa em ordem. Após cada etapa, execute os testes correspondentes. Não introduza bibliotecas sem justificar a necessidade. Não use `shell=True`. Não coloque o processamento pesado dentro do endpoint HTTP. Não armazene arquivos com nomes fornecidos pelo usuário. Não exponha stack traces, segredos ou caminhos internos.

Entregue:

- Código completo do backend e frontend.
- Dockerfiles e `docker-compose.yml`.
- `.env.example`.
- Migrações ou criação inicial do banco.
- Testes unitários e de integração.
- README com instalação, execução, modelos, GPU opcional, solução de problemas e limites conhecidos.
- Exemplos de chamadas da API.
- Validação final com um arquivo de áudio e um arquivo de vídeo.

Se encontrar uma decisão não especificada, escolha a alternativa mais simples que preserve privacidade, segurança, testabilidade e possibilidade de evolução. Registre a decisão no README. Antes de finalizar, verifique os critérios de aceitação deste documento e informe quais foram validados.

## 18. Evoluções futuras

Depois do MVP estável, podem ser adicionados autenticação, múltiplos usuários, Redis, Celery ou RQ, PostgreSQL, diarização de locutores, tradução, edição manual de segmentos, legendas queimadas no vídeo, armazenamento S3 compatível, WebSocket, filas distribuídas e implantação com GPU. Esses recursos não devem ser implementados na primeira versão sem necessidade, pois aumentam a superfície de falhas e a complexidade operacional.

## Referências

[1]: https://fastapi.tiangolo.com/ "FastAPI Documentation"

[2]: https://github.com/SYSTRAN/faster-whisper "faster-whisper Repository"

[3]: https://ffmpeg.org/documentation.html "FFmpeg Documentation"

[4]: https://github.com/openai/whisper "OpenAI Whisper Repository"

[5]: https://react.dev/ "React Documentation"

[6]: https://www.typescriptlang.org/docs/ "TypeScript Documentation"

[7]: https://docs.docker.com/compose/ "Docker Compose Documentation"

[8]: https://docs.pytest.org/ "pytest Documentation"

[9]: https://docs.celeryq.dev/ "Celery Documentation"

[10]: https://redis.io/docs/latest/ "Redis Documentation"
