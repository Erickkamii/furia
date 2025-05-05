# 🤖 FURIA Chatbot - Fullstack (Next.js + FastAPI)

Este projeto é um chatbot inteligente para a **FURIA Esports**, com backend em Python (FastAPI) e frontend em Next.js.  
Ele utiliza a API da OpenAI para responder perguntas com base em uma base de conhecimento específica da organização.

---

## 📁 Estrutura do Repositório

```
/furia-bot/
│
├── backend/          # Backend com FastAPI
│   ├── main.py       # Código principal do servidor
│   └── data/         
│       └── furia_esports.json  # Base de conhecimento
│
├── frontend/         # Frontend com Next.js
│   └── ...           
│
├── docker-compose.yml
└── .env              # Arquivo de variáveis de ambiente (não versionado)
```

---

## ⚙️ Pré-requisitos

- Docker instalado: [https://docs.docker.com/get-docker](https://docs.docker.com/get-docker)
- Conta e chave de API da OpenAI: [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)

---

## 🚀 Como rodar o projeto

1. Clone o repositório:

   ```bash
   git clone https://github.com/seu-usuario/furia-bot.git
   cd furia-bot
   ```

2. Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

   ```
   OPENAI_API_KEY=sua-chave-da-openai-aqui
   ```

3. Inicie os serviços com Docker:

   ```bash
   docker-compose up --build
   ```

4. Acesse:
   - Frontend: http://localhost:3000  
   - Backend (API): http://localhost:8000/health

---

## 🧠 Como funciona?

- O **frontend** envia uma pergunta ao backend via `/query`.
- O **backend** lê uma base de conhecimento (`furia_esports.json`) com dados da FURIA.
- O backend usa a **OpenAI API** para gerar uma resposta com base no contexto e retorna para o frontend.

---

## 🛠 Tecnologias utilizadas

- 🔙 **FastAPI** (Python)
- 🌐 **Next.js** (React)
- 🧠 **OpenAI API**
- 🐳 **Docker + Docker Compose**

---

## 📄 Licença

Este projeto é apenas para fins acadêmicos e de demonstração.
