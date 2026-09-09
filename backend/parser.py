import fitz # PyMuPDF
import json
import logging

def parse_pdf(file_path: str):
    doc = fitz.open(file_path)
    chunks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        
        # Simple chunking: one chunk per page for now
        # Could refine to split large pages later
        page_text = []
        bboxes = []
        for block in blocks:
            # block = (x0, y0, x1, y1, "text", block_no, block_type)
            if block[6] == 0: # text block
                text = block[4].strip()
                if text:
                    page_text.append(text)
                    bboxes.append({
                        "text": text,
                        "bbox": [block[0], block[1], block[2], block[3]]
                    })
        
        full_text = "\n".join(page_text)
        if full_text.strip():
            chunks.append({
                "page_number": page_num + 1,
                "text": full_text,
                "bboxes": bboxes
            })
            
    return chunks
