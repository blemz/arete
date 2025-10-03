# Diagrama de Arquitetura do Sistema Arete

## 1. Arquitetura Completa (Slide 3 e 5)

### Versão Mermaid (Para Renderização)

```mermaid
graph TB
    subgraph "Interface do Usuário"
        UI[Reflex Web UI<br/>React + Python]
        CLI[CLI Interface<br/>chat_rag_clean.py]
    end

    subgraph "Pipeline RAG"
        QP[Processamento de Consulta<br/>Análise + Embedding]
        VS[Busca Vetorial<br/>Weaviate]
        GS[Busca em Grafo<br/>Neo4j]
        CA[Montagem de Contexto<br/>Top-K Results]
        LLM[Geração LLM<br/>Multi-Provedor]
        CV[Verificação de Citações<br/>Cross-reference]
    end

    subgraph "Serviços de Embedding"
        ES[EmbeddingService]
        OAI[OpenAI<br/>text-embedding-3-small]
        OR[OpenRouter<br/>Múltiplos modelos]
        GEM[Gemini<br/>text-embedding-004]
        OLL[Ollama<br/>Local/Gratuito]
    end

    subgraph "Provedores LLM"
        OPENAI[OpenAI<br/>GPT-4o, GPT-5-mini]
        OPENR[OpenRouter<br/>100+ modelos]
        GEMINI[Google Gemini<br/>Pro, Ultra]
        CLAUDE[Anthropic Claude<br/>Sonnet, Opus]
        OLLAMA[Ollama<br/>Llama, Gemma, Phi]
    end

    subgraph "Armazenamento"
        NEO[(Neo4j<br/>Grafo de Conhecimento<br/>83 entidades<br/>109 relacionamentos)]
        WEAV[(Weaviate<br/>Banco Vetorial<br/>227 chunks<br/>1536d embeddings)]
        REDIS[(Redis<br/>Cache<br/>Sessões)]
    end

    subgraph "Processamento de Dados"
        ING[Ingestão<br/>ingest_restructured_text.py]
        CHUNK[Chunking Semântico<br/>200-300 palavras]
        NER[Extração de Entidades<br/>LLM + Regex]
        REL[Extração de Relacionamentos<br/>Graph Transformer]
        EMB[Geração de Embeddings<br/>Batch 100]
    end

    %% Fluxo de Consulta
    UI --> QP
    CLI --> QP
    QP --> ES
    ES --> OAI
    ES --> OR
    ES --> GEM
    ES --> OLL
    QP --> VS
    QP --> GS
    VS --> WEAV
    GS --> NEO
    VS --> CA
    GS --> CA
    CA --> LLM
    LLM --> OPENAI
    LLM --> OPENR
    LLM --> GEMINI
    LLM --> CLAUDE
    LLM --> OLLAMA
    LLM --> CV
    CV --> NEO
    CV --> WEAV
    CV --> UI
    CV --> CLI

    %% Fluxo de Ingestão
    ING --> CHUNK
    CHUNK --> NER
    NER --> REL
    REL --> NEO
    CHUNK --> EMB
    EMB --> ES
    EMB --> WEAV
    NER --> NEO

    %% Cache
    CA -.-> REDIS
    VS -.-> REDIS
    GS -.-> REDIS

    style UI fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#fff
    style CLI fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#fff
    style NEO fill:#00A8E1,stroke:#006B8F,stroke-width:3px,color:#fff
    style WEAV fill:#00D4AA,stroke:#008C6F,stroke-width:3px,color:#fff
    style REDIS fill:#D82C20,stroke:#8A1C14,stroke-width:2px,color:#fff
    style LLM fill:#9B59B6,stroke:#6C3483,stroke-width:2px,color:#fff
    style CV fill:#27AE60,stroke:#1E8449,stroke-width:2px,color:#fff
```

---

## 2. Fluxo de Pipeline RAG Simplificado (Slide 5)

```mermaid
graph LR
    A[👤 Pergunta do Usuário<br/>'O que é virtude?'] --> B[⚡ Embedding<br/>1536 dimensões]
    B --> C[🔍 Busca Vetorial<br/>227 chunks<br/>Top 5 resultados]
    C --> D[🏛️ Consulta Grafo<br/>83 entidades<br/>Relacionamentos]
    D --> E[📝 Contexto Montado<br/>~5000 tokens]
    E --> F[🧠 GPT-5-mini<br/>Raciocínio 25-35s]
    F --> G[✅ Verificação<br/>Citações validadas]
    G --> H[📖 Resposta Estruturada<br/>+ Citações + Scores]

    style A fill:#E8F4F8,stroke:#4A90E2,stroke-width:2px
    style B fill:#FFF4E6,stroke:#F39C12,stroke-width:2px
    style C fill:#E8F8F5,stroke:#00D4AA,stroke-width:2px
    style D fill:#EBF5FB,stroke:#00A8E1,stroke-width:2px
    style E fill:#F4ECF7,stroke:#9B59B6,stroke-width:2px
    style F fill:#FADBD8,stroke:#E74C3C,stroke-width:2px
    style G fill:#D5F4E6,stroke:#27AE60,stroke-width:2px
    style H fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px
```

---

## 3. Arquitetura Multi-Provedor (Slide 6)

```mermaid
graph TD
    ARETE[🏛️ Sistema Arete<br/>Intelligent Router]

    ARETE --> OAI[OpenAI<br/>GPT-4o, GPT-5-mini<br/>$$$]
    ARETE --> OPR[OpenRouter<br/>100+ modelos<br/>$$]
    ARETE --> GEM[Google Gemini<br/>Pro, Ultra<br/>$$]
    ARETE --> CLA[Anthropic Claude<br/>Sonnet, Opus<br/>$$$]
    ARETE --> OLL[Ollama<br/>Llama, Gemma, Phi<br/>GRÁTIS]

    OAI -.-> |Fallback| OPR
    OPR -.-> |Fallback| GEM
    GEM -.-> |Fallback| CLA
    CLA -.-> |Fallback| OLL

    OAI --> RES[Resposta Final]
    OPR --> RES
    GEM --> RES
    CLA --> RES
    OLL --> RES

    style ARETE fill:#9B59B6,stroke:#6C3483,stroke-width:3px,color:#fff,font-size:16px
    style OAI fill:#10A37F,stroke:#0D8C6F,stroke-width:2px,color:#fff
    style OPR fill:#FF6B6B,stroke:#CC5555,stroke-width:2px,color:#fff
    style GEM fill:#4285F4,stroke:#3367D6,stroke-width:2px,color:#fff
    style CLA fill:#CC785C,stroke:#A35F4A,stroke-width:2px,color:#fff
    style OLL fill:#000000,stroke:#333333,stroke-width:2px,color:#fff
    style RES fill:#27AE60,stroke:#1E8449,stroke-width:2px,color:#fff
```

### Benefícios Visualizados

```
💰 Otimização de Custos
   ┌─────────────────────────────┐
   │ OpenAI GPT-5: $0.03/1K tok  │ ← Raciocínio complexo
   │ OpenRouter: $0.001/1K tok   │ ← Consultas simples
   │ Ollama: GRÁTIS              │ ← Modo offline
   └─────────────────────────────┘

🔄 Confiabilidade
   ┌─────────────────────────────┐
   │ Provedor 1 indisponível → 2 │
   │ Provedor 2 rate-limit → 3   │
   │ Provedor 3 timeout → 4      │
   │ Provedor 4 falha → 5 (local)│
   └─────────────────────────────┘
   Uptime: 99.9%+

🎯 Especialização
   ┌─────────────────────────────┐
   │ GPT-5-mini: Filosofia       │
   │ Claude: Análise argumento   │
   │ Gemini: Multilíngue         │
   │ Llama3: Rápido/offline      │
   └─────────────────────────────┘
```

---

## 4. Pipeline de Ingestão (Slide 13)

```mermaid
graph TB
    START[📄 Texto Original<br/>PDF ou Markdown]

    START --> REST[🤖 Reestruturação AI<br/>PhilosophicalTextRestructurer]
    REST --> META[📋 Extração de Metadados<br/>YAML front-matter]
    META --> CHUNK[✂️ Chunking Semântico<br/>200-300 palavras]

    CHUNK --> NER[🏷️ Extração de Entidades<br/>LLM Graph Transformer]
    CHUNK --> EMB[🧮 Geração de Embeddings<br/>OpenAI 1536d]

    NER --> REL[🔗 Mapeamento de Relacionamentos<br/>Análise contextual]

    REL --> NEO[(Neo4j<br/>Grafo)]
    EMB --> WEAV[(Weaviate<br/>Vetores)]
    META --> NEO
    CHUNK --> WEAV

    NEO --> DONE[✅ Ingestão Completa]
    WEAV --> DONE

    style START fill:#E8F4F8,stroke:#4A90E2,stroke-width:2px
    style REST fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px
    style META fill:#FADBD8,stroke:#E74C3C,stroke-width:2px
    style CHUNK fill:#D5F4E6,stroke:#27AE60,stroke-width:2px
    style NER fill:#EBF5FB,stroke:#00A8E1,stroke-width:2px
    style EMB fill:#E8F8F5,stroke:#00D4AA,stroke-width:2px
    style REL fill:#F4ECF7,stroke:#9B59B6,stroke-width:2px
    style NEO fill:#00A8E1,stroke:#006B8F,stroke-width:3px,color:#fff
    style WEAV fill:#00D4AA,stroke:#008C6F,stroke-width:3px,color:#fff
    style DONE fill:#27AE60,stroke:#1E8449,stroke-width:3px,color:#fff
```

### Estatísticas do Pipeline

```
📊 Métricas de Processamento (Apologia + Charmides)

ENTRADA:
├─ 2 documentos PDF
├─ 51.383 palavras totais
└─ ~120 páginas

PROCESSAMENTO:
├─ Reestruturação AI: ~15 minutos
├─ Chunking: 227 chunks criados
├─ NER: 83 entidades extraídas
├─ Relacionamentos: 109 mapeados
└─ Embeddings: ~3 minutos (batch 100)

SAÍDA:
├─ Neo4j: 83 nós + 109 arestas
├─ Weaviate: 227 objetos vetoriais
└─ Tempo total: ~20 minutos
```

---

## 5. Grafo de Conhecimento Exemplo (Slide 7)

```mermaid
graph TD
    VIRTUE[Virtude<br/>ἀρετή - arete<br/>Conceito Central]

    VIRTUE -->|is_example_of| TEMP[Temperança<br/>σωφροσύνη - sophrosyne]
    VIRTUE -->|is_example_of| WIS[Sabedoria<br/>σοφία - sophia]
    VIRTUE -->|is_example_of| COUR[Coragem<br/>ἀνδρεία - andreia]
    VIRTUE -->|is_example_of| JUST[Justiça<br/>δικαιοσύνη - dikaiosyne]

    TEMP -->|requires| SELF[Autoconhecimento<br/>γνῶθι σεαυτόν]
    WIS -->|leads_to| KNOW[Conhecimento<br/>ἐπιστήμη - episteme]
    JUST -->|creates| HARM[Harmonia da Alma<br/>ψυχῆς ἁρμονία]

    SELF -->|inscribed_at| DELPH[Delfos<br/>Oráculo]

    SOC[Sócrates<br/>Φιλόσοφος] -->|teaches| VIRTUE
    SOC -->|exemplifies| TEMP
    SOC -->|pursues| WIS

    PLATO[Platão<br/>Φιλόσοφος] -->|student_of| SOC
    PLATO -->|writes_about| VIRTUE

    CHARM[Charmides<br/>Διάλογος] -->|discusses| TEMP
    APOL[Apologia<br/>Διάλογος] -->|discusses| WIS

    style VIRTUE fill:#9B59B6,stroke:#6C3483,stroke-width:4px,color:#fff,font-size:16px
    style TEMP fill:#E74C3C,stroke:#C0392B,stroke-width:3px,color:#fff
    style WIS fill:#3498DB,stroke:#2980B9,stroke-width:3px,color:#fff
    style COUR fill:#F39C12,stroke:#E67E22,stroke-width:3px,color:#fff
    style JUST fill:#27AE60,stroke:#229954,stroke-width:3px,color:#fff
    style SOC fill:#E8F4F8,stroke:#4A90E2,stroke-width:2px
    style PLATO fill:#E8F4F8,stroke:#4A90E2,stroke-width:2px
    style CHARM fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px
    style APOL fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px
```

### Tipos de Relacionamentos

```
🔗 Tipos de Edges no Grafo:

CONCEITUAIS:
├─ is_example_of: Conceito específico → Conceito geral
├─ requires: Conceito A precisa de Conceito B
├─ leads_to: Conceito A resulta em Conceito B
├─ contradicts: Conceito A ↔ Conceito B (incompatíveis)
└─ synthesizes: Conceito C = Conceito A + Conceito B

AUTORAIS:
├─ writes_about: Autor → Conceito
├─ discusses: Diálogo → Conceito
├─ exemplifies: Pessoa → Virtude
├─ teaches: Professor → Conceito
└─ student_of: Aluno → Professor

TEXTUAIS:
├─ appears_in: Conceito → Texto (frequência)
├─ mentioned_with: Conceito A co-ocorre Conceito B
└─ defined_as: Conceito → Definição

TEMPORAIS:
├─ precedes: Evento A antes de Evento B
├─ influences: Filósofo A → Filósofo B
└─ evolves_to: Conceito versão 1 → versão 2
```

---

## 6. Roadmap de Corpus (Slide 14)

```mermaid
gantt
    title Expansão do Corpus Filosófico 2025-2027
    dateFormat YYYY-MM-DD
    section Fase Atual
    Corpus Base (Platão) :done, fase8, 2024-01-01, 2025-01-15

    section Fase 9
    República :active, fase9a, 2025-04-01, 60d
    Meno :fase9b, 2025-04-15, 45d
    Fédon :fase9c, 2025-05-01, 50d
    Simpósio :fase9d, 2025-05-15, 45d

    section Fase 10
    Ética a Nicômaco :fase10a, 2025-07-01, 70d
    Metafísica :fase10b, 2025-07-20, 65d
    Política :fase10c, 2025-08-10, 60d

    section Fase 11
    Estoicos :fase11a, 2025-10-01, 60d
    Pré-Socráticos :fase11b, 2025-10-20, 50d

    section Fase 12
    Agostinho :fase12a, 2026-01-01, 70d
    Aquino :fase12b, 2026-02-01, 60d
    Descartes :fase12c, 2026-03-01, 40d
    Kant :fase12d, 2026-03-20, 50d
```

### Crescimento do Corpus

```
📈 Projeção de Crescimento

JAN 2025 (Atual):
├─ Palavras: 51.383
├─ Chunks: 227
├─ Entidades: 83
└─ Relacionamentos: 109

JUL 2025 (Fim Fase 9):
├─ Palavras: 246.383 (+380%)
├─ Chunks: 1.217 (+436%)
├─ Entidades: 283 (+241%)
└─ Relacionamentos: 409 (+275%)

DEZ 2025 (Fim Fase 10):
├─ Palavras: 536.383 (+944%)
├─ Chunks: 2.677 (+1079%)
├─ Entidades: 533 (+541%)
└─ Relacionamentos: 809 (+642%)

JUN 2026 (Fim Fase 12):
├─ Palavras: 958.383 (+1765%)
├─ Chunks: 4.787 (+2008%)
├─ Entidades: 733 (+783%)
└─ Relacionamentos: 1.209 (+1009%)

2027+ (Visão):
├─ Palavras: 1.000.000+
├─ Chunks: 5.000+
├─ Entidades: 1.000+
└─ Relacionamentos: 2.000+
```

---

## 7. Instruções para Criação Visual

### Para PowerPoint/Google Slides:

1. **Copiar Mermaid Code** → Colar em https://mermaid.live
2. **Exportar como PNG** (alta resolução)
3. **Inserir em slide** mantendo proporções
4. **Adicionar anotações** se necessário

### Para Diagramas Customizados:

**Ferramenta Recomendada:** draw.io (diagrams.net)

**Paleta de Cores Arete:**
```
Primárias:
- Roxo Principal: #9B59B6
- Azul Neo4j: #00A8E1
- Verde Weaviate: #00D4AA

Secundárias:
- Azul Claro: #4A90E2
- Verde Sucesso: #27AE60
- Amarelo Aviso: #F1C40F
- Vermelho Erro: #E74C3C

Neutros:
- Cinza Escuro: #34495E
- Cinza Médio: #7F8C8D
- Cinza Claro: #ECF0F1
- Branco: #FFFFFF
```

**Fontes:**
- Títulos: **Inter Bold** ou **Roboto Bold**
- Corpo: **Inter Regular** ou **Roboto Regular**
- Código: **Fira Code** ou **JetBrains Mono**
- Grego: **New Athena Unicode** ou **GFS Didot**

---

## 8. Assets Adicionais Necessários

### Screenshots a Capturar:

1. **Reflex UI - Chat Interface** (Slide 4)
   - URL: http://localhost:3000
   - Resolução: 1920x1080
   - Mostrar: Conversa completa com resposta

2. **Reflex UI - Document Viewer** (Slide 4)
   - Split view: chat + documento
   - Highlight em citação

3. **Neo4j Browser** (Slide 7)
   - URL: http://localhost:7474
   - Query: `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 50`
   - Layout: Force-directed graph

4. **CLI Output** (Slide 12)
   - Terminal com fundo escuro
   - Comando + resposta completa
   - Font size: 14pt para legibilidade

### Icons e Logos:

Baixar logos oficiais de:
- OpenAI (logo + wordmark)
- OpenRouter
- Google Gemini
- Anthropic Claude
- Ollama
- Neo4j
- Weaviate
- Reflex

**Fonte:** Sites oficiais ou brandfetch.com

---

**Criado em:** 2025-01-03
**Versão:** 1.0 PT-BR
**Formato:** Markdown + Mermaid
**Uso:** Apresentação Arete - Diagramas de Arquitetura
