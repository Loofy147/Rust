import logging
from typing import List, Optional, Dict, Callable, Set
from faiss_vector_store import FAISSVectorStore
from super_advanced_agents import EmbeddingPipeline, MultiModalEmbeddingPipeline
from PIL import Image
from collections import Counter
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrainingDataAgent")

class TrainingDataAgent:
    def __init__(self, vector_store: FAISSVectorStore, text_embedder: EmbeddingPipeline, image_embedder: Optional[MultiModalEmbeddingPipeline] = None):
        self.vector_store = vector_store
        self.text_embedder = text_embedder
        self.image_embedder = image_embedder
        self.raw_texts = []
        self.raw_images = []
        self.processed = 0
        self.labels = set()
        self.duplicates: Set[str] = set()
        self.validation_errors = []
        self.stats = {}

    def ingest_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None, label: Optional[str] = None):
        for i, text in enumerate(texts):
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            if label:
                meta["label"] = label
                self.labels.add(label)
            vector = self.text_embedder.embed(text)
            self.vector_store.add(vector, {**meta, "text": text, "type": "training_text"})
            self.raw_texts.append(text)
            self.processed += 1
        logger.info(f"Ingested {len(texts)} texts.")

    def ingest_documents(self, docs: List[str], chunk_size: int = 256, overlap: int = 32, label: Optional[str] = None):
        for doc in docs:
            chunks = self.chunk_text(doc, chunk_size, overlap)
            self.ingest_texts(chunks, label=label)
        logger.info(f"Ingested {len(docs)} documents (chunked).")

    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i+chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    def ingest_images(self, images: List[Image.Image], metadatas: Optional[List[Dict]] = None, label: Optional[str] = None):
        if not self.image_embedder:
            raise RuntimeError("Image embedder not provided.")
        for i, img in enumerate(images):
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            if label:
                meta["label"] = label
                self.labels.add(label)
            vector = self.image_embedder.embed_image(img)
            self.vector_store.add(vector, {**meta, "type": "training_image"})
            self.raw_images.append(img)
            self.processed += 1
        logger.info(f"Ingested {len(images)} images.")

    def deduplicate(self):
        seen = set()
        new_metadata = []
        for meta in self.vector_store.metadata:
            if meta and meta.get("text"):
                if meta["text"] in seen:
                    self.duplicates.add(meta["text"])
                else:
                    seen.add(meta["text"])
                    new_metadata.append(meta)
        self.vector_store.metadata = new_metadata
        logger.info(f"Deduplicated training data. {len(self.duplicates)} duplicates found.")

    def report_duplicates(self):
        logger.info(f"Duplicate texts: {list(self.duplicates)}")
        return list(self.duplicates)

    def normalize(self):
        for meta in self.vector_store.metadata:
            if meta and "text" in meta:
                meta["text"] = meta["text"].lower()
        logger.info("Normalized all text to lowercase.")

    def validate(self, validator: Optional[Callable[[str], bool]] = None):
        self.validation_errors = []
        for meta in self.vector_store.metadata:
            if meta and "text" in meta:
                text = meta["text"]
                if validator and not validator(text):
                    self.validation_errors.append(text)
        logger.info(f"Validation complete. {len(self.validation_errors)} errors found.")
        return self.validation_errors

    def compute_stats(self):
        lengths = [len(meta["text"]) for meta in self.vector_store.metadata if meta and "text" in meta]
        vocab = Counter()
        for meta in self.vector_store.metadata:
            if meta and "text" in meta:
                tokens = re.findall(r"\w+", meta["text"].lower())
                vocab.update(tokens)
        self.stats = {
            "num_texts": len(lengths),
            "avg_length": sum(lengths)/len(lengths) if lengths else 0,
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "vocab_size": len(vocab),
            "top_vocab": vocab.most_common(10)
        }
        logger.info(f"Stats: {self.stats}")
        return self.stats

    def export_for_finetuning(self, path: str):
        import json
        with open(path, "w") as f:
            for meta in self.vector_store.metadata:
                if meta and "text" in meta:
                    f.write(json.dumps({"text": meta["text"]}) + "\n")
        logger.info(f"Exported training data to {path}")

    def get_stats(self):
        return {
            "texts": len(self.raw_texts),
            "images": len(self.raw_images),
            "processed": self.processed,
            "vector_store_count": len(self.vector_store.metadata),
            "labels": list(self.labels),
            "duplicates": len(self.duplicates),
            "validation_errors": len(self.validation_errors),
            "stats": self.stats
        }

if __name__ == "__main__":
    # Example usage
    store = FAISSVectorStore(dim=384)
    embedder = EmbeddingPipeline()
    agent = TrainingDataAgent(store, embedder)
    agent.ingest_texts(["Paris is beautiful.", "Berlin is historic.", "Paris is beautiful."], label="city")
    agent.ingest_documents(["Rome is ancient. The Colosseum is in Rome."], chunk_size=5, overlap=1, label="history")
    agent.normalize()
    agent.deduplicate()
    agent.report_duplicates()
    agent.validate(lambda t: len(t) > 10)  # Example: text must be >10 chars
    agent.compute_stats()
    agent.export_for_finetuning("train_data.jsonl")
    print(agent.get_stats())