from sentence_transformers import SentenceTransformer
from typing import List, Dict
from torch import Tensor
from torch.cuda import is_available
import json
model = SentenceTransformer(
    'BAAI/bge-m3',
    device='cuda' if is_available() else 'cpu'
)

def encode_text(text: List[str]) -> Tensor:
    return model.encode(
        text, 
        convert_to_tensor=True,
        max_length=8192,
        truncation=True
        )

def compute_similarity(text1: List[str], text2: List[str]) -> Tensor:
    text1_embedding = encode_text(text1)
    text2_embedding = encode_text(text2)
    similarity = model.similarity(text1_embedding, text2_embedding)
    print(similarity.shape)
    return similarity

def split_text(texts: Dict[str, str], chunk_size: int = 8192) -> List[str]:
    '''
    No overlap for now.
    '''
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    # Convert items to list for easier manipulation
    items = list(texts.items())
    chunks: List[Dict[str, str]] = []
    current_chunk: Dict[str, str] = {}
    current_size = 0

    for key, value in items:
        # Estimate the size of this item (key + value + some JSON overhead)
        item_size = len(key) + len(value) + 10  # 10 for JSON formatting characters

        # If adding this item would exceed chunk_size, save current chunk and start new one
        if current_size + item_size > chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = {}
            current_size = 0

        # Add item to current chunk
        current_chunk[key] = value
        current_size += item_size

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    print(len(chunks))
    print([len(chunk.values()) for chunk in chunks])
    for chunk in chunks:
        print(chunk.keys())
        print("-"*100)

    # convert to list of strings as json
    chunks_string = [
        json.dumps(chunk)
        for chunk in chunks
    ]

    if len(chunks_string) == 0:
        print(f"No chunks found for {json.dumps(texts)}")

    return chunks_string