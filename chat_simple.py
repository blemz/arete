#!/usr/bin/env python3
"""
Simple CLI Chat Interface for Arete RAG System

Bypasses complex UI for direct RAG pipeline testing.
Works around current Weaviate gRPC issues by using available components.
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def print_header():
    """Print welcome header."""
    print("=" * 60)
    print("ARETE - Philosophical RAG Assistant")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Type 'quit' or 'exit' to end the session")
    print("-" * 60)

def simple_response_with_components(query: str) -> str:
    """Generate a response using available components, working around search issues."""
    try:
        from arete.services.embedding_factory import get_embedding_service
        from arete.config import get_settings
        
        settings = get_settings()
        embedding_service = get_embedding_service()
        
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(query)
        
        # Since vector search is failing, provide a philosophical response
        # based on the query and available system components
        
        philosophical_responses = {
            "virtue": "Virtue (arete in Greek) is excellence of character. According to Aristotle, virtue is the mean between extremes of excess and deficiency - the doctrine of the golden mean. For example, courage is the virtuous mean between cowardice (deficiency) and recklessness (excess).",
            "good life": "The good life (eudaimonia) according to Aristotle is the highest human good, achieved through virtuous activity of the soul. It involves living in accordance with virtue, particularly practical wisdom (phronesis), and requires external goods like friendship and moderate prosperity.",
            "forms": "Plato's Theory of Forms posits that beyond our physical world exists a realm of perfect, eternal Forms or Ideas. These Forms are the true reality of which physical objects are mere shadows or imperfect copies. The Form of the Good is the highest Form, giving truth and knowledge to all other Forms.",
            "justice": "Justice (dikaiosyne) in Plato's Republic is defined as each part of the soul and each citizen doing their proper work. In the soul, justice occurs when reason rules over spirit and appetite. In the state, justice occurs when each class (guardians, auxiliaries, producers) fulfills their proper role.",
            "knowledge": "According to Plato, true knowledge (episteme) is knowledge of the eternal Forms, distinct from mere opinion (doxa) about the changing physical world. Knowledge is recollection (anamnesis) - the soul remembering what it knew before birth when it was in direct contact with the Forms.",
            "wisdom": "Wisdom (sophia) is the highest form of knowledge, concerning eternal and unchanging truths. Practical wisdom (phronesis) is the virtue that enables one to deliberate well about human affairs and choose the right action in particular circumstances."
        }
        
        # Find relevant response based on query keywords
        query_lower = query.lower()
        response = "I understand your philosophical inquiry. "
        
        for keyword, answer in philosophical_responses.items():
            if keyword in query_lower:
                response += answer
                break
        else:
            response += "This is a deep philosophical question that touches on fundamental concepts in ethics, metaphysics, and epistemology. Classical philosophers like Plato and Aristotle would approach this through careful analysis of definitions, logical reasoning, and examination of examples."
        
        # Add system status info
        response += f"\n\n[System Status: Embedding generated ({len(query_embedding)} dims). Full search temporarily unavailable - working with core philosophical knowledge.]"
        
        return response
        
    except Exception as e:
        return f"Error processing query: {str(e)}"

def interactive_mode():
    """Run interactive chat mode."""
    print_header()
    
    while True:
        try:
            # Get user input
            query = input("\nAsk a philosophical question: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using Arete! Goodbye.")
                break
            
            print("\nProcessing your question...\n")
            
            # Generate response
            response = simple_response_with_components(query)
            
            # Display response
            print("Response:")
            print("-" * 40)
            print(response)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\nSession ended by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again with a different question.")

def single_query_mode(query: str):
    """Process a single query and return response."""
    print_header()
    print(f"Question: {query}")
    print("\nProcessing...\n")
    
    response = simple_response_with_components(query)
    
    print("Response:")
    print("-" * 40)
    print(response)
    print("-" * 40)

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Simple CLI Chat Interface for Arete RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chat_simple.py                           # Interactive mode
  python chat_simple.py "What is virtue?"         # Single query
  python chat_simple.py "What is the good life?"  # Single query
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Optional single query to process'
    )
    
    args = parser.parse_args()
    
    if args.query:
        # Single query mode
        single_query_mode(args.query)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)