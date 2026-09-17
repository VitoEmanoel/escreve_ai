# Escreve.AI

O **Escreve.AI** é um sistema completo, 100% offline e focado em privacidade para transcrição de áudio e vídeo utilizando os modelos de Inteligência Artificial mais modernos (faster-whisper). 

## Recursos Principais
-  Extração e transcrição de mídias pesadas (MP4, MP3, WAV, M4A, etc) localmente.
-  Suporte avançado via CPU ou aceleração de placa de vídeo (GPU NVIDIA).
-  Exportação para vários formatos: `TXT`, `JSON`, `SRT` (Legenda) e `VTT` (Legenda Web).
-  Auto-limpeza de dados. Todos os metadados e arquivos sensíveis são limpos periodicamente, garantindo privacidade total.

---

## 🐳 Opção 1: Rodando via Docker (Recomendado e mais fácil)

### Pré-requisitos (Linux/macOS/Windows)
1. Certifique-se de ter o [Docker](https://docs.docker.com/get-docker/) e o [Docker Compose](https://docs.docker.com/compose/install/) instalados.
2. **No Linux**, garanta que o serviço do Docker esteja iniciado e habilitado:
   ```bash
   sudo systemctl enable --now docker
   ```
   > **Dica de permissão no Linux**: Para rodar o Docker sem `sudo`, adicione seu usuário ao grupo:
   > ```bash
   > sudo usermod -aG docker $USER
   > newgrp docker
   > ```

### Passo a passo:
1. Abra o terminal na raiz do projeto e crie o arquivo de configuração `.env`:
   ```bash
   cp .env.example backend/.env
   ```
2. Suba a aplicação com o Docker Compose:
   ```bash
   docker compose up --build -d
   ```
3. Acompanhe os logs da inicialização (opcional):
   ```bash
   docker compose logs -f
   ```
4. Acesse **http://localhost** no seu navegador.
5. Para desligar os serviços:
   ```bash
   docker compose down
   ```

> **Aviso de Porta**: A interface roda na porta padrão `80`. Se a porta 80 estiver em uso por outro serviço na sua máquina, altere em [docker-compose.yml](file:///home/victor/Documentos/Repository/escreve_ai/docker-compose.yml) a linha `- "80:80"` para `- "8080:80"` e acesse em `http://localhost:8080`.

**Nota (GPU - NVIDIA)**: Para usar a placa de vídeo no Docker, descomente a seção `deploy: resources...` no arquivo `docker-compose.yml` e instale o [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

---

##  Opção 2: Rodando Localmente (Para Desenvolvedores)
Caso queira modificar o código ou usar Python nativamente.

### Requisitos:
- **Python 3.10+**
- **FFmpeg** instalado no sistema (`sudo apt install ffmpeg` no Linux ou via `brew` no Mac)
- **Node.js** (v20+)

### Passo a passo (Backend):
1. Crie um ambiente virtual (recomendamos `uv` ou `venv`):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Rode o servidor na porta 8000:
   ```bash
   export PYTHONPATH=$PWD/backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Passo a passo (Frontend):
Em um **novo terminal**:
1. Entre na pasta frontend e instale:
   ```bash
   cd frontend
   npm install
   ```
2. Rode o servidor de interface:
   ```bash
   npm run dev
   ```
3. Acesse **http://localhost:5173**.

---

## Customização e Limites
Você pode alterar os limites padrão acessando o arquivo `backend/.env` (crie um se não existir, baseado em `.env.example`).
Por padrão, arquivos têm limite de 1 GB de tamanho e 180 minutos de áudio contínuo. Jobs antigos são destruídos após 24h.

---
Feito de forma segura e autônoma! 
