# Meridiam ✨
## Toma decisões melhores em 30 segundos

Ferramenta visual para priorizares tarefas usando o método GUT (Gravidade × Urgência × Tendência).
Com IA opcional para te dar sugestões estratégicas.

---

## 🚀 Começar AGORA (literalmente 30 segundos)

### Opção 1: Mais Simples (sem IA)
1. Faz download de `index.html`
2. Duplo-clique no ficheiro
3. Já está a funcionar ✅

### Opção 2: Com IA (2 minutos extra)
1. Faz download de **todos** os ficheiros desta pasta
2. Copia `config.example.js` e renomeia para `config.js`
3. [Clica aqui](https://aistudio.google.com/app/apikey) para criar uma API key do Google (grátis)
4. Abre `config.js` e cola a tua API key onde diz `YOUR_GEMINI_API_KEY_HERE`
5. Duplo-clique em `index.html`
6. Pronto - agora tens IA ✨

---

## 💡 Como usar

### 1️⃣ Adicionar uma decisão/tarefa
Clica no botão **+** e escreve o que precisas fazer.
Exemplo: *"Lançar campanha no Instagram"*

### 2️⃣ Classificar importância
Responde 3 perguntas simples (escala de 1 a 5):
- **G**ravidade: Que problema isto resolve?
- **U**rgência: Precisa ser feito quando?
- **T**endência: Vai piorar se não fizer?

💡 *Dica: Clica em "Sugerir com IA" e ela classifica por ti*

### 3️⃣ Ver prioridades
A app calcula automaticamente o que é crítico (score alto = fazer JÁ).
Gráfico visual mostra tudo numa bolha interativa.

### 4️⃣ Pedir estratégia à IA
Clica em **"✨ Estratégia"** em qualquer tarefa.
A IA dá-te um plano de ação concreto.

---

## ❓ Perguntas Rápidas

**Preciso de internet?**
Não. Funciona 100% offline no teu computador/telemóvel.

**Os meus dados ficam onde?**
No teu dispositivo. Nada vai para a cloud (a não ser que configures Firebase).

**Funciona no telemóvel?**
Sim! Abre no browser. Podes até "instalar" como app (Chrome → Menu → Instalar app).

**Quanto custa?**
Zero. A API do Google Gemini tem plano grátis generoso.

**Preciso saber programar?**
Não. Zero código. Prometo.

---

## 🎨 Personalização (Opcional)

### Ícones para instalar como app
1. Abre `generate-icons.html` no browser
2. Faz download dos 2 ícones
3. Guarda-os nesta pasta
4. Agora podes instalar como app nativa no telemóvel

### Sincronizar entre dispositivos
Se quiseres que as tarefas apareçam em todos os teus dispositivos:
1. Cria conta grátis no [Firebase](https://console.firebase.google.com/)
2. Copia as credenciais para `config.js`
3. Pronto - sincroniza automaticamente

---

## 🆘 Problemas?

**IA não funciona**
→ Confirma que colocaste a API key no `config.js`

**Abre mas não guarda nada**
→ Normal se abrires diretamente do ficheiro. Usa um servidor local:
```bash
# Se tiveres Python instalado:
python -m http.server 8000
# Abre http://localhost:8000
```

**Não consigo instalar como app**
→ Precisa estar num servidor (não funciona abrindo o ficheiro diretamente)

---

## 🧠 Para quem é isto?

✅ Gestores de produto com backlog infinito
✅ Marketers a escolher entre 20 campanhas
✅ Founders a priorizar features
✅ Qualquer pessoa cansada de decidir "à sorte"

---

## 🔒 Privacidade

- Tudo fica no teu dispositivo
- A IA só vê o que tu envias (e não guarda nada)
- Zero tracking
- Zero analytics
- Código aberto - podes ver tudo

---

**Feito com ☕ e frustração com ferramentas complicadas**
