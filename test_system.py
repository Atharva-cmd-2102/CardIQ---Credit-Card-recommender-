"""
Quick Test Script
Tests the complete CardIQ system: PDF Processing → RAG → Multi-Agent System
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.pdf_processor import PDFProcessor
from rag.rag_system import RAGSystem
from agents import OrchestratorAgent


def main():
    print("=" * 60)
    print("CardIQ System Test")
    print("=" * 60)
    
    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set!")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key'")
        return
    
    print("✓ API Key found\n")
    
    # Step 1: Process PDFs
    print("STEP 1: Processing PDFs")
    print("-" * 60)
    processor = PDFProcessor()
    processed_cards = processor.process_all_pdfs()
    
    if not processed_cards:
        print("❌ No PDFs processed. Add PDFs to data/pdfs/")
        return
    
    print(f"✓ Processed {len(processed_cards)} cards\n")
    
    # Step 2: Build RAG System
    print("STEP 2: Building RAG System")
    print("-" * 60)
    rag = RAGSystem()
    rag.create_embeddings(processed_cards)
    print("✓ RAG system ready\n")
    
    # Step 3: Test RAG Search
    print("STEP 3: Testing RAG Search")
    print("-" * 60)
    test_query = "What is the annual fee?"
    results = rag.search(test_query, k=2)
    print(f"Query: '{test_query}'")
    print(f"Found {len(results)} relevant chunks:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['card_name']} (Relevance: {result['relevance']:.2f})")
        print(f"   {result['text'][:150]}...\n")
    
    # Step 4: Initialize Multi-Agent System
    print("STEP 4: Initializing Multi-Agent System")
    print("-" * 60)
    orchestrator = OrchestratorAgent(rag_system=rag)
    print()
    
    # Step 5: Run Complete Analysis
    print("STEP 5: Running Complete Analysis")
    print("-" * 60)
    
    # Test spending profile
    test_spending = {
        "dining": 400,
        "groceries": 500,
        "gas": 200,
        "travel": 150,
        "drugstores": 100,
        "other": 600
    }
    
    # Cards to evaluate
    test_cards = [
        {
            "name": "Chase Freedom Flex",
            "annual_fee": 0,
            "rewards": {
                "base": 0.01,
                "dining": 0.03,
                "drugstores": 0.03,
                "gas": 0.01,
                "travel": 0.05,
                "groceries": 0.01,
                "quarterly_bonus": 0.05  # Up to $1500/quarter
            }
        }
    ]
    
    # Run analysis
    result = orchestrator.run(
        spending_profile=test_spending,
        cards=test_cards,
        user_preferences={"annual_fee_ok": False}
    )
    
    # Display Results
    if result.get("status") == "success":
        print("\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 60)
        
        recs = result['recommendations']['recommendations']
        
        print(f"\n📊 TOP RECOMMENDATION:")
        print("-" * 60)
        top_rec = recs[0]
        print(f"Card: {top_rec['card_name']}")
        print(f"Net Annual Value: ${top_rec.get('net_annual_value', 'N/A')}")
        print(f"Strength: {top_rec.get('recommendation_strength', 'N/A')}/10")
        print(f"\nBest For: {top_rec.get('best_for', 'N/A')}")
        
        print(f"\nPros:")
        for pro in top_rec.get('pros', [])[:3]:
            print(f"  ✓ {pro}")
        
        print(f"\nCons:")
        for con in top_rec.get('cons', [])[:3]:
            print(f"  ⚠ {con}")
        
        print(f"\n💰 API Cost: ${result['cost']:.4f}")
        
    else:
        print(f"\n❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
