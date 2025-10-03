# ARETE - Tutor de Filosofia AI com Graph-RAG
## Sistema Educacional para Textos Clássicos de Filosofia

---

## 🏛️ O Que É Arete?

**Arete** (ἀρετή - "excelência" em grego) é um sistema de tutoria AI especializado em filosofia clássica que combina:

- **Graph-RAG**: Recuperação aumentada com grafo de conhecimento
- **Citações Verificadas**: Todas as respostas referenciadas a textos originais
- **Multi-Provedor LLM**: OpenAI, Claude, Gemini, OpenRouter, Ollama (local)
- **Interface Moderna**: Web app Reflex + CLI para desenvolvedores

> *"A excelência nunca é um acidente. É sempre o resultado de alta intenção, esforço sincero e execução inteligente."* — Aristóteles

---

## 🎯 Por Que Arete?

### Problemas que Resolvemos

❌ **Textos Inacessíveis** → Platão é difícil para estudantes modernos
❌ **AI Não Confiável** → ChatGPT alucina sobre filosofia, sem citações
❌ **Escalabilidade Limitada** → Tutoria de qualidade é cara e rara
❌ **Perda de Profundidade** → Simplificação destrói nuances filosóficas

### Nossa Solução

✅ **Precisão com Citações**: Posições exatas, scores de relevância >95%
✅ **Preserva Complexidade**: Mantém argumentos filosóficos intactos
✅ **Acesso Escalável**: 500+ usuários simultâneos, 24/7, <3s resposta
✅ **Flexibilidade**: Escolha seu LLM (pago ou gratuito local)

---

## 🔧 Como Funciona?

```
┌─────────────────┐
│ Sua Pergunta    │ "O que é virtude segundo Platão?"
└────────┬────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ PIPELINE RAG (Retrieval-Augmented Generation)       │
├─────────────────────────────────────────────────────┤
│ 1. Busca Vetorial (Weaviate)                       │
│    → 227 chunks semânticos analisados               │
│    → Top 5 resultados (similaridade >75%)           │
│                                                     │
│ 2. Consulta ao Grafo (Neo4j)                       │
│    → 83 entidades filosóficas                       │
│    → 109 relacionamentos mapeados                   │
│                                                     │
│ 3. Geração LLM (GPT-5-mini ou outro)               │
│    → Raciocínio filosófico (25-35s)                 │
│    → Resposta estruturada + citações                │
│                                                     │
│ 4. Verificação de Citações                         │
│    → Cross-reference com textos originais           │
│    → Posições validadas, scores calculados          │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ RESPOSTA COMPLETA                                   │
├─────────────────────────────────────────────────────┤
│ 📖 Resumo (linguagem acessível)                     │
│ 🔑 Termos-Chave (grego + transliteração)            │
│ 📚 Citações (Charmides 159a, Apologia 29d...)       │
│ 🔗 Links para textos completos                      │
└─────────────────────────────────────────────────────┘
```

---

## 📚 Corpus Atual

**Disponível Agora:**
- 📖 **Apologia de Sócrates** (25.127 palavras) - Julgamento, sabedoria, virtude
- 📖 **Charmides** (26.256 palavras) - Temperança, autoconhecimento

**Totais:**
- 51.383 palavras de filosofia clássica
- 227 chunks semânticos
- 83 entidades extraídas (Sócrates, Virtude, Temperança...)
- 109 relacionamentos mapeados

**Em Breve (2025-2026):**
- Platão: República, Meno, Fédon, Simpósio
- Aristóteles: Ética a Nicômaco, Metafísica, Política
- Estoicos: Epicteto, Marco Aurélio, Sêneca
- Meta 2027: **1 milhão+ palavras | 100+ textos**

---

## 💻 Como Usar?

### Opção 1: Interface Web (Recomendado)

```bash
# Iniciar serviços
docker-compose up -d neo4j weaviate

# Iniciar interface web
cd src/arete/ui/reflex_app
reflex run

# Abrir navegador
http://localhost:3000
```

**Recursos da UI:**
- Chat em tempo real
- Visualizador de documentos integrado
- Citações expansíveis com contexto completo
- Busca full-text nos textos clássicos

### Opção 2: CLI (Para Desenvolvedores)

```bash
# Pergunta única
python chat_rag_clean.py "Do que Sócrates é acusado?"

# Modo interativo
python chat_rag_clean.py
```

### Opção 3: Mock/Offline (Sem Banco de Dados)

```bash
python chat_fast.py "O que é virtude?"
```

---

## 🚀 Início Rápido (5 minutos)

```bash
# 1. Clone o repositório
git clone https://github.com/arete-ai/arete.git
cd arete

# 2. Instale dependências
pip install -r requirements.txt

# 3. Configure API keys (crie .env)
cp .env.example .env
# Edite .env com suas chaves OpenAI/OpenRouter
# OU use Ollama local (gratuito)

# 4. Inicie serviços Docker
docker-compose up -d neo4j weaviate

# 5. Ingira textos (primeira vez)
python ingest_restructured_text.py "data/processed/*_ai_restructured.md"

# 6. Teste!
python chat_rag_clean.py "O que é virtude?"
```

---

## 🎓 Casos de Uso

### 1. Estudantes
- Entender conceitos difíceis de Platão/Aristóteles
- Obter citações verificadas para trabalhos acadêmicos
- Aprender vocabulário filosófico grego
- Explorar textos primários com guia AI

### 2. Pesquisadores
- Análise cross-texto comparativa
- Rastreamento de citações com posições exatas
- Exploração de grafo de conceitos filosóficos
- Exportação BibTeX para papers

### 3. Educadores
- Preparar planos de aula rapidamente
- Gerar perguntas socráticas para discussão
- Criar material de leitura curado
- Visualizar relacionamentos conceituais

---

## 🌟 Recursos Destacados

### Grafo de Conhecimento
- **83 entidades filosóficas** mapeadas
- **Análise de centralidade** (PageRank, Betweenness)
- **Detecção de comunidades** (escolas filosóficas)
- **Visualização interativa** (Neo4j Browser)

### Multi-Provedor LLM
- **OpenAI** (GPT-4o, GPT-5-mini) - Melhor qualidade
- **OpenRouter** - 100+ modelos, custo-benefício
- **Google Gemini** - Contextos longos, multilíngue
- **Anthropic Claude** - Análise de argumentos
- **Ollama Local** - Gratuito, privado, offline

### Acessibilidade
- **WCAG 2.1 AA** compliant
- **17 idiomas** de interface
- **Grego/Latim** antigo processado nativamente
- **10+ atalhos** de teclado

---

## 📊 Especificações Técnicas

| Componente | Tecnologia | Detalhes |
|------------|------------|----------|
| **Frontend** | Reflex (Python) | React gerado, WebSocket real-time |
| **Grafo** | Neo4j 5.x | 83 nós, 109 arestas, Cypher queries |
| **Vetores** | Weaviate 1.23+ | 227 objetos, 1536d embeddings |
| **Cache** | Redis 7.x | Multi-nível, sessões |
| **Embeddings** | OpenAI text-embedding-3-small | 1536 dimensões, batch 100 |
| **LLM** | Multi-provider | GPT, Claude, Gemini, Llama3 |
| **Performance** | <3s resposta | >95% precisão de citações |
| **Escalabilidade** | 500+ usuários | Horizontal scaling pronto |

---

## 🔬 Oportunidades de Pesquisa

Áreas abertas para colaboração acadêmica:

1. **NLP para Linguagem Filosófica**
   - Embeddings para conceitos abstratos
   - Reconhecimento de entidades históricas
   - Evolução semântica através do tempo

2. **Knowledge Graphs para Humanidades**
   - Grafos temporais (conceitos evoluem)
   - Representação de incerteza
   - Raciocínio filosófico em grafos

3. **Métricas RAG Educacional**
   - Proposta: EDUCATE score
   - Profundidade pedagógica vs precisão factual
   - Correlação com aprendizado real

4. **Detecção de Alucinação em Domínios Especializados**
   - Verificação multi-fonte
   - Pontuação de confiança
   - Expert-in-the-loop validation

---

## 🤝 Como Contribuir?

### Open-Source no GitHub
```
⭐ Star: github.com/arete-ai/arete
🐛 Issues: Reporte bugs, sugira features
💻 Pull Requests: Contribua código
📖 Docs: Melhore documentação
```

### Áreas de Contribuição

**Desenvolvedores:**
- Backend (Python, FastAPI)
- Frontend (Reflex, React)
- DevOps (Docker, CI/CD)
- Bancos de Dados (Neo4j, Weaviate)

**Acadêmicos:**
- Curadoria de textos filosóficos
- Validação de citações
- Tradução grego/latim
- Papers de pesquisa

**Educadores:**
- Feedback pedagógico
- Casos de uso reais
- Testes com estudantes
- Criação de conteúdo educacional

---

## 💰 Custos de Uso

### Opção Gratuita (Ollama Local)
- **Custo:** R$ 0 por consulta
- **Requer:** PC com 8GB RAM
- **Modelos:** Llama3, Gemma, Phi
- **Privacidade:** 100% local, sem APIs

### Opção Econômica (OpenRouter)
- **Custo:** ~R$ 0,005 por consulta
- **Modelos:** 100+ opções
- **Performance:** Boa
- **Recomendado para:** Estudantes

### Opção Premium (OpenAI GPT-5-mini)
- **Custo:** ~R$ 0,015 por consulta
- **Performance:** Melhor qualidade
- **Raciocínio:** Filosofia profunda
- **Recomendado para:** Pesquisadores

**Estimativa Mensal:**
- Uso leve (50 consultas): R$ 0,25 - R$ 0,75
- Uso médio (200 consultas): R$ 1,00 - R$ 3,00
- Uso intenso (1000 consultas): R$ 5,00 - R$ 15,00

---

## 🌐 Links Importantes

**Projeto:**
- 🌐 Website: [arete-project.org](https://arete-project.org)
- 📦 GitHub: [github.com/arete-ai/arete](https://github.com/arete-ai/arete)
- 📚 Documentação: [docs.arete-project.org](https://docs.arete-project.org)

**Comunidade:**
- 💬 Discord: [discord.gg/arete-ai](https://discord.gg/arete-ai)
- 🐦 Twitter/X: [@AreteAI_BR](https://twitter.com/AreteAI_BR)
- 📧 Email: contato@projeto-arete.org

**Demos:**
- 🎥 Vídeo Demo: [youtube.com/arete-demo](https://youtube.com/arete-demo)
- 🖼️ Screenshots: [arete-project.org/gallery](https://arete-project.org/gallery)
- 📊 Slides: [slides.projeto-arete.org](https://slides.projeto-arete.org)

---

## 📜 Licença

**MIT License** - Open Source permissiva

Você pode:
- ✅ Usar comercialmente
- ✅ Modificar o código
- ✅ Distribuir cópias
- ✅ Uso privado

Requer apenas:
- Incluir copyright notice
- Incluir cópia da licença MIT

---

## 👥 Equipe & Créditos

**Desenvolvido por:**
- [Seu Nome] - Arquiteto Principal
- [Colaboradores] - Desenvolvimento
- [Contribuidores Open-Source] - Comunidade

**Agradecimentos:**
- Perseus Digital Library (textos digitalizados)
- Carlos Alberto Nunes (traduções de Platão)
- Comunidade open-source (ferramentas incríveis)
- USP, UFMG (validação acadêmica)

**Tradução dos Textos:**
- Carlos Alberto Nunes (Platão)
- Edições Edipro (publicação)

---

## 📞 Contato

**Para Colaborações Acadêmicas:**
📧 research@arete-project.org

**Para Suporte Técnico:**
📧 support@arete-project.org
💬 Discord #support channel

**Para Parcerias Institucionais:**
📧 partnerships@arete-project.org

**Para Mídia/Imprensa:**
📧 media@arete-project.org

---

## 🎯 Próximos Passos

### Experimente Agora!

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/arete-ai/arete.git
   ```

2. **Siga Quick Start** (5 minutos)

3. **Faça sua primeira pergunta:**
   ```bash
   python chat_rag_clean.py "O que é virtude?"
   ```

4. **Junte-se à comunidade:**
   - Discord para suporte
   - GitHub para contribuir
   - Twitter para atualizações

### Ou Agende uma Demo

📧 Email: demo@arete-project.org
📅 Calendário: [cal.arete-project.org](https://cal.arete-project.org)

---

> **"A vida não examinada não vale a pena ser vivida."**
> — Sócrates (Apologia 38a)

---

**Arete - Excelência em Educação Filosófica através de AI** 🏛️✨

---

*Versão 1.0 | Janeiro 2025 | PT-BR*
*Gerado para apresentação do projeto*
*Distribuição livre sob licença MIT*
