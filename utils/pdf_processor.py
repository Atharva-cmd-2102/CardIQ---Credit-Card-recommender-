"""
PDF Processor for Credit Card Documents
Extracts text from card agreement PDFs and structures them for RAG
"""

import os
from pathlib import Path
from typing import List, Dict
import json
from pypdf import PdfReader


class PDFProcessor:
    """Process credit card PDF documents"""
    
    def __init__(self, pdf_dir: str = "data/pdfs", output_dir: str = "data/processed"):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from a PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num} ---\n{page_text}\n"
            
            return text
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
        """
        Split text into overlapping chunks for better RAG retrieval
        
        Args:
            text: Full text to chunk
            chunk_size: Target size of each chunk (in characters)
            overlap: Overlap between chunks
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Split by sentences (simple approach)
        sentences = text.replace('\n', ' ').split('. ')
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            sentence = sentence.strip() + '. '
            
            # If adding this sentence exceeds chunk_size, save current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': current_chunk.strip(),
                    'length': len(current_chunk)
                })
                
                # Start new chunk with overlap
                # Keep last 'overlap' characters
                current_chunk = current_chunk[-overlap:] + sentence
                chunk_id += 1
            else:
                current_chunk += sentence
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'chunk_id': chunk_id,
                'text': current_chunk.strip(),
                'length': len(current_chunk)
            })
        
        return chunks
    
    def process_card_pdf(self, pdf_path: Path, card_name: str) -> Dict:
        """
        Process a single card PDF
        
        Returns:
            Dictionary with card metadata and chunks
        """
        print(f"Processing: {card_name}")
        
        # Extract text
        full_text = self.extract_text_from_pdf(pdf_path)
        
        if not full_text:
            return None
        
        # Create chunks
        chunks = self.chunk_text(full_text)
        
        # Add metadata to each chunk
        for chunk in chunks:
            chunk['card_name'] = card_name
            chunk['source_file'] = str(pdf_path.name)
        
        processed_data = {
            'card_name': card_name,
            'source_file': str(pdf_path.name),
            'full_text_length': len(full_text),
            'num_chunks': len(chunks),
            'chunks': chunks
        }
        
        # Save processed data
        output_file = self.output_dir / f"{card_name.lower().replace(' ', '_')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2)
        
        print(f"✓ Processed {len(chunks)} chunks for {card_name}")
        
        return processed_data
    
    def process_all_pdfs(self) -> List[Dict]:
        """Process all PDFs in the pdf directory"""
        
        if not self.pdf_dir.exists():
            print(f"PDF directory not found: {self.pdf_dir}")
            return []
        
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.pdf_dir}")
            return []
        
        print(f"Found {len(pdf_files)} PDF files")
        
        processed_cards = []
        
        for pdf_file in pdf_files:
            # Extract card name from filename
            card_name = pdf_file.stem.replace('_', ' ').title()
            
            result = self.process_card_pdf(pdf_file, card_name)
            
            if result:
                processed_cards.append(result)
        
        print(f"\n✓ Successfully processed {len(processed_cards)} cards")
        
        return processed_cards


# Example usage
if __name__ == "__main__":
    processor = PDFProcessor()
    cards = processor.process_all_pdfs()
    
    print(f"\nProcessed {len(cards)} cards:")
    for card in cards:
        print(f"  - {card['card_name']}: {card['num_chunks']} chunks")
