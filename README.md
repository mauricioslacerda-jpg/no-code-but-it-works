# 🔄 Antigravity Google Drive Sync

Agente de sincronização para compartilhar dados do [Antigravity](https://antigravity.google) entre dois computadores via Google Drive.

## ✨ Funcionalidades

- **Push**: Upload de dados locais para o Google Drive
- **Pull**: Download de dados do Drive para o local
- **Sync**: Sincronização bidirecional (pull + push)
- **Updates**: Gerenciamento de atualizações gerais compartilhadas
- **Backup automático**: Cria backups de releitura com flag `_01_reavaliar` quando há mudanças
- **Detecção de conflitos**: Baseada em timestamps e checksums MD5

## 📁 O que é sincronizado

| Pasta | Conteúdo |
|-------|----------|
| `brain/` | Conversas e artefatos do Antigravity |
| `knowledge/` | Knowledge Items acumulados |
| `conversations/` | Logs de conversas (protobuf) |
| `updates/` | Notas de atualização gerais |

## 🚀 Setup Rápido

### 1. Instalar Python e dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais OAuth2

Siga o guia em [setup_credentials.md](setup_credentials.md) para criar as credenciais no Google Cloud Console.

### 3. Autenticar

```bash
python gdrive_sync.py auth
```

### 4. Sincronizar!

```bash
python gdrive_sync.py sync      # Sincronização bidirecional
python gdrive_sync.py push      # Apenas enviar
python gdrive_sync.py pull      # Apenas receber
python gdrive_sync.py status    # Ver status atual
python gdrive_sync.py updates   # Ver atualizações gerais
```

## 📝 Comandos de Updates

```bash
python gdrive_sync.py updates list                    # Listar atualizações
python gdrive_sync.py updates add "Mensagem aqui"     # Adicionar nota
python gdrive_sync.py updates clear                   # Limpar notas antigas (>30 dias)
```

## ⚙️ Como funciona

```
PC 1 ←→ Google Drive (Antigravity-Sync/) ←→ PC 2
```

Os dados do Antigravity são sincronizados via uma pasta compartilhada no Google Drive. O script usa checksums MD5 para detectar mudanças e timestamps para resolver conflitos.

## 👤 Autor

Mauricio Lacerda (mauricio.s.lacerda@gmail.com)
