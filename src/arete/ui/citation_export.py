"""
Citation Export Functionality.

Provides export capabilities for citations in multiple formats including
JSON, BibTeX, Markdown, and custom philosophical citation formats.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
import re
from io import StringIO
import streamlit as st


class ExportFormat(str, Enum):
    """Supported citation export formats."""
    JSON = "json"
    BIBTEX = "bibtex"
    MARKDOWN = "markdown"
    CHICAGO = "chicago"
    MLA = "mla"
    CLASSICAL = "classical"
    CSV = "csv"


@dataclass
class CitationExportConfig:
    """Configuration for citation export."""
    
    format: ExportFormat = ExportFormat.MARKDOWN
    include_context: bool = True
    include_metadata: bool = False
    include_confidence: bool = False
    group_by_work: bool = True
    sort_by_relevance: bool = True
    timestamp: bool = True
    filename_prefix: str = "arete_citations"


class CitationExporter:
    """
    Export citations in various scholarly formats.
    
    Supports multiple export formats suitable for academic use,
    particularly focused on philosophical and classical texts.
    """
    
    def __init__(self, config: Optional[CitationExportConfig] = None):
        """Initialize exporter with configuration."""
        self.config = config or CitationExportConfig()
    
    def export_citations(
        self,
        citations: List[Any],  # CitationDetails from citation_preview.py
        format: Optional[ExportFormat] = None
    ) -> str:
        """
        Export citations in specified format.
        
        Args:
            citations: List of citation objects to export
            format: Export format (overrides config if provided)
            
        Returns:
            Formatted string ready for export
        """
        export_format = format or self.config.format
        
        # Sort and group if configured
        processed_citations = self._process_citations(citations)
        
        # Export based on format
        if export_format == ExportFormat.JSON:
            return self._export_json(processed_citations)
        elif export_format == ExportFormat.BIBTEX:
            return self._export_bibtex(processed_citations)
        elif export_format == ExportFormat.MARKDOWN:
            return self._export_markdown(processed_citations)
        elif export_format == ExportFormat.CHICAGO:
            return self._export_chicago(processed_citations)
        elif export_format == ExportFormat.MLA:
            return self._export_mla(processed_citations)
        elif export_format == ExportFormat.CLASSICAL:
            return self._export_classical(processed_citations)
        elif export_format == ExportFormat.CSV:
            return self._export_csv(processed_citations)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
    
    def _process_citations(self, citations: List[Any]) -> List[Any]:
        """Process citations based on configuration."""
        processed = list(citations)
        
        # Sort by relevance if configured
        if self.config.sort_by_relevance:
            processed.sort(
                key=lambda c: getattr(c, 'relevance_score', 0),
                reverse=True
            )
        
        return processed
    
    def _export_json(self, citations: List[Any]) -> str:
        """Export as JSON format."""
        export_data = {
            "export_date": datetime.now().isoformat() if self.config.timestamp else None,
            "total_citations": len(citations),
            "citations": []
        }
        
        for citation in citations:
            cite_dict = {
                "text": citation.text,
                "source": citation.source,
                "author": citation.author,
                "work": citation.work,
                "reference": citation.reference
            }
            
            if self.config.include_context and citation.context:
                cite_dict["context"] = citation.context
            
            if self.config.include_confidence:
                cite_dict["confidence"] = citation.confidence
                cite_dict["relevance_score"] = citation.relevance_score
            
            if self.config.include_metadata:
                cite_dict["metadata"] = {
                    "citation_id": citation.citation_id,
                    "chunk_id": citation.chunk_id,
                    "position": citation.position,
                    "document_id": citation.document_id
                }
            
            export_data["citations"].append(cite_dict)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_bibtex(self, citations: List[Any]) -> str:
        """Export as BibTeX format."""
        output = StringIO()
        
        if self.config.timestamp:
            output.write(f"% Exported from Arete on {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        for i, citation in enumerate(citations, 1):
            # Generate BibTeX key
            author_key = self._sanitize_bibtex_key(citation.author or "Unknown")
            work_key = self._sanitize_bibtex_key(citation.work or "Work")
            year = "0000"  # Classical texts don't have publication years
            
            key = f"{author_key}{year}{work_key}"
            
            # Determine entry type
            entry_type = "@book" if citation.work else "@misc"
            
            output.write(f"{entry_type}{{{key},\n")
            
            if citation.author:
                output.write(f"  author = {{{citation.author}}},\n")
            
            if citation.work:
                output.write(f"  title = {{{citation.work}}},\n")
            
            if citation.reference:
                output.write(f"  note = {{Reference: {citation.reference}}},\n")
            
            if self.config.include_context and citation.context:
                output.write(f"  annote = {{{citation.context}}},\n")
            
            # Add quoted text as abstract
            if citation.text:
                output.write(f"  abstract = {{{citation.text}}},\n")
            
            output.write("}\n\n")
        
        return output.getvalue()
    
    def _export_markdown(self, citations: List[Any]) -> str:
        """Export as Markdown format."""
        output = StringIO()
        
        # Header
        output.write("# Citations\n\n")
        if self.config.timestamp:
            output.write(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        
        # Group by work if configured
        if self.config.group_by_work:
            grouped = self._group_citations_by_work(citations)
            
            for work_key, work_citations in grouped.items():
                output.write(f"## {work_key}\n\n")
                
                for citation in work_citations:
                    self._write_markdown_citation(output, citation)
                    output.write("\n")
        else:
            for citation in citations:
                self._write_markdown_citation(output, citation)
                output.write("\n")
        
        return output.getvalue()
    
    def _write_markdown_citation(self, output: StringIO, citation: Any) -> None:
        """Write a single citation in Markdown format."""
        # Reference line
        reference = self._format_reference(citation)
        output.write(f"### {reference}\n\n")
        
        # Quoted text
        output.write(f"> {citation.text}\n\n")
        
        # Metadata
        if self.config.include_context and citation.context:
            output.write(f"**Context:** {citation.context}\n\n")
        
        if self.config.include_confidence:
            output.write(f"*Confidence: {citation.confidence:.1%} | ")
            output.write(f"Relevance: {citation.relevance_score:.1%}*\n\n")
        
        output.write("---\n\n")
    
    def _export_chicago(self, citations: List[Any]) -> str:
        """Export in Chicago Manual of Style format."""
        output = StringIO()
        
        if self.config.timestamp:
            output.write(f"# Citations (Chicago Style)\n")
            output.write(f"*Exported on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
        
        for i, citation in enumerate(citations, 1):
            # Chicago format: Author. Title. Reference. "Quote."
            parts = []
            
            if citation.author:
                parts.append(citation.author)
            
            if citation.work:
                parts.append(f"*{citation.work}*")
            
            if citation.reference:
                parts.append(citation.reference)
            
            cite_str = f"{i}. {'. '.join(parts)}."
            
            if citation.text:
                cite_str += f' "{citation.text}"'
            
            output.write(f"{cite_str}\n\n")
        
        return output.getvalue()
    
    def _export_mla(self, citations: List[Any]) -> str:
        """Export in MLA format."""
        output = StringIO()
        
        if self.config.timestamp:
            output.write(f"Works Cited\n")
            output.write(f"{datetime.now().strftime('%d %B %Y')}\n\n")
        
        for citation in citations:
            # MLA format: Author. "Work." Reference.
            parts = []
            
            if citation.author:
                # Last name, First name format (simplified for classical authors)
                parts.append(citation.author)
            
            if citation.work:
                parts.append(f'"{citation.work}"')
            
            if citation.reference:
                parts.append(citation.reference)
            
            cite_str = ". ".join(parts) + "."
            output.write(f"{cite_str}\n")
            
            if citation.text and self.config.include_context:
                output.write(f'    "{citation.text}"\n')
            
            output.write("\n")
        
        return output.getvalue()
    
    def _export_classical(self, citations: List[Any]) -> str:
        """Export in classical citation format."""
        output = StringIO()
        
        if self.config.timestamp:
            output.write(f"Classical Citations\n")
            output.write(f"{datetime.now().strftime('%Y-%m-%d')}\n")
            output.write("=" * 40 + "\n\n")
        
        for citation in citations:
            # Classical format: Author, Work Reference
            if citation.author and citation.work and citation.reference:
                output.write(f"{citation.author}, {citation.work} {citation.reference}\n")
            elif citation.work and citation.reference:
                output.write(f"{citation.work} {citation.reference}\n")
            else:
                output.write(f"{citation.source}\n")
            
            if citation.text:
                # Indent quoted text
                wrapped_text = self._wrap_text(citation.text, 70)
                for line in wrapped_text.split('\n'):
                    output.write(f"    {line}\n")
            
            output.write("\n")
        
        return output.getvalue()
    
    def _export_csv(self, citations: List[Any]) -> str:
        """Export as CSV format."""
        import csv
        output = StringIO()
        
        fieldnames = ["Author", "Work", "Reference", "Text", "Source"]
        
        if self.config.include_context:
            fieldnames.append("Context")
        
        if self.config.include_confidence:
            fieldnames.extend(["Confidence", "Relevance"])
        
        if self.config.include_metadata:
            fieldnames.extend(["Citation_ID", "Position"])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for citation in citations:
            row = {
                "Author": citation.author or "",
                "Work": citation.work or "",
                "Reference": citation.reference or "",
                "Text": citation.text,
                "Source": citation.source
            }
            
            if self.config.include_context:
                row["Context"] = citation.context or ""
            
            if self.config.include_confidence:
                row["Confidence"] = f"{citation.confidence:.2f}"
                row["Relevance"] = f"{citation.relevance_score:.2f}"
            
            if self.config.include_metadata:
                row["Citation_ID"] = citation.citation_id
                row["Position"] = str(citation.position) if citation.position else ""
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _format_reference(self, citation: Any) -> str:
        """Format citation reference."""
        if citation.author and citation.work and citation.reference:
            return f"{citation.author}, {citation.work} {citation.reference}"
        elif citation.work and citation.reference:
            return f"{citation.work} {citation.reference}"
        elif citation.reference:
            return citation.reference
        return citation.source
    
    def _sanitize_bibtex_key(self, text: str) -> str:
        """Sanitize text for BibTeX key."""
        # Remove non-alphanumeric characters
        key = re.sub(r'[^a-zA-Z0-9]', '', text)
        return key[:20]  # Limit length
    
    def _group_citations_by_work(self, citations: List[Any]) -> Dict[str, List[Any]]:
        """Group citations by work/author."""
        grouped = {}
        
        for citation in citations:
            if citation.work:
                key = f"{citation.author or 'Unknown'} - {citation.work}"
            elif citation.author:
                key = citation.author
            else:
                key = "Other Sources"
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(citation)
        
        return grouped
    
    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > width:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def get_filename(self, format: Optional[ExportFormat] = None) -> str:
        """Generate export filename."""
        export_format = format or self.config.format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        extension_map = {
            ExportFormat.JSON: "json",
            ExportFormat.BIBTEX: "bib",
            ExportFormat.MARKDOWN: "md",
            ExportFormat.CHICAGO: "txt",
            ExportFormat.MLA: "txt",
            ExportFormat.CLASSICAL: "txt",
            ExportFormat.CSV: "csv"
        }
        
        extension = extension_map.get(export_format, "txt")
        return f"{self.config.filename_prefix}_{timestamp}.{extension}"


class CitationExportUI:
    """Streamlit UI component for citation export."""
    
    def __init__(self):
        """Initialize export UI."""
        self.exporter = CitationExporter()
    
    def render_export_controls(self, citations: List[Any]) -> None:
        """
        Render export controls in Streamlit.
        
        Args:
            citations: List of citations to export
        """
        if not citations:
            st.warning("No citations to export")
            return
        
        with st.expander("📥 Export Citations", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                format = st.selectbox(
                    "Export Format",
                    options=list(ExportFormat),
                    format_func=lambda x: x.value.upper()
                )
            
            with col2:
                st.markdown("**Options**")
                include_context = st.checkbox("Include context", value=True)
                include_metadata = st.checkbox("Include metadata", value=False)
                include_confidence = st.checkbox("Include scores", value=False)
            
            with col3:
                st.markdown("**Organization**")
                group_by_work = st.checkbox("Group by work", value=True)
                sort_by_relevance = st.checkbox("Sort by relevance", value=True)
            
            # Update exporter config
            self.exporter.config.format = format
            self.exporter.config.include_context = include_context
            self.exporter.config.include_metadata = include_metadata
            self.exporter.config.include_confidence = include_confidence
            self.exporter.config.group_by_work = group_by_work
            self.exporter.config.sort_by_relevance = sort_by_relevance
            
            # Export button
            if st.button("🚀 Export Citations", type="primary"):
                try:
                    exported_content = self.exporter.export_citations(citations)
                    filename = self.exporter.get_filename()
                    
                    # Provide download button
                    st.download_button(
                        label=f"📄 Download {filename}",
                        data=exported_content,
                        file_name=filename,
                        mime=self._get_mime_type(format)
                    )
                    
                    # Show preview
                    with st.expander("Preview", expanded=True):
                        if format == ExportFormat.JSON:
                            st.json(json.loads(exported_content))
                        else:
                            st.code(exported_content[:1000] + "..." if len(exported_content) > 1000 else exported_content)
                    
                    st.success(f"Successfully exported {len(citations)} citations!")
                    
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
    
    def _get_mime_type(self, format: ExportFormat) -> str:
        """Get MIME type for download."""
        mime_map = {
            ExportFormat.JSON: "application/json",
            ExportFormat.BIBTEX: "text/plain",
            ExportFormat.MARKDOWN: "text/markdown",
            ExportFormat.CSV: "text/csv",
            ExportFormat.CHICAGO: "text/plain",
            ExportFormat.MLA: "text/plain",
            ExportFormat.CLASSICAL: "text/plain"
        }
        return mime_map.get(format, "text/plain")