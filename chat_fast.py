#!/usr/bin/env python3
"""
Fast CLI Chat Interface for Arete RAG System

Bypasses embedding generation for immediate responses.
Tests core philosophical knowledge without database dependencies.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

def print_header():
    """Print welcome header."""
    print("=" * 60)
    print("ARETE - Fast Philosophical Assistant")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Type 'quit' or 'exit' to end the session")
    print("-" * 60)

def get_philosophical_response(query: str) -> str:
    """Generate philosophical response based on classical knowledge."""
    
    philosophical_knowledge = {
        "virtue": "Virtue (arete in Greek) is excellence of character. According to Aristotle, virtue is the mean between extremes of excess and deficiency - the doctrine of the golden mean. For example, courage is the virtuous mean between cowardice (deficiency) and recklessness (excess). Virtue is acquired through habituation and practice, making it a matter of character rather than knowledge alone.",
        
        "good life": "The good life (eudaimonia) according to Aristotle is the highest human good, achieved through virtuous activity of the soul. It involves living in accordance with virtue, particularly practical wisdom (phronesis), and requires external goods like friendship and moderate prosperity. Eudaimonia is not a feeling but an activity - specifically, the activity of the soul in accordance with virtue over a complete life.",
        
        "forms": "Plato's Theory of Forms posits that beyond our physical world exists a realm of perfect, eternal Forms or Ideas. These Forms are the true reality of which physical objects are mere shadows or imperfect copies. The Form of the Good is the highest Form, giving truth and knowledge to all other Forms. We can access knowledge of the Forms through philosophical reasoning and dialectic.",
        
        "justice": "Justice (dikaiosyne) in Plato's Republic is defined as each part doing its proper work. In the soul, justice occurs when reason rules over spirit and appetite in harmony. In the state, justice occurs when each class (philosopher-kings, guardians, producers) fulfills their proper role. Justice is not merely following laws but achieving harmony through proper ordering.",
        
        "knowledge": "According to Plato, true knowledge (episteme) is knowledge of the eternal Forms, distinct from mere opinion (doxa) about the changing physical world. Knowledge is recollection (anamnesis) - the soul remembering what it knew before birth when it was in direct contact with the Forms. The divided line and cave allegory illustrate the progression from ignorance to knowledge.",
        
        "wisdom": "Wisdom (sophia) is the highest form of knowledge, concerning eternal and unchanging truths about the most important realities. Practical wisdom (phronesis) is the virtue that enables one to deliberate well about human affairs and choose the right action in particular circumstances. Socratic wisdom involves knowing that one does not know.",
        
        "soul": "The soul (psyche) for Plato has three parts: reason (logos), spirit (thymos), and appetite (epithymia). The rational part should rule, aided by the spirited part, over the appetitive part. For Aristotle, the soul is the form of a living body, with rational, sensitive, and nutritive functions. The rational soul is what makes humans distinct.",
        
        "happiness": "Happiness (eudaimonia) is not a temporary emotional state but the highest good that we seek for its own sake. Aristotle argues it consists in virtuous activity of the soul, particularly the exercise of our highest capacities in accordance with excellence. It requires a complete life and some external goods.",
        
        "courage": "Courage (andreia) is the virtue concerned with fear and confidence. The courageous person faces dangers they ought to face, in the right way, at the right time, for the right reasons. It is the mean between cowardice (excessive fear) and recklessness (deficient fear). True courage involves rational choice and noble purpose.",
        
        "friendship": "Friendship (philia) for Aristotle comes in three types: friendships of utility, pleasure, and virtue. The highest form is friendship based on virtue, where friends love each other for who they are and wish good for each other's sake. Such friendships are rare, lasting, and essential for the good life."
    }
    
    # Find relevant response based on query keywords
    query_lower = query.lower()
    
    # Check for exact matches first
    for keyword, answer in philosophical_knowledge.items():
        if keyword in query_lower:
            return f"{answer}\n\n[Source: Classical philosophical texts - Aristotle's Nicomachean Ethics, Plato's Republic and other dialogues]"
    
    # Check for related philosophical terms
    related_terms = {
        "ethics": "virtue",
        "moral": "virtue", 
        "character": "virtue",
        "mean": "virtue",
        "excellence": "virtue",
        "eudaimonia": "good life",
        "flourishing": "good life",
        "living well": "good life",
        "ideal": "forms",
        "reality": "forms",
        "truth": "knowledge",
        "episteme": "knowledge",
        "doxa": "knowledge", 
        "opinion": "knowledge",
        "sofia": "wisdom",
        "phronesis": "wisdom",
        "practical wisdom": "wisdom",
        "psyche": "soul",
        "reason": "soul",
        "rational": "soul"
    }
    
    for term, main_concept in related_terms.items():
        if term in query_lower:
            answer = philosophical_knowledge.get(main_concept, "")
            if answer:
                return f"{answer}\n\n[Source: Classical philosophical texts - concept related to {main_concept}]"
    
    # Generic philosophical response
    return """This is a profound philosophical question that would benefit from careful analysis using classical philosophical methods.

Key approaches to consider:
- Definitional analysis: What exactly do the key terms mean?
- Examples and counterexamples: What cases illustrate the concept?
- Logical reasoning: What follows from our premises?
- Ethical implications: How does this affect how we should live?

Classical philosophers like Plato and Aristotle would examine this through dialogue, logical argument, and connection to fundamental concepts like virtue, knowledge, justice, and the good life.

[Source: General philosophical methodology from classical tradition]"""

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
            
            print("\nProcessing...\n")
            
            # Generate response
            response = get_philosophical_response(query)
            
            # Display response
            print("Response:")
            print("-" * 60)
            print(response)
            print("-" * 60)
            
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
    
    response = get_philosophical_response(query)
    
    print("Response:")
    print("-" * 60)
    print(response)
    print("-" * 60)

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Fast CLI Chat Interface for Arete RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chat_fast.py                             # Interactive mode
  python chat_fast.py "What is virtue?"           # Single query
  python chat_fast.py "What is the good life?"    # Single query
  python chat_fast.py "What is justice?"          # Single query
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