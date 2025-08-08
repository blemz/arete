// Neo4j Database Schema for Arete Graph-RAG System
// This file contains the constraints and indexes for the knowledge graph

// ============================================================================
// NODE CONSTRAINTS AND INDEXES
// ============================================================================

// Document constraints and indexes
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE INDEX document_title IF NOT EXISTS FOR (d:Document) ON (d.title);
CREATE INDEX document_author IF NOT EXISTS FOR (d:Document) ON (d.author);
CREATE INDEX document_created_at IF NOT EXISTS FOR (d:Document) ON (d.created_at);
CREATE TEXT INDEX document_content_text IF NOT EXISTS FOR (d:Document) ON (d.content);

// Entity constraints and indexes  
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE TEXT INDEX entity_description_text IF NOT EXISTS FOR (e:Entity) ON (e.description);

// Chunk constraints and indexes
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;
CREATE INDEX chunk_document_id IF NOT EXISTS FOR (c:Chunk) ON (c.document_id);
CREATE INDEX chunk_position IF NOT EXISTS FOR (c:Chunk) ON (c.position);
CREATE TEXT INDEX chunk_text_content IF NOT EXISTS FOR (c:Chunk) ON (c.text);

// Citation constraints and indexes
CREATE CONSTRAINT citation_id IF NOT EXISTS FOR (ct:Citation) REQUIRE ct.id IS UNIQUE;
CREATE INDEX citation_reference IF NOT EXISTS FOR (ct:Citation) ON (ct.reference);
CREATE INDEX citation_location IF NOT EXISTS FOR (ct:Citation) ON (ct.location);

// ============================================================================
// RELATIONSHIP INDEXES
// ============================================================================

// Entity relationships
CREATE INDEX entity_relationship_type IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.type);
CREATE INDEX entity_relationship_strength IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.strength);

// Document-Entity relationships
CREATE INDEX document_mentions_strength IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r.strength);
CREATE INDEX document_mentions_count IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r.count);

// Chunk relationships
CREATE INDEX chunk_next_position IF NOT EXISTS FOR ()-[r:NEXT]-() ON (r.position);
CREATE INDEX chunk_contains_relevance IF NOT EXISTS FOR ()-[r:CONTAINS]-() ON (r.relevance);

// Citation relationships
CREATE INDEX citation_cites_page IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.page);
CREATE INDEX citation_supports_strength IF NOT EXISTS FOR ()-[r:SUPPORTS]-() ON (r.strength);

// ============================================================================
// FULL-TEXT INDEXES FOR SEMANTIC SEARCH
// ============================================================================

// Create full-text indexes for advanced text search
CREATE FULLTEXT INDEX document_fulltext IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.content, d.author];
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (e:Entity) ON EACH [e.name, e.description, e.properties];
CREATE FULLTEXT INDEX chunk_fulltext IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text, c.metadata];

// ============================================================================
// PROPERTY EXISTENCE CONSTRAINTS
// ============================================================================

// Ensure essential properties exist
CREATE CONSTRAINT document_required_props IF NOT EXISTS FOR (d:Document) REQUIRE d.title IS NOT NULL;
CREATE CONSTRAINT entity_required_props IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS NOT NULL;
CREATE CONSTRAINT chunk_required_props IF NOT EXISTS FOR (c:Chunk) REQUIRE c.text IS NOT NULL;

// ============================================================================
// CUSTOM PROCEDURES (if using APOC)
// ============================================================================

// Note: These would typically be loaded via APOC plugin
// CALL apoc.schema.assert({}, {}) // Clear existing schema if needed

// ============================================================================
// SAMPLE DATA VALIDATION QUERIES
// ============================================================================

// Verify schema creation
// CALL db.schema.visualization();
// CALL db.indexes();
// CALL db.constraints();

// Performance optimization settings (for production)
// CALL dbms.procedures() YIELD name WHERE name CONTAINS 'apoc' RETURN count(*);