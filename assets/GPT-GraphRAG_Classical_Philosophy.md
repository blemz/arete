# GraphRAG for Classical Philosophy with LangChain & Neo4j

Building a **GraphRAG** (Graph Retrieval-Augmented Generation) system
for classical philosophical texts involves an LLM-driven pipeline that
automatically extracts entities and relations and stores them in a Neo4j
knowledge graph. Best practice is to break the text into manageable
chunks (with overlap) and use a structured prompt to guide the LLM to
output nodes and edges in JSON or similar
format【23†L375-L384】【14†L45-L49】. For example, one can define node
types (e.g. *Person*, *Concept*, *Work*, *School*) and relation types
(e.g. `TEACHES`, `INFLUENCES`, `AUTHORED`) and instruct the model to
"Extract each entity with its type and relationships (including
direction and a brief description) from the text." Providing a detailed
schema and few-shot examples helps ensure
consistency【11†L264-L273】【16†L414-L421】. After extraction, perform
**entity disambiguation**: group duplicate or synonymous nodes and merge
them (for instance, recognizing that "Socrates" and "the philosopher
Socrates" are the same). This can be done via a second LLM pass or
clustering algorithm【23†L418-L425】【38†L105-L112】.

-   **Pipeline steps**: (1) *Chunk text* into 1000--2000 token segments
    (with overlap) so that the LLM can process
    context【23†L384-L392】. (2) *Extract entities/relations* with an
    LLM prompt that returns structured JSON or Pydantic objects
    (LangChain's function calling helps
    here)【14†L107-L116】【11†L264-L273】. (3) *Entity resolution*: have
    the LLM or code merge duplicates and reconcile differing property
    values【23†L411-L418】. (4) *Import into Neo4j*: translate each JSON
    node/edge into Cypher `MERGE` statements.

-   **Example guidance**: The Neo4j GraphRAG pipeline uses prompts like:

        Extract entities (nodes) and their types from the following text, and list all relationships between them. Return JSON with {"nodes":[{"id": "...", "label": "<type>", "properties":{"name": "..."}}], "relationships":[{"type": "...", "start": "...", "end": "...", "properties":{"details": "..."}}]}.
        Use only these node labels and rel-types: {schema}. 
        Examples: {examples}. Input: {text}

    This ensures the LLM outputs valid graph
    triples【11†L264-L273】【16†L414-L421】.

-   **Special notes for philosophy**: Classical texts often use
    dialogues and archaic phrasing. You may first apply coreference
    resolution (e.g. link pronouns to speakers) so the LLM sees
    "Socrates" rather than "he." Also include in the prompt the context
    that these are philosophical works: e.g. "The text is from Plato's
    *Republic*." This primes the model to expect philosophical terms and
    figures.

# Domain-Specific Models and Prompting

... (truncated for brevity in code)
