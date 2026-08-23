from sentence_transformers import SentenceTransformer
from PIL import Image
import requests
from io import BytesIO

# Loaded once at import time — the model stays in memory for the life
# of the Django process, so we don't reload it on every request.
_model = None


_clip_model = None


def get_clip_model():
    global _clip_model
    if _clip_model is None:
        _clip_model = SentenceTransformer("clip-ViT-B-32")
    return _clip_model


def compute_image_embedding(image_url):
    """Downloads an image from its URL and returns a 512-dim CLIP embedding."""
    if not image_url:
        return None
    try:
        response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(response.content)).convert("RGB")
        model = get_clip_model()
        embedding = model.encode(image, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Failed to compute image embedding for {image_url}: {e}")
        return None

def get_model():
    global _model
    if _model is None:
        # all-MiniLM-L6-v2: small (~80MB), fast on CPU, 384-dim output —
        # matches the VectorField(dimensions=384) we set up back in Step 7.
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def compute_text_embedding(text):
    """Returns a 384-dim embedding vector for the given text, as a list of floats."""
    if not text or not text.strip():
        return None
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two vectors, assuming both are already normalized."""
    if vec_a is None or vec_b is None:
        return 0.0
    import numpy as np
    a = np.array(vec_a)
    b = np.array(vec_b)
    # Since both vectors are normalized (unit length), dot product == cosine similarity
    return float(np.dot(a, b))