"""
Response Parser for Enhanced Prompt System

Parses XML-structured responses from the enhanced prompt templates
into structured data for clean UI display.
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ParsedResponse:
    """Structured response data."""
    direct_answer: str
    detailed_explanation: str
    broader_connections: str
    references: str
    raw_response: str
    has_xml_structure: bool

class ResponseParser:
    """Parser for XML-structured philosophical responses."""
    
    @staticmethod
    def parse_response(response_text: str) -> ParsedResponse:
        """
        Parse XML-structured response into components.
        
        Args:
            response_text: Raw response from the enhanced prompt system
            
        Returns:
            ParsedResponse with extracted sections
        """
        
        # Clean up the response text
        cleaned_response = ResponseParser._clean_response(response_text)
        
        # Try to extract XML sections
        sections = ResponseParser._extract_xml_sections(cleaned_response)
        
        if sections:
            return ParsedResponse(
                direct_answer=sections.get('direct_answer', ''),
                detailed_explanation=sections.get('detailed_explanation', ''),
                broader_connections=sections.get('broader_connections', ''),
                references=sections.get('references', ''),
                raw_response=response_text,
                has_xml_structure=True
            )
        else:
            # Fallback: treat entire response as detailed explanation
            return ParsedResponse(
                direct_answer='',
                detailed_explanation=cleaned_response,
                broader_connections='',
                references='',
                raw_response=response_text,
                has_xml_structure=False
            )
    
    @staticmethod
    def _clean_response(response_text: str) -> str:
        """Clean up response text by removing debug output."""
        lines = response_text.split('\n')
        cleaned_lines = []
        
        skip_patterns = [
            'DEBUG:',
            'Initializing',
            'Connecting to',
            'Loading',
            'Found ',
            'SUCCESS:',
            'Processing:',
            'Generating',
            'Query vector:',
            'Searching',
            'Response generated',
            '===',  # Separator lines
            'ARETE RAG RESPONSE',
            'Query:',
            'Related entities:',
            'Key entities:',
            'Response:',
            '---'   # Dash separators
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip debug and system output lines
            if any(pattern in line for pattern in skip_patterns):
                continue
            
            # Skip lines that look like system output
            if line.startswith('>>') or line.startswith('Found:'):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def _extract_xml_sections(response_text: str) -> Optional[Dict[str, str]]:
        """Extract XML sections from response."""
        sections = {}
        
        # XML section patterns
        patterns = {
            'direct_answer': r'<direct_answer>\s*(.*?)\s*</direct_answer>',
            'detailed_explanation': r'<detailed_explanation>\s*(.*?)\s*</detailed_explanation>',
            'broader_connections': r'<broader_connections>\s*(.*?)\s*</broader_connections>',
            'references': r'<references>\s*(.*?)\s*</references>'
        }
        
        found_any = False
        
        for section_name, pattern in patterns.items():
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(1).strip()
                found_any = True
            else:
                sections[section_name] = ''
        
        return sections if found_any else None
    
    @staticmethod
    def extract_citations(references_text: str) -> List[Dict[str, str]]:
        """Extract citations from the references section."""
        citations = []
        
        if not references_text:
            return citations
        
        # Look for citation patterns like "Work Title: citation text"
        citation_patterns = [
            r'([A-Z][^:]+):\s*([^\\n]+)',  # "Apology 38a: text"
            r'([A-Z][^\\n]*?)\\s*[-–—]\\s*([^\\n]+)',  # "Source - text"
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, references_text, re.MULTILINE)
            for match in matches:
                citations.append({
                    'source': match[0].strip(),
                    'text': match[1].strip()
                })
        
        # If no structured citations found, treat each line as a citation
        if not citations:
            lines = [line.strip() for line in references_text.split('\n') if line.strip()]
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 1)
                    citations.append({
                        'source': parts[0].strip(),
                        'text': parts[1].strip()
                    })
                else:
                    citations.append({
                        'source': 'Citation',
                        'text': line
                    })
        
        return citations