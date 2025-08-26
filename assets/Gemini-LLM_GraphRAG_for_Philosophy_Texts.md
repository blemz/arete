

# **The Trustworthy GraphRAG Pipeline: A Framework for Secure Knowledge Extraction from Classical Philosophical Texts**

## **1\. The Trustworthy GraphRAG Pipeline: A New Paradigm for Knowledge Extraction**

### **1.1 The Problem Statement: Navigating the Philosophical Lexicon**

The central challenge in creating a knowledge extraction system for classical philosophical texts lies not in the volume of the data, but in its profound semantic complexity. Unlike legal documents or medical journals, which often follow a predictable structure and contain a finite set of well-defined entities and relationships, works by philosophers such as Plato, Socrates, and Aristotle are inherently abstract and dialectical.1 The language is dense, often metaphorical, and laden with nuance, making it challenging for Natural Language Processing (NLP) models to accurately interpret idioms, sarcasm, or subtle contextual cues.2 A simple, one-size-fits-all approach to knowledge extraction is insufficient.

The user's emphasis on "information quality" and "security" demands a re-evaluation of these terms in the context of knowledge graphs. "Security" is not merely about preventing unauthorized access but, more fundamentally, about ensuring the fidelity of the generated knowledge to the source material.3 The system must be robust against the risks of hallucination and misinterpretation, which are particularly pronounced in a domain where "ground truth" is often a matter of scholarly debate rather than empirical fact.4 Therefore, this report proposes a methodology that moves beyond a simple "upload and generate" approach, acknowledging the philosophical nature of the data itself and building a system that is transparent, verifiable, and explainable.

### **1.2 Why a GraphRAG Approach is Uniquely Suited for Philosophy**

Traditional Retrieval-Augmented Generation (RAG) systems, which rely on a flat vector index to retrieve relevant text chunks, are fundamentally limited in their ability to handle the intricate reasoning and interconnected ideas found in philosophy. A vector-only approach can successfully retrieve all mentions of "the good" from Plato's *Republic*, but it would be unable to reason over the hierarchical and causal relationships between "the good" and concepts like "justice," "the Forms," or the "divided line." This is where the GraphRAG paradigm, with a graph database as its core knowledge layer, demonstrates its unique value.

A graph database like Neo4j natively treats relationships as first-class citizens, a design principle that is critical for modeling philosophical concepts.3 Instead of reconstructing connections with complex code or

JOIN operations, the graph model explicitly links entities with typed relationships.5 For example, a

Socrates node can be connected to a Plato node via a DISCIPLES relationship, or an Argument node can be linked to a Concept node via a SUPPORTS relationship. This structured representation allows for sophisticated graph traversals and contextual reasoning that are impossible with a simple similarity search.1 A user could query not just for "Socrates," but for "all arguments presented by Plato that were influenced by Socrates's dialogues on the concept of justice." This capability to perform complex traversals is precisely what is needed to navigate the a-linear, multi-faceted landscape of philosophical discourse.

Furthermore, the very act of building a knowledge graph from these texts aligns with core philosophical disciplines. As noted in research, knowledge graphs make explicit ontological commitments—defining what entities and relationships exist—and epistemological assumptions about how knowledge is structured.6 This process directly mirrors the philosophical study of being and knowledge, making the methodology an intellectually coherent approach to the subject matter.6

## **2\. Building the Foundation: From Unstructured Text to a Structured Knowledge Graph**

### **2.1 The Architectural Blueprint: An Overview of the Pipeline**

The proposed system for reliable knowledge extraction from philosophical texts is not a single tool but a multi-layered architectural pipeline. The process begins with data ingestion and proceeds through LLM-based extraction, graph construction, and, most importantly, a rigorous trust and validation layer. The Neo4j LLM Knowledge Graph Builder offers a robust starting point, providing a user-friendly interface that simplifies the initial steps of the pipeline, from connecting to a Neo4j database to uploading source files and generating the graph.9 This application can be deployed locally, offering greater control and customization over the entire process.10 The core stages of the pipeline are as follows:

* **Data Ingestion:** Sourcing and preparing the philosophical texts.  
* **LLM-based Extraction:** Using an LLM to identify entities and relationships from the text.  
* **Graph Construction:** Populating the Neo4j database with the extracted knowledge.  
* **Trust and Validation Layer:** A critical, multi-stage process to ensure the accuracy and integrity of the extracted information before it is integrated into the final graph. This layer is what differentiates a reliable system from a basic one.  
* **Interaction with the RAG Agent:** The final stage where the constructed knowledge graph is used for advanced querying and reasoning.

### **2.2 Data Ingestion and Source Preparation for Philosophical Texts**

The first step in the pipeline involves ingesting the source material. The Neo4j LLM Knowledge Graph Builder is well-equipped to handle various file formats, including PDF, DOCX, and plain TXT files, as well as web-based sources like Wikipedia pages and web links.9 This flexibility is essential for accommodating the diverse formats of classical philosophical texts, which often exist as digitized documents, scholarly editions, or online articles.

A specific challenge for this domain is the prevalence of dialogue-based works, such as Plato's *Phaedo* or *The Republic*. Extracting entities and relationships from a conversational format is more difficult than from a structured narrative, as multi-speaker context and low information density can complicate the task.12 To address this, a pre-processing step is recommended. Instead of treating the entire document as a monolithic block of text, it can be chunked by speaker or by topic. This approach aligns with methodologies for dialogue-based extraction that integrate knowledge to capture more effective features from the text.12 By creating a structured framework for the LLM, the system can more accurately attribute statements and arguments to the correct philosopher, thereby improving the overall quality of the extracted graph.

### **2.3 Designing a Domain-Specific Philosophical Ontology**

The most critical factor for ensuring high-quality, consistent extraction is the design of a well-defined schema.5 This schema acts as the foundational blueprint for the knowledge graph, dictating what entities and relationships are permissible. A generic schema would be insufficient for this domain. The concepts and relationships in philosophy are highly abstract and require careful, domain-specific definitions.

A proposed schema for classical philosophical texts includes the following node labels and relationship types:

#### **Proposed Philosophical Graph Schema**

| Node Label | Description |
| :---- | :---- |
| **Philosopher** | Represents a key historical figure (e.g., Plato, Socrates). |
| **Concept** | Represents an abstract idea or principle (e.g., Justice, The Forms, Virtue). |
| **Text** | Represents a specific work or dialogue (e.g., *The Republic*, *Nicomachean Ethics*). |
| **Argument** | Represents a specific point, logical premise, or dialectical exchange. |
| **HistoricalEvent** | Represents a significant event in a philosopher's life or the surrounding historical context (e.g., The Peloponnesian War, The Trial of Socrates). |

| Relationship Type | Description |
| :---- | :---- |
| **\--\>** | Indicates one philosopher's work or ideas had an effect on another's. |
| **\--\>** | Indicates a philosopher or text explicitly addresses a particular concept. |
| **\--\>** | Links a specific text or a portion of it to a concept it illustrates. |
| **\--\>** | Links a specific argument to the concept it is meant to uphold or defend. |
| **\--\>** | Links a text to a specific argument presented within it. |

A key capability of the Neo4j Knowledge Graph Builder is its ability to allow an LLM to suggest a schema based on a provided text sample.10 This feature can be used to rapidly prototype the ontology and capture nuances that may be missed during a manual design phase. By providing the LLM with a few pages of text and a verbal description, the system can propose a structured framework that is then refined by the user. This iterative process ensures the data model is robust and accurately reflects the complex domain, addressing the foundational need for a strong data model.

## **3\. Mitigating LLM-Induced Risks: Hallucination, Inconsistency, and Bias**

### **3.1 The Philosophical Hallucination Problem**

The primary risk in using Large Language Models for knowledge extraction is the phenomenon of hallucination, which is the generation of plausible but factually incorrect or unfounded information.4 For a domain as abstract as philosophy, this risk is especially high. An LLM, which operates as a statistical pattern-matching engine, may infer a relationship or attribute a concept to a philosopher that is not explicitly stated in the text.15 For example, a model might incorrectly conclude that a certain historical figure held a specific view simply because it is a common philosophical position for their era, even if the source text does not support this claim. This compromises the integrity of the generated knowledge and transforms the system from a reliable knowledge repository into a source of misinformation. The fundamental problem is that the LLM is "guessing" based on its training data, not grounding its output in the provided source.15 This is compounded by the fact that for philosophical debates, there is no single, clear "ground truth" to check against.4 Therefore, the system must be designed to rigorously vet every extraction to ensure it is directly evidenced by the source material.

### **3.2 Advanced Prompting Techniques for Enhanced Reliability**

To mitigate these risks, the pipeline must employ advanced prompting techniques that move beyond simple instructions.

#### **Few-Shot Prompting as the Standard**

Few-shot prompting provides the LLM with several concrete examples of desired entity and relationship extractions, significantly improving accuracy and consistency compared to a zero-shot approach.16 For complex tasks involving nuanced understanding, few-shot learning offers a more powerful and reliable approach.18 The examples prime the model to the specific task, helping it to understand the required output format and the type of information to extract.

#### **Implementing Chain-of-Verification (CoVe) for Factual Accuracy**

Chain-of-Verification (CoVe) is a powerful self-critique method that reduces hallucinations by forcing the LLM to verify its own work.14 The process involves four steps:

1. **Baseline Response Generation:** The LLM generates a draft of the extracted triples from a text chunk.  
2. **Verification Planning:** The LLM is prompted to create a list of verification questions based on its initial response.  
3. **Verification Execution:** The LLM is then asked to answer each of the verification questions by referencing the original text. For instance, for an extracted triple (Plato)--\>(Justice), the verification question might be: "Does the provided text explicitly state that Plato discussed the concept of Justice?"  
4. **Final Response Generation:** The LLM refines its initial list of triples, retaining only those that were successfully verified in the previous step.

This technique forces the LLM to ground its output directly in the source material, ensuring that extractions are based on explicit evidence rather than plausibility.14 While CoVe does not eliminate all hallucinations, it significantly reduces them and is particularly effective for list-based and long-form content generation tasks, making it ideal for our pipeline.19

#### **Leveraging Universal Self-Consistency (USC) to Improve Coherence**

Universal Self-Consistency (USC) builds upon the concept of self-consistency, which generates multiple outputs from a single prompt and selects the most common or consistent answer.20 Unlike the standard approach, which requires a structured output for a simple majority vote (e.g., a numerical answer), USC is designed for open-ended, free-form tasks, making it well-suited for philosophical texts.21 The methodology involves running the same CoVe-equipped prompt multiple times to generate several candidate sets of triples. The LLM is then prompted to select the most internally consistent and coherent set of triples from the combined outputs.20 This is a crucial step for a domain with no ground truth, as it allows the system to identify the most robust and repeatable extractions, thereby improving the overall quality of the knowledge graph.

### **3.3 Data-Driven LLM Selection**

The choice of LLM is a critical factor in the pipeline's reliability. Empirical studies provide clear guidance on which models exhibit the highest performance and consistency for knowledge extraction tasks. Research on data extraction from electronic health records, a domain that, like ours, requires high accuracy, indicates that certain LLMs exhibit outstanding performance.22

The analysis, which involved assessing consistency over multiple prompt iterations, showed that **Claude 3.0 Opus**, **Claude 3.0 Sonnet**, **GPT-4**, and **Llama 3-70b** demonstrated superior performance across key metrics like accuracy, recall, and precision.22 The following table provides a detailed look at the performance of these models, offering a data-backed justification for their selection.

| LLM Model | Accuracy | Recall | Precision | F1-score |
| :---- | :---- | :---- | :---- | :---- |
| Claude 3.0 Opus | 0.995 | 1 | 0.984 | 0.992 |
| Claude 3.0 Sonnet | 0.988 | 1 | 0.976 | 0.988 |
| GPT-4 | 0.988 | 0.976 | 0.983 | 0.979 |
| Claude 2.1 | 0.986 | 1 | 0.954 | 0.976 |
| Gemini Advanced | 0.982 | 0.96 | 0.983 | 0.971 |
| PaLM 2 chat bison | 0.982 | 0.984 | 0.953 | 0.968 |
| Llama 3-70b | 0.982 | 1 | 0.939 | 0.968 |
| Gemini | 0.957 | 0.92 | 0.958 | 0.938 |
| GPT-3.5 | 0.948 | 0.984 | 0.854 | 0.914 |

The empirical data from this study provides a clear rationale for prioritizing these models. Their consistently high performance and low error rates make them the ideal choice for a pipeline where information quality is paramount. The Neo4j Knowledge Graph Builder supports a variety of LLMs, including OpenAI, Gemini, and Llama 3, allowing the user to configure the system with their preferred model.10

## **4\. Ensuring Data Fidelity: The Validation and Quality Assurance Layer**

### **4.1 The LLM-as-a-Judge Paradigm**

The most significant challenge in building a trustworthy knowledge graph is data validation. Manual annotation and fact-checking are prohibitively expensive and time-consuming.23 To address this, the pipeline must implement an automated validation process, a concept that can be framed as "LLM-as-a-judge." This paradigm leverages the reasoning capabilities of an LLM to evaluate the quality and accuracy of the extractions made by another LLM.23 An LLM is not just a generator; it is a powerful reasoning engine that can be tasked with performing a meta-analysis on the extracted information.25

This approach formalizes the process of automated fact-checking, where an LLM is used to verify the factual accuracy of a statement against a knowledge base.25 It moves beyond simple self-correction, which has been shown to be unreliable in some cases.26 Instead of trusting a single LLM to correct its own mistakes, a separate, designated "judge" LLM is used to evaluate the output, thereby reducing potential bias and enhancing reliability.

### **4.2 The Dual-Validation Framework: A Two-Phase Process**

A single-pass validation is insufficient for a domain where nuance and interpretation are so common. This report proposes a robust, two-phase validation pipeline that mimics the workflow of a human researcher or annotator. This dual-validation mechanism ensures that the knowledge is both internally consistent with the existing graph and externally plausible against a broader set of sources.24

#### **Phase 1: Internal Consistency Validation**

After the initial ingestion and extraction, a designated LLM-as-a-judge agent validates the newly created triples against the existing knowledge graph. This is a critical step that leverages the inherent structure of the graph database. For example, if a new extraction from *The Republic* claims that Socrates taught Aristotle, the judge agent can traverse the graph to find that Aristotle was a student of Plato, and Plato was a student of Socrates. The new triple introduces a contradiction, which the judge agent can flag for manual review. This process prioritizes internal graphical evidence, mirroring the human tendency to first check existing knowledge before seeking external sources.24

#### **Phase 2: External Plausibility Verification**

For extractions that are ambiguous or for which there is no internal evidence, the judge agent can perform an external check. This involves integrating the pipeline with external knowledge sources or tools, such as a web search or academic databases like Connected Papers.28 The judge agent can perform a query to verify the extracted triple against authoritative sources. For example, it could check if the relationship

(Philosopher)--\>(Philosopher) is a widely accepted view in a given field. This "dual-verification" process ensures that only high-confidence, factually accurate predictions are integrated into the final knowledge graph, thereby maintaining its integrity and reducing the need for extensive human curation.24

### **4.3 Ensuring Trust and Integrity within Neo4j**

The foundational layer of data integrity is established within the Neo4j database itself. Unlike traditional relational databases, which rely on foreign keys to enforce referential integrity, Neo4j's native property graph model ensures that a relationship cannot exist without its connected nodes.3 This inherent design feature provides a strong, foundational layer of security from an information quality standpoint.

Beyond this native functionality, the system must also implement data governance measures using Cypher queries. It is possible to define unique constraints on node properties (e.g., Philosopher.name) and to ensure that relationships only exist between specified node labels. This practice, a form of schema enforcement, is a critical layer of data governance.5 As the knowledge graph grows, these constraints ensure its consistency and prevent the ingestion of malformed or inconsistent data. The report recommends a continuous process of data validation and evolution, including automating updates and regularly monitoring query performance as the graph scales.5

## **5\. A Case Study in Action: A Proposed Pipeline for Platonic Dialogues**

This section provides a step-by-step application of the proposed methodology, demonstrating how it would be used to generate a trustworthy knowledge graph from a Platonic dialogue. The example chosen is Plato's *Phaedo*, a work that presents the final hours of Socrates and his arguments for the immortality of the soul.

#### **Step 1: Ingest and Define Initial Schema**

The full text of *Phaedo* is ingested into the system using the Neo4j LLM Knowledge Graph Builder. The initial schema is defined to include the following core elements:

* **Nodes:** Philosopher, Concept, Text, Argument.  
* **Relationships:** DISCUSSED, SUPPORTS.

#### **Step 2: Apply Advanced Prompting for Extraction**

The pre-processed text is then passed to a chosen LLM, such as GPT-4 or Claude 3.0 Opus, selected for their demonstrated reliability and consistency.22 The prompt is crafted using a few-shot approach, with examples of desired extractions. For instance, an example could show how to extract the triple

(Socrates)--\>(Immortality\_of\_the\_Soul).

To ensure factual accuracy and mitigate the risk of hallucination, the prompt is infused with the Chain-of-Verification (CoVe) methodology. After generating a list of candidate triples, the LLM is instructed to ask verification questions for each one, such as, "Does the text explicitly state that Socrates presented the 'Argument from Opposites' to support his claim?" This forces the LLM to ground each extraction in the source text.

#### **Step 3: Refine with Universal Self-Consistency**

The CoVe-enabled prompt is run multiple times to generate several candidate sets of triples. The Universal Self-Consistency (USC) process is then initiated. All of the verified outputs are compiled into a new prompt. The LLM is then asked to select the most consistent and coherent set of triples from the compiled list. This process refines the initial output and selects the most robust set of knowledge to be ingested into the graph.

#### **Step 4: Ingest into Neo4j**

The final, validated set of triples is then ingested into a Neo4j database. This is a crucial step where the knowledge is structured and persisted. Using a tool like the Neo4j LLM Knowledge Graph Builder, the process is streamlined to create the nodes and relationships, thereby forming the initial knowledge graph of the Platonic dialogue.

#### **Step 5: Validate and Ensure Integrity**

The newly ingested knowledge is not yet considered "trusted." A final validation step is performed using the LLM-as-a-judge paradigm. A separate LLM agent is used to check the newly added knowledge for internal consistency and external plausibility. For instance, the judge agent could verify that the arguments presented in *Phaedo* are not attributed to Plato in other documents in the graph and that the core concepts are correctly linked. This final check ensures the integrity of the graph as a whole.

#### **Recommended Toolkit and Configuration**

The proposed pipeline relies on a specific set of tools and configurations:

* **Core LLM:** A top-tier model like **GPT-4** or **Claude 3.0 Opus** is recommended, justified by the empirical data on their high performance and consistency.22  
* **Database:** A Neo4j AuraDB instance provides a managed, scalable solution, or a local Docker deployment of the Neo4j LLM Knowledge Graph Builder can be used for full customization.10  
* **Frameworks:** LangChain's LLM Graph Transformer will be the core of the extraction logic.9  
* **Configuration:** The system is highly configurable. Key parameters like batch size (configurable through the Docker env) and the list of supported LLM models (VITE\_LLM\_MODELS\_PROD) can be customized to suit specific needs and to adapt to new models as they become available.9

## **6\. Conclusion and Future Directions**

### **6.1 Synthesis of Findings and a Call to Action**

The creation of a reliable and secure GraphRAG system for classical philosophical texts is not a simple task that can be solved with a single tool. It is a methodological paradigm that requires a sophisticated, multi-layered approach. The findings presented in this report demonstrate that a trustworthy pipeline must be built on a foundation of a well-defined philosophical ontology, employ advanced prompting techniques like few-shot learning and Chain-of-Verification, and, most importantly, incorporate a rigorous, automated validation layer using the LLM-as-a-judge paradigm. This approach elevates the system from a mere data store to a trustworthy knowledge repository, ensuring that the generated graph is a high-fidelity representation of the source material. The "security" of this system is defined by its ability to prevent and mitigate LLM-induced risks, ensuring the fidelity of the knowledge to the original texts.

### **6.2 Future Research Avenues**

The work does not end with the creation of the knowledge graph. The structured data produced by this pipeline opens up new and exciting avenues for research and analysis.

* **Modeling Philosophical Evolution:** The graph can be used to analyze how abstract concepts evolve across different texts or how one philosopher's work is reinterpreted by another. This is a task uniquely suited for a graph database, as it can model the temporal and causal relationships between ideas.  
* **Reasoning over Abstract Concepts:** Future research can explore how the graph can be used to perform logical inferences that go beyond simple retrieval, helping scholars discover previously unseen connections and insights within the philosophical lexicon.  
* **Ethical Considerations:** It is imperative to acknowledge the ethical implications of creating such a knowledge graph. The process can inadvertently perpetuate biases present in the training data or misinterpret subtle nuances in the source texts.2 A trustworthy system must be transparent about its limitations and the provenance of its knowledge, ensuring that its insights are explainable and verifiable. This ongoing commitment to transparency and accountability is the final, and most critical, component of a truly secure knowledge system.

#### **Referências citadas**

1. From Legal Documents to Knowledge Graphs | by Tomaz Bratanic | Neo4j Developer Blog | Aug, 2025 | Medium, acessado em agosto 26, 2025, [https://medium.com/neo4j/from-legal-documents-to-knowledge-graphs-ccd9cb062320](https://medium.com/neo4j/from-legal-documents-to-knowledge-graphs-ccd9cb062320)  
2. Philosophical Implications of NLP \- Number Analytics, acessado em agosto 26, 2025, [https://www.numberanalytics.com/blog/philosophical-implications-nlp](https://www.numberanalytics.com/blog/philosophical-implications-nlp)  
3. graph databases \- neo4j data integrity? \- Stack Overflow, acessado em agosto 26, 2025, [https://stackoverflow.com/questions/14458670/neo4j-data-integrity](https://stackoverflow.com/questions/14458670/neo4j-data-integrity)  
4. Making Sense of AI: How to Evaluate Entity Extraction using LLM — Part 1 (No Ground Truth\!) | by Albin Thomas | Medium, acessado em agosto 26, 2025, [https://medium.com/@albinthomas231/evaluating-llm-entity-extraction-part-1-no-ground-truth-0443be16f91a](https://medium.com/@albinthomas231/evaluating-llm-entity-extraction-part-1-no-ground-truth-0443be16f91a)  
5. How to Build a Knowledge Graph in 7 Steps \- Graph Database & Analytics \- Neo4j, acessado em agosto 26, 2025, [https://neo4j.com/blog/graph-database/how-to-build-a-knowledge-graph-in-7-steps/](https://neo4j.com/blog/graph-database/how-to-build-a-knowledge-graph-in-7-steps/)  
6. Unlocking Knowledge Graphs in Philosophy \- Number Analytics, acessado em agosto 26, 2025, [https://www.numberanalytics.com/blog/ultimate-guide-knowledge-graph-philosophy-information](https://www.numberanalytics.com/blog/ultimate-guide-knowledge-graph-philosophy-information)  
7. Semantic Web | Linked Data, Ontologies, RDF | Britannica, acessado em agosto 26, 2025, [https://www.britannica.com/topic/Semantic-Web](https://www.britannica.com/topic/Semantic-Web)  
8. The Semantic Web in a philosophical perspective, acessado em agosto 26, 2025, [https://wab.uib.no/agora-alws/article/download/2661/3045](https://wab.uib.no/agora-alws/article/download/2661/3045)  
9. LLM Knowledge Graph Builder Front-End Architecture \- Graph Database & Analytics \- Neo4j, acessado em agosto 26, 2025, [https://neo4j.com/blog/developer/frontend-architecture-and-integration/](https://neo4j.com/blog/developer/frontend-architecture-and-integration/)  
10. Introduction to the Neo4j LLM Knowledge Graph Builder \- Graph Database & Analytics, acessado em agosto 26, 2025, [https://neo4j.com/blog/developer/llm-knowledge-graph-builder/](https://neo4j.com/blog/developer/llm-knowledge-graph-builder/)  
11. neo4j-labs/llm-graph-builder: Neo4j graph construction from unstructured data using LLMs \- GitHub, acessado em agosto 26, 2025, [https://github.com/neo4j-labs/llm-graph-builder](https://github.com/neo4j-labs/llm-graph-builder)  
12. Dialogue-based Entity Relation Extraction with Knowledge – DOAJ, acessado em agosto 26, 2025, [https://doaj.org/article/c9406a9c786c49b2a2cd0bc9654e0b93](https://doaj.org/article/c9406a9c786c49b2a2cd0bc9654e0b93)  
13. Consistent Inference for Dialogue Relation Extraction \- IJCAI, acessado em agosto 26, 2025, [https://www.ijcai.org/proceedings/2021/535](https://www.ijcai.org/proceedings/2021/535)  
14. Chain-of-Verification (CoVe): Reduce LLM Hallucinations \- Learn Prompting, acessado em agosto 26, 2025, [https://learnprompting.org/docs/advanced/self\_criticism/chain\_of\_verification](https://learnprompting.org/docs/advanced/self_criticism/chain_of_verification)  
15. How to Prevent LLM Hallucinations: 5 Proven Strategies \- Voiceflow, acessado em agosto 26, 2025, [https://www.voiceflow.com/blog/prevent-llm-hallucinations](https://www.voiceflow.com/blog/prevent-llm-hallucinations)  
16. Chain of Thought with Explicit Evidence Reasoning for Few-shot Relation Extraction | OpenReview, acessado em agosto 26, 2025, [https://openreview.net/forum?id=sthusQGkef¬eId=6lwlgCklIT](https://openreview.net/forum?id=sthusQGkef&noteId=6lwlgCklIT)  
17. What is few shot prompting? \- IBM, acessado em agosto 26, 2025, [https://www.ibm.com/think/topics/few-shot-prompting](https://www.ibm.com/think/topics/few-shot-prompting)  
18. 0-Shot vs Few-Shot vs Partial-Shot Examples in Language Model Learning, acessado em agosto 26, 2025, [https://promptengineering.org/0-shot-vs-few-shot-vs-partial-shot-examples-in-language-model-learning/](https://promptengineering.org/0-shot-vs-few-shot-vs-partial-shot-examples-in-language-model-learning/)  
19. Chain-Of-VErification (COVE) Explained : r/PromptEngineering \- Reddit, acessado em agosto 26, 2025, [https://www.reddit.com/r/PromptEngineering/comments/1bh610y/chainofverification\_cove\_explained/](https://www.reddit.com/r/PromptEngineering/comments/1bh610y/chainofverification_cove_explained/)  
20. Self-Consistency and Universal Self-Consistency Prompting \- PromptHub, acessado em agosto 26, 2025, [https://www.prompthub.us/blog/self-consistency-and-universal-self-consistency-prompting](https://www.prompthub.us/blog/self-consistency-and-universal-self-consistency-prompting)  
21. Universal Self-Consistency \- Learn Prompting, acessado em agosto 26, 2025, [https://learnprompting.org/docs/advanced/ensembling/universal\_self\_consistency](https://learnprompting.org/docs/advanced/ensembling/universal_self_consistency)  
22. Large language models for data extraction from unstructured and semi-structured electronic health records: a multiple model performance evaluation, acessado em agosto 26, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC11751965/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11751965/)  
23. KGValidator: A Framework for Automatic Validation of Knowledge Graph Construction \- CEUR-WS, acessado em agosto 26, 2025, [https://ceur-ws.org/Vol-3747/text2kg\_paper12.pdf](https://ceur-ws.org/Vol-3747/text2kg_paper12.pdf)  
24. LLM-based Reranking and Validation of Knowledge Graph Completion \- CEUR-WS, acessado em agosto 26, 2025, [https://ceur-ws.org/Vol-3999/paper6.pdf](https://ceur-ws.org/Vol-3999/paper6.pdf)  
25. LLM-based Fact-Checking: A Pipeline for Studying Information Disorder \- CEUR-WS, acessado em agosto 26, 2025, [https://ceur-ws.org/Vol-3962/paper60.pdf](https://ceur-ws.org/Vol-3962/paper60.pdf)  
26. When Can LLMs Actually Correct Their Own Mistakes? A Critical Survey of Self-Correction of LLMs \- ACL Anthology, acessado em agosto 26, 2025, [https://aclanthology.org/2024.tacl-1.78.pdf](https://aclanthology.org/2024.tacl-1.78.pdf)  
27. KGGen: Extracting Knowledge Graphs from Plain Text with ..., acessado em agosto 26, 2025, [https://arxiv.org/abs/2502.09956](https://arxiv.org/abs/2502.09956)  
28. Connected Papers | Find and explore academic papers, acessado em agosto 26, 2025, [https://www.connectedpapers.com/](https://www.connectedpapers.com/)