from rapidfuzz import fuzz

def find_best_bbox(evidence_text, bboxes):
    if not evidence_text or not bboxes:
        return None
    best_bbox = None
    best_score = 0
    for b in bboxes:
        score = fuzz.partial_ratio(evidence_text, b["text"])
        if score > best_score:
            best_score = score
            best_bbox = b["bbox"]
    if best_score > 70:
        return best_bbox
    return None
