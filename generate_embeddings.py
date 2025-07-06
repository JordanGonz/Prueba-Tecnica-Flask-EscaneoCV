import pickle
from models import Candidate
from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_text_for_embedding(candidate):
    def parse_json_field(field):
        try:
            parsed = json.loads(field)
            if isinstance(parsed, list):
                return ", ".join(parsed)
            return str(parsed)
        except:
            return str(field or "")

    return " ".join(filter(None, [
        candidate.name,
        parse_json_field(candidate.skills),
        parse_json_field(candidate.summary),
        parse_json_field(candidate.experience),
        parse_json_field(candidate.education)
    ])).strip()
    
def generate_candidate_embeddings():
    from app import app
    from extensions import db  

    with app.app_context():
        candidates = Candidate.query.all()
        embeddings = {}

        for c in candidates:
            text = get_text_for_embedding(c)
            if text:
                emb = model.encode(text)
                embeddings[c.id] = emb

        with open('candidate_vectors.pkl', 'wb') as f:
            pickle.dump(embeddings, f)

        print(f"✅ Se generaron {len(embeddings)} embeddings y se guardaron en 'candidate_vectors.pkl'")

if __name__ == '__main__':
    generate_candidate_embeddings()
