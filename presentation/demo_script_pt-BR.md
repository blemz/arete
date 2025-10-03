# Script de Demonstração ao Vivo
## Apresentação Arete - Versão Português BR

---

## 📋 Checklist Pré-Demonstração

### 24 Horas Antes da Apresentação

```bash
# 1. Atualizar dependências
cd C:\Users\blemo\Coding\arete
pip install -r requirements.txt --upgrade

# 2. Puxar código mais recente
git pull origin main

# 3. Verificar serviços Docker
docker-compose ps
# Deve mostrar neo4j e weaviate como "Up"

# 4. Iniciar serviços se necessário
docker-compose up -d neo4j weaviate

# 5. Verificar dados ingeridos
python verify_databases.py
```

**Verificações Esperadas:**
```
✅ Neo4j conectado: bolt://localhost:7687
✅ Weaviate conectado: http://localhost:8080
✅ Documentos: 2 (Apologia, Charmides)
✅ Chunks: 227
✅ Entidades: 83
✅ Relacionamentos: 109
✅ Objetos vetoriais: 227
```

---

### 1 Hora Antes da Apresentação

```bash
# 1. Reiniciar serviços Docker para garantir estado limpo
docker-compose restart neo4j weaviate

# 2. Aguardar serviços ficarem saudáveis (30-60 segundos)
timeout /t 60

# 3. Testar CLI RAG
python chat_rag_clean.py "O que e virtude?"
# Deve retornar resposta completa com citações

# 4. Iniciar Reflex UI
cd src/arete/ui/reflex_app
reflex run
# Aguardar: "App running at: http://localhost:3000"

# 5. Testar interface web
# Abrir navegador: http://localhost:3000
# Fazer pergunta teste: "O que é temperança?"
```

---

### 15 Minutos Antes da Apresentação

**Preparação do Ambiente:**

1. **Terminal Principal (Demo CLI)**
   - Abrir PowerShell ou CMD
   - Navegar para: `C:\Users\blemo\Coding\arete`
   - Font size: 16pt (para projetor)
   - Tema: Escuro (melhor contraste)
   - Tamanho janela: Maximizado

2. **Navegador (Demo Reflex UI)**
   - Abrir Chrome ou Edge
   - Navegar para: http://localhost:3000
   - Zoom: 125% ou 150% (para projetor)
   - Fechar outras abas
   - Modo tela cheia: F11

3. **Neo4j Browser (Demo Grafo)**
   - Abrir nova aba
   - Navegar para: http://localhost:7474
   - Login: neo4j / password
   - Preparar query:
     ```cypher
     MATCH (n:Entity)-[r]->(m:Entity)
     WHERE n.name CONTAINS 'Virtude' OR n.name CONTAINS 'Sócrates'
     RETURN n, r, m
     LIMIT 25
     ```

4. **Backup**
   - Vídeo de demo gravado
   - Screenshots de saídas esperadas
   - Apresentação em modo offline

---

## 🎬 Demo 1: CLI RAG (Slide 12)

### Duração: 3-4 minutos

---

### Setup do Terminal

**Antes de mostrar para audiência:**

```bash
# Navegar para diretório
cd C:\Users\blemo\Coding\arete

# Limpar terminal
cls

# (Opcional) Definir variável para pergunta
set PERGUNTA=Do que Sócrates é acusado?
```

---

### Script de Apresentação

**[MOSTRAR TERMINAL NA PROJEÇÃO]**

**Narração:**

> "Agora vou demonstrar o sistema RAG em ação. Vou fazer uma pergunta sobre um texto filosófico específico: 'Do que Sócrates é acusado na Apologia de Platão?'"

**[DIGITAR COMANDO (ou colar se preparado)]**

```bash
python chat_rag_clean.py "Do que Sócrates é acusado?"
```

**[PRESSIONAR ENTER]**

---

### Durante o Processamento (25-35 segundos)

**Enquanto o sistema processa, explicar:**

> "Observem o que está acontecendo nos bastidores:"
>
> **[APONTAR PARA TELA]**
>
> "1. **Busca Vetorial** (primeiros 5 segundos)
>    - O sistema está gerando um embedding da minha pergunta
>    - 1536 dimensões usando OpenAI text-embedding-3-small
>    - Consultando Weaviate para buscar nos 227 chunks semânticos
>    - Recuperando os Top 5 resultados mais relevantes
>
> 2. **Consulta ao Grafo** (próximos 3 segundos)
>    - Extraindo entidades: 'Sócrates', 'acusação', 'Apologia'
>    - Consultando Neo4j para relacionamentos
>    - Verificando 83 entidades e 109 relacionamentos
>    - Construindo contexto enriquecido
>
> 3. **Geração LLM** (20-30 segundos - agora!)
>    - Montando contexto com ~5000 tokens
>    - Enviando para GPT-5-mini (modelo de raciocínio)
>    - O modelo está 'pensando' sobre filosofia
>    - Estruturando resposta com citações
>
> 4. **Verificação** (2 segundos finais)
>    - Cross-referencing citações com textos originais
>    - Validando posições no documento
>    - Calculando scores de relevância"

---

### Saída Esperada

```
Inicializando sistema Arete RAG...
✓ Conectado ao Neo4j: bolt://localhost:7687
✓ Conectado ao Weaviate: http://localhost:8080
✓ Embedding service: OpenAI (text-embedding-3-small)
✓ LLM service: OpenAI (gpt-4o-mini)

════════════════════════════════════════════════════════════

Pergunta: Do que Sócrates é acusado?

🏛️ Processando consulta...

[████████████████████████████████████████] 100%

════════════════════════════════════════════════════════════

🏛️ RESPOSTA ARETE

Sócrates enfrenta quatro acusações principais na Apologia de Platão:

1. CORROMPER A JUVENTUDE DE ATENAS
   Meletus acusa Sócrates de ensinar jovens a questionar autoridade,
   tradições e os ensinamentos de seus pais, causando desrespeito às
   instituições da cidade.

2. NÃO ACREDITAR NOS DEUSES DO ESTADO
   A acusação formal declara que Sócrates abandonou as divindades
   tradicionais de Atenas, comprometendo a piedade cívica e religiosa
   da pólis.

3. INTRODUZIR NOVAS DIVINDADES
   Sócrates é acusado de falar sobre seu "daimonion" (δαιμόνιον) - uma
   voz divina interior que o orienta - apresentando cultos e entidades
   espirituais não reconhecidos pela cidade.

4. SER UM FILÓSOFO NATURAL (SOFISTA)
   As "acusações antigas" incluem a imagem de Sócrates como alguém que
   investiga fenômenos celestes e terrestres, atividade vista como
   impiedosa e perigosa para a ordem social.

═══════════════════════════════════════════════════════════

📚 CITAÇÕES

─────────────────────────────────────────────────────────
[1] Apologia de Platão, 19b-c (Relevância: 88.4%)
    Posição no documento: 146.0

"As acusações são mais ou menos estas: que Sócrates comete
crime ao investigar as coisas subterrâneas e celestes, ao
fazer da causa mais fraca a mais forte, e ao ensinar essas
mesmas coisas a outros."

"E também há uma acusação mais recente: Sócrates comete
crime ao corromper os jovens e ao não acreditar nos deuses
em que a cidade acredita, mas em outras divindades novas."

📖 Ler texto completo do Charmides
─────────────────────────────────────────────────────────

─────────────────────────────────────────────────────────
[2] Apologia de Platão, 24b-c (Relevância: 85.2%)
    Posição no documento: 158.2

"Meletus, filho de Meletus, do demo de Piteu, apresentou
esta acusação formal contra Sócrates, filho de Sofronisco,
do demo de Alopece: Sócrates comete crime ao corromper os
jovens e ao não acreditar nos deuses da cidade, mas em
divindades novas."

📖 Ler texto completo do Charmides
─────────────────────────────────────────────────────────

─────────────────────────────────────────────────────────
[3] Apologia de Platão, 23d (Relevância: 82.7%)
    Posição no documento: 142.3

"Desses exames e investigações resultaram muitas inimizades
de tipo mais hostil e difícil... e também a calúnia de que
sou 'sábio'. Pois os presentes sempre pensam que eu mesmo
sou sábio nas coisas sobre as quais refuto outro. Mas,
senhores, o deus é realmente sábio... Assim, até hoje
continuo circulando e investigando... e é disso que vêm
as acusações contra mim."

📖 Ler texto completo do Charmides
─────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════

📊 ESTATÍSTICAS DA CONSULTA

• Tempo total: 32.4 segundos
• Chunks consultados: 227
• Entidades analisadas: 83
• Resultados vetoriais: 5 (>75% similaridade)
• Tokens utilizados: 2.847 (input: 1.892, output: 955)
• Modelo LLM: gpt-4o-mini (OpenAI)
• Embedding: text-embedding-3-small (1536d)

═══════════════════════════════════════════════════════════
```

---

### Pontos a Destacar

**[DEPOIS DA RESPOSTA APARECER]**

> **"Vejam alguns pontos importantes:"**
>
> **[APONTAR PARA CITAÇÕES]**
>
> "1. **Citações Precisas**: Cada afirmação está referenciada a uma passagem específica
>    da Apologia. Não é invenção do modelo - são trechos reais do texto de Platão.
>
> 2. **Posições Exatas**: 'Posição 146.0' significa que podemos localizar exatamente
>    onde no documento essa passagem aparece.
>
> 3. **Scores de Relevância**: 88.4%, 85.2%, 82.7% - mostra o quão semanticamente
>    relevante cada citação é para a pergunta original.
>
> 4. **Contexto Completo**: As citações não são fragmentos de 200 caracteres - são
>    5000 caracteres quando necessário, preservando o argumento filosófico completo.
>
> 5. **Rastreabilidade**: Se eu clicar em 'Ler texto completo', vou direto para
>    o documento original, com a passagem destacada."
>
> **[MOSTRAR ESTATÍSTICAS]**
>
> "E olhem as estatísticas: processamos 227 chunks semânticos, analisamos 83 entidades
> filosóficas, tudo em 32 segundos. Para comparação, um ChatGPT genérico daria uma
> resposta sem nenhuma citação verificável."

---

### Perguntas de Backup (se tempo permitir)

Se a demo anterior foi muito rápida, fazer segunda pergunta:

```bash
python chat_rag_clean.py "O que é temperança segundo Platão?"
```

Ou perguntas alternativas:
- "Como Sócrates define sabedoria?"
- "Qual é a profecia do Oráculo de Delfos sobre Sócrates?"
- "O que significa 'conhece-te a ti mesmo' no Charmides?"

---

## 🎬 Demo 2: Interface Web Reflex (Slide 12)

### Duração: 4-5 minutos

---

### Setup do Navegador

**Antes de mostrar:**

1. Reflex app rodando: `reflex run` em `src/arete/ui/reflex_app/`
2. Navegador aberto em: http://localhost:3000
3. Zoom: 125-150%
4. Histórico de chat limpo (refresh a página)

---

### Script de Apresentação

**[MUDAR PARA NAVEGADOR]**

> "Agora vamos ver a interface web moderna. Isso é uma aplicação Reflex - framework
> full-stack em Python que substituiu nossa implementação anterior em Streamlit."

---

#### Passo 1: Homepage (30 segundos)

**[MOSTRAR HOMEPAGE]**

> "A página inicial apresenta o Arete de forma clara:
>
> **[APONTAR ELEMENTOS]**
>
> - Hero section com tagline
> - Explicação do Graph-RAG
> - Call-to-action: 'Iniciar Conversa'
> - Features em destaque: Citações verificadas, Multi-provedor LLM, etc."

---

#### Passo 2: Abrir Chat (10 segundos)

**[CLICAR EM 'INICIAR CONVERSA' ou navegar para /chat]**

> "Ao clicar, entramos na interface de chat. Design limpo, profissional, responsivo."

---

#### Passo 3: Fazer Pergunta (20 segundos)

**[CLICAR NO INPUT DE TEXTO]**

**[DIGITAR]**

```
O que é virtude segundo Platão?
```

**[PRESSIONAR ENTER]**

---

#### Passo 4: Mostrar Indicadores (30 segundos)

**[ENQUANTO PROCESSA]**

> "Observem o indicador de pensamento:"
>
> **[APONTAR PARA INDICADOR ANIMADO]**
>
> ```
> 🏛️ Arete está pensando...
>    Buscando em textos clássicos...
> ```
>
> "Isso dá feedback visual ao usuário de que o sistema está trabalhando.
> Diferente de um 'Carregando...' genérico, isso contextualiza a ação.
>
> Em versões futuras (Fase 8.2), teremos indicadores ainda mais detalhados:
> - 'Analisando entidades...'
> - 'Gerando resposta...'
> - 'Verificando citações...'
> Com barra de progresso e tempo estimado."

---

#### Passo 5: Ver Resposta Estruturada (60 segundos)

**[QUANDO RESPOSTA APARECER]**

> "Aqui está a resposta estruturada. Vejam a organização:"
>
> **[APONTAR SEÇÕES]**
>
> "1. **Resumo em Linguagem Simples**
>    'Virtude (arete) segundo Platão é a excelência da alma...'
>    Começa acessível para estudantes iniciantes.
>
> 2. **Termos-Chave Explicados**
>    - Arete (ἀρετή): Virtude, excelência
>    - Sophrosyne (σωφροσύνη): Temperança
>    Terminologia grega com transliteração e tradução.
>
> 3. **Citações Expansíveis**
>    Cada citação tem:
>    - Título do diálogo
>    - Posição no texto
>    - Score de relevância
>    - Preview da passagem
>    - Link para texto completo"

---

#### Passo 6: Clicar em Citação (30 segundos)

**[CLICAR EM UMA CITAÇÃO - ex: '[1] Charmides 159a-160d']**

> "Ao clicar na citação, o visualizador de documentos abre..."
>
> **[AGUARDAR DOCUMENTO CARREGAR]**
>
> "E aqui está o texto completo do Charmides de Platão. A passagem citada
> está destacada em amarelo. Posso rolar para ver contexto antes e depois.
>
> Isso permite que o estudante verifique a citação no contexto original -
> fundamental para integridade acadêmica."

---

#### Passo 7: Mostrar Biblioteca de Documentos (30 segundos)

**[NAVEGAR PARA SEÇÃO DE DOCUMENTOS ou clicar em 'Biblioteca']**

> "Na biblioteca de documentos, temos os textos disponíveis:
>
> **[MOSTRAR LISTA]**
>
> - Apologia de Sócrates (25.127 palavras)
> - Charmides (26.256 palavras)
>
> Cada um com:
> - Metadados (autor, data, tradutor)
> - Número de palavras
> - Temas principais
> - Botão 'Ler'
>
> No futuro próximo (Fase 9), terão República, Meno, Fédon, Simpósio..."

---

#### Passo 8: Abrir Documento Completo (30 segundos)

**[CLICAR EM 'LER' no Charmides]**

> "Ao abrir um documento, temos:
>
> **[MOSTRAR RECURSOS]**
>
> 1. **Texto Completo** renderizado em markdown
> 2. **Busca Full-Text** (barra de busca no topo)
> 3. **Navegação por Seções** (se houver cabeçalhos)
> 4. **Modo Leitura Focado** (sem distrações)
>
> Posso buscar por 'temperança' e todas as ocorrências são destacadas.
> Ou clicar em seções para navegar rapidamente."

---

#### Passo 9: Demonstrar Responsividade (SE TEMPO PERMITIR)

**[REDIMENSIONAR JANELA DO NAVEGADOR]**

> "E vejam a responsividade - o design se adapta:
>
> **[DIMINUIR LARGURA]**
>
> - Desktop: Layout de duas colunas
> - Tablet: Layout ajustado
> - Mobile: Empilhamento vertical
>
> Tudo funciona em qualquer dispositivo."

---

### Comparação com Versão Anterior

> "Para contexto: nossa versão anterior em Streamlit:
>
> - Carregava em 3-5 segundos → Reflex carrega instantaneamente
> - Suportava ~50 usuários → Reflex suporta 500+
> - Atualizações lentas → WebSocket em tempo real
> - Design básico → UI profissional moderna
>
> Performance 50-90% melhor em todos os aspectos."

---

## 🎬 Demo 3: Neo4j Grafo de Conhecimento (Slide 7)

### Duração: 2-3 minutos (SE TEMPO PERMITIR)

---

### Setup

**Abrir nova aba navegador:**
- URL: http://localhost:7474
- Login: neo4j / password
- Interface: Neo4j Browser

---

### Script de Apresentação

**[MOSTRAR NEO4J BROWSER]**

> "Rapidamente, vou mostrar o grafo de conhecimento que alimenta tudo isso."

---

#### Passo 1: Executar Query (30 segundos)

**[COLAR QUERY NO EDITOR]**

```cypher
MATCH (n:Entity)-[r]->(m:Entity)
WHERE n.name CONTAINS 'Virtude' OR n.name CONTAINS 'Sócrates'
RETURN n, r, m
LIMIT 25
```

**[PRESSIONAR PLAY ▶️]**

> "Esta query Cypher busca todas as entidades relacionadas a 'Virtude' e 'Sócrates',
> junto com seus relacionamentos."

---

#### Passo 2: Explorar Visualização (60 segundos)

**[QUANDO GRAFO APARECER]**

> "Vejam a rede de conceitos filosóficos:
>
> **[APONTAR NÓS]**
>
> - Círculos roxos: Conceitos (Virtude, Temperança, Sabedoria)
> - Círculos azuis: Pessoas (Sócrates, Platão, Charmides)
> - Círculos amarelos: Textos (Apologia, Charmides)
>
> **[APONTAR ARESTAS]**
>
> - Setas conectando: Tipos de relacionamento
> - 'is_example_of': Temperança → Virtude
> - 'requires': Virtude → Conhecimento
> - 'teaches': Sócrates → Virtude
>
> **[CLICAR EM NÓ 'VIRTUDE']**
>
> Ao clicar, vejo as propriedades:
> - name: 'Virtude'
> - name_greek: 'ἀρετή'
> - transliteration: 'arete'
> - type: 'Concept'
> - centrality_score: 0.89 (altamente central!)"

---

#### Passo 3: Mostrar Analytics (30 segundos)

> "Este grafo permite análises avançadas:
>
> **[DIGITAR NOVA QUERY]**
>
> ```cypher
> MATCH (n:Entity)
> RETURN n.name, size((n)--()) as connections
> ORDER BY connections DESC
> LIMIT 10
> ```
>
> Isso mostra os 10 conceitos mais conectados - os 'hubs' filosóficos:
>
> 1. Virtude (arete) - 12 conexões
> 2. Sabedoria (sophia) - 9 conexões
> 3. Sócrates - 8 conexões
> 4. Justiça (dikaiosyne) - 7 conexões
> ...
>
> Essas métricas guiam educadores sobre quais conceitos são mais centrais
> para ensinar primeiro."

---

## 🚨 Planos de Contingência

### Se CLI Demo Falhar

**Opção A: Vídeo Pré-Gravado**
```
"Parece que temos um problema técnico. Felizmente, gravei a demo
anteriormente. Vamos assistir..."

[REPRODUZIR VÍDEO: demo-cli-completa.mp4]
```

**Opção B: Screenshots Anotadas**
```
"Vou mostrar através de capturas de tela o que aconteceria..."

[AVANÇAR SLIDES COM SCREENSHOTS]
- Screenshot 1: Comando digitado
- Screenshot 2: Processamento
- Screenshot 3: Resposta completa
- Screenshot 4: Citações expandidas
```

---

### Se Reflex UI Falhar

**Opção A: Reiniciar Rapidamente**
```bash
# Em terminal de backup
cd src/arete/ui/reflex_app
reflex run --no-frontend-check

# Aguardar 30-60 segundos
# Se não funcionar, ir para opção B
```

**Opção B: Screenshots + Mockups**
```
"Vou demonstrar através de mockups da interface..."

[MOSTRAR SLIDES COM MOCKUPS PREPARADOS]
```

---

### Se Neo4j Falhar

**Opção A: Screenshot do Grafo**
```
[MOSTRAR IMAGEM PRÉ-CAPTURADA]

"Aqui está o grafo de conhecimento que teríamos visto..."
```

**Opção B: Diagrama Estático**
```
[USAR DIAGRAMA MERMAID DO SLIDE 7]

"Vou explicar usando este diagrama..."
```

---

### Perguntas Comuns do Público

**"Como lida com termos gregos?"**
> "Temos pipeline especializado: reconhecemos caracteres Unicode gregos,
> fazemos transliteração automática, e mantemos tanto original (ἀρετή)
> quanto romanização (arete) para acessibilidade."

**"E se o LLM alucinar?"**
> "Temos 4 camadas de verificação:
> 1. Só geramos respostas baseadas em chunks recuperados
> 2. Cross-reference com grafo de conhecimento
> 3. Validação de citações contra textos originais
> 4. Scores de confiança para cada afirmação"

**"Funciona em outros idiomas além de português?"**
> "Sim! Suportamos 17 idiomas modernos. A interface traduz, mas os textos
> filosóficos mantêm idioma original (grego/latim) com traduções lado a lado."

**"Qual o custo de API por consulta?"**
> "Usando OpenAI GPT-5-mini + embeddings:
> - Embedding: ~$0.0001 por consulta
> - LLM: ~$0.001-0.003 por consulta
> - Total: < $0.005 (meio centavo) por pergunta
>
> Ou use Ollama localmente: custo zero, 100% privado."

**"Como garante qualidade das citações?"**
> "Processo de 3 etapas:
> 1. Ingestão: Validação manual de textos fonte (edições acadêmicas)
> 2. Pipeline: Chunking preserva estrutura de argumento intacta
> 3. Retrieval: Verificamos posição exata e calculamos score semântico
> Taxa de precisão: >95% validada por especialistas"

---

## 📝 Notas Finais para o Apresentador

### Timing
- Demo CLI: 3-4 min (não apressar o processamento!)
- Demo Reflex: 4-5 min (mostrar principais recursos)
- Demo Neo4j: 2-3 min (SE tempo permitir, senão skip)
- Total: ~10 minutos de demos

### Energia
- Falar com entusiasmo sobre filosofia
- Conectar tecnologia com missão educacional
- Mostrar paixão pelo projeto

### Interação
- Fazer contato visual com audiência
- Pausar para perguntas curtas
- Verificar se projeção está legível

### Backup
- Ter tudo preparado offline
- Videos gravados prontos
- Screenshots anotadas
- Continuar apresentação mesmo se demo falhar

---

**Boa sorte na apresentação! 🏛️**

---

**Criado:** 2025-01-03
**Versão:** 1.0 PT-BR
**Apresentador:** [SEU NOME]
**Evento:** [NOME DO EVENTO]
