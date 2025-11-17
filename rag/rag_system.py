"""
RAG (Retrieval-Augmented Generation) System
Uses FAISS for vector storage and semantic search
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


class RAGSystem:
    """
    Retrieval-Augmented Generation system for credit card documents
    Uses semantic search to find relevant card information
    """
    
    def __init__(self, 
                 embeddings_dir: str = "embeddings",
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG system
        
        Args:
            embeddings_dir: Directory to store/load embeddings
            model_name: Sentence transformer model to use
        """
        self.embeddings_dir = Path(embeddings_dir)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("✓ Model loaded")
        
        self.index = None
        self.chunks = []
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
    
    def create_embeddings(self, processed_cards: List[Dict]):
        """
        Create embeddings for all card chunks
        
        Args:
            processed_cards: List of processed card data from PDFProcessor
        """
        print("\nCreating embeddings...")
        
        # Collect all chunks
        self.chunks = []
        texts = []
        
        for card in processed_cards:
            for chunk in card['chunks']:
                self.chunks.append(chunk)
                texts.append(chunk['text'])
        
        print(f"Total chunks to embed: {len(texts)}")
        
        # Create embeddings (batch processing)
        print("Encoding texts...")
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        print(f"✓ Created {len(embeddings)} embeddings")
        
        # Create FAISS index
        print("Building FAISS index...")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"✓ FAISS index built with {self.index.ntotal} vectors")
        
        # Save index and chunks
        self.save_index()
    
    def save_index(self):
        """Save FAISS index and chunk metadata"""
        index_path = self.embeddings_dir / "faiss_index.bin"
        chunks_path = self.embeddings_dir / "chunks_metadata.pkl"
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save chunks
        with open(chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)
        
        print(f"✓ Saved index to {index_path}")
        print(f"✓ Saved metadata to {chunks_path}")
    
    def load_index(self):
        """Load existing FAISS index and metadata"""
        index_path = self.embeddings_dir / "faiss_index.bin"
        chunks_path = self.embeddings_dir / "chunks_metadata.pkl"
        
        if not index_path.exists() or not chunks_path.exists():
            print("No existing index found. Please create embeddings first.")
            return False
        
        print("Loading existing index...")
        
        # Load FAISS index
        self.index = faiss.read_index(str(index_path))
        
        # Load chunks
        with open(chunks_path, 'rb') as f:
            self.chunks = pickle.load(f)
        
        print(f"✓ Loaded index with {self.index.ntotal} vectors")
        print(f"✓ Loaded {len(self.chunks)} chunk metadata")
        
        return True
    
    def search(self, query: str, k: int = 3, card_filter: str = None) -> List[Dict]:
        """
        Semantic search for relevant chunks
        
        Args:
            query: Search query
            k: Number of results to return
            card_filter: Optional card name to filter results
        
        Returns:
            List of relevant chunks with scores
        """
        if self.index is None:
            print("Index not loaded. Please load or create index first.")
            return []
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search
        distances, indices = self.index.search(
            query_embedding.astype('float32'), 
            k if not card_filter else k * 3  # Get more if filtering
        )
        
        # Collect results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk['score'] = float(distance)
                chunk['relevance'] = 1.0 / (1.0 + distance)  # Convert distance to relevance
                
                # Apply card filter if specified
                if card_filter is None or card_filter.lower() in chunk['card_name'].lower():
                    results.append(chunk)
                
                if len(results) >= k:
                    break
        
        return results
    
    def get_context_for_query(self, query: str, k: int = 3, card_filter: str = None) -> str:
        """
        Get formatted context string for LLM prompt
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            card_filter: Optional card name filter
        
        Returns:
            Formatted context string
        """
        results = self.search(query, k=k, card_filter=card_filter)
        
        if not results:
            return "No relevant information found."
        
        context = "RELEVANT INFORMATION FROM CREDIT CARD DOCUMENTS:\n\n"
        
        for i, result in enumerate(results, 1):
            context += f"[Source {i}: {result['card_name']} - Relevance: {result['relevance']:.2f}]\n"
            context += f"{result['text']}\n\n"
        
        return context


# Example usage
if __name__ == "__main__":
    # Initialize RAG system
    rag = RAGSystem()
    
    # Load processed cards
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        cards = []
        for json_file in processed_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                cards.append(json.load(f))
        
        if cards:
            # Create embeddings
            rag.create_embeddings(cards)
            
            # Test search
            print("\n--- Testing Search ---")
            query = "What is the annual fee?"
            results = rag.search(query, k=3)
            
            print(f"\nQuery: {query}")
            print(f"Found {len(results)} results:\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['card_name']} (Relevance: {result['relevance']:.2f})")
                print(f"   {result['text'][:200]}...")
                print()
    else:
        print("No processed cards found. Run pdf_processor.py first.")
