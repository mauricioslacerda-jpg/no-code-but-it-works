# Meridiam ✨

Decision Maker Hub - Aplicação web progressiva (PWA) com ferramentas de gestão e marketing para tomada de decisão baseada em dados, com integração de IA.

## Características

- **Decision Frameworks**: Método GUT (Gravidade, Urgência, Tendência) e outras ferramentas
- **Multiplataforma**: Funciona em desktop, mobile e tablet
- **PWA**: Instalável como app nativo
- **Offline-first**: Funciona sem internet (modo local)
- **Sync Cloud**: Sincronização opcional com Firebase
- **IA Integrada**: Sugestões e análises estratégicas com Google Gemini

## Setup Rápido

### 1. Configuração Básica (Modo Local)

```bash
# Clone o repositório
git clone https://github.com/mauricioslacerda-jpg/no-code-but-it-works.git
cd no-code-but-it-works/meridiam

# Abra index.html diretamente no navegador
# A app funciona em modo local sem configuração adicional
```

### 2. Configuração com IA (Opcional)

```bash
# Copie o arquivo de exemplo
cp config.example.js config.js

# Edite config.js e adicione sua Gemini API Key
# Obtenha em: https://aistudio.google.com/app/apikey
```

### 3. Configuração com Sync Cloud (Opcional)

Edite `config.js` e adicione as credenciais do Firebase:

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Crie um novo projeto
3. Ative Firestore Database e Authentication (Anonymous)
4. Copie as credenciais para `config.js`

## Deploy

### GitHub Pages

```bash
# Ative GitHub Pages nas configurações do repositório
# Branch: main
# Folder: / (root)
```

### Netlify / Vercel

```bash
# Faça deploy direto do repositório
# Build command: (deixe vazio)
# Publish directory: /
```

### Firebase Hosting

```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy
```

## Estrutura

```
/
├── index.html          # Aplicação principal
├── config.example.js   # Template de configuração
├── config.js          # Suas credenciais (não versionado)
├── manifest.json      # PWA manifest
└── README.md          # Documentação do projeto
```

## Modos de Operação

| Modo | Requer | Funcionalidades |
|------|--------|-----------------|
| **Local** | Nada | CRUD de atividades GUT, cálculo de scores, gráficos |
| **+ IA** | Gemini API | Sugestões automáticas, análises, estratégias |
| **+ Cloud** | Firebase | Sincronização multi-dispositivo, backup automático |

## Uso

1. **Adicionar Atividade**: Clique no botão + e descreva a tarefa
2. **Avaliar GUT**: Defina Gravidade, Urgência e Tendência (1-5)
3. **Usar IA**: Clique em "Sugerir com IA" para avaliação automática
4. **Ver Estratégia**: Em cada atividade, clique "Estratégia" para plano de ação
5. **Analisar Tudo**: Na home, "Analisar Prioridades" para visão geral

## Segurança

- **NUNCA** faça commit de `config.js`
- Use variáveis de ambiente em produção
- Restrinja a API Key do Gemini no Google Cloud Console
- Configure regras de segurança do Firestore

## Compatibilidade

- ✅ Chrome/Edge 90+
- ✅ Safari 14+
- ✅ Firefox 88+
- ✅ iOS Safari 14+
- ✅ Chrome Android 90+

## Tecnologias

- Vanilla JavaScript (ES6+)
- Tailwind CSS (CDN)
- Chart.js (gráficos)
- Firebase (backend opcional)
- Google Gemini AI (análises)

## Licença

MIT - Use como quiser.

## Suporte

Abra uma issue no GitHub para bugs ou sugestões.
