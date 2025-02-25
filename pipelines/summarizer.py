from transformers import pipeline
from typing import Any

summarizer = pipeline(
    "summarization",
    model="google-t5/t5-large",
    device="cpu"
)

def summarize(text: str) -> Any:
    return summarizer(text, max_length=text.count(" ") * 2, min_length=text.count(" ") * 1, do_sample=False)

