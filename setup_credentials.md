# Como Configurar Credenciais OAuth2 para Google Drive

## Passo 1: Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Faça login com a conta **mauricio.s.lacerda@gmail.com**
3. Clique em **"Select a project"** → **"New Project"**
4. Nome do projeto: `Antigravity Sync`
5. Clique em **"Create"**

## Passo 2: Ativar Google Drive API

1. No menu lateral, vá em **"APIs & Services"** → **"Library"**
2. Pesquise por **"Google Drive API"**
3. Clique em **"Google Drive API"** → **"Enable"**

## Passo 3: Configurar Tela de Consentimento OAuth

1. Vá em **"APIs & Services"** → **"OAuth consent screen"**
2. Selecione **"External"** → **"Create"**
3. Preencha:
   - App name: `Antigravity Sync`
   - User support email: `mauricio.s.lacerda@gmail.com`
   - Developer contact: `mauricio.s.lacerda@gmail.com`
4. Clique em **"Save and Continue"** nas próximas etapas
5. Em **"Test users"**, adicione: `mauricio.s.lacerda@gmail.com`

## Passo 4: Criar Credenciais OAuth2

1. Vá em **"APIs & Services"** → **"Credentials"**
2. Clique em **"+ Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `Antigravity Sync Desktop`
5. Clique em **"Create"**
6. Clique em **"Download JSON"**
7. **Renomeie o arquivo para `credentials.json`**
8. **Mova o arquivo para a pasta do script:**

```
C:\Users\mauri\.gemini\antigravity\scratch\gdrive_sync\credentials.json
```

## Passo 5: Primeira Autenticação

```bash
cd C:\Users\mauri\.gemini\antigravity\scratch\gdrive_sync
python gdrive_sync.py auth
```

O navegador abrirá. Faça login com `mauricio.s.lacerda@gmail.com` e autorize o acesso.

> ⚠️ Como o app está em modo "Testing", aparecerá um aviso de segurança do Google. 
> Clique em **"Advanced"** → **"Go to Antigravity Sync (unsafe)"** → **"Continue"**.

Após autorizar, o arquivo `token.json` será criado automaticamente.

## Repetir no Segundo Computador

No outro computador:
1. Copie o `credentials.json` para a mesma pasta do script
2. Execute `python gdrive_sync.py auth`
3. Autorize com a mesma conta Google
4. Pronto! Ambos os PCs compartilharão a mesma pasta no Drive
