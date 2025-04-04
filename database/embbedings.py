from sentence_transformers import SentenceTransformer
from torch import Tensor
from torch.cuda import is_available
from bson.binary import Binary
from bson.binary import BinaryVectorDtype

model = SentenceTransformer(
            'BAAI/bge-m3',
            device='cuda' if is_available() else 'cpu'
        )

print("Initialized BGE model with device: ", model.device)

def encode_text(text: str, precision: str = "float32") -> Tensor:
    return model.encode(
            text, 
            convert_to_tensor=True,
            max_length=8192,
            truncation=True,
            precision=precision
        )

def generate_bson_vector(vector, vector_dtype=BinaryVectorDtype.FLOAT32):
    return Binary.from_vector(vector, vector_dtype)