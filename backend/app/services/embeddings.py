"""
Text Embeddings Service.

Uses Sentence Transformers to encode text into fixed-size dense vectors.
The model is loaded into memory once and reused for all subsequent encode calls.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingsService:
    """Singleton wrapper around the SentenceTransformer model."""

    _model: SentenceTransformer | None = None
    _MODEL_NAME = "all-MiniLM-L6-v2"

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """
        Lazily load and return the embedding model.
        The model weights (~80MB) are downloaded on the first run and cached.
        """
        if cls._model is None:
            logger.info("Loading sentence transformer model '%s' ...", cls._MODEL_NAME)
            cls._model = SentenceTransformer(cls._MODEL_NAME)
            logger.info("Sentence transformer '%s' loaded successfully.", cls._MODEL_NAME)
        return cls._model

    @classmethod
    def encode(cls, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Encode single string or batch of strings into dense vectors.

        Args:
            text: A single string or a list of strings to embed.

        Returns:
            A list of floats (for a single string) or a list of lists of floats.
        """
        model = cls.get_model()

        # Convert to a list of lists if single vector, else list of lists of floats
        embeddings_tensor = model.encode(text, convert_to_tensor=False)

        # PyTorch returns numpy arrays, convert them to standard Python lists
        if isinstance(text, str):
            # embeddings_tensor is a 1D numpy array
            return embeddings_tensor.tolist()  # type: ignore
        else:
            # embeddings_tensor is a 2D numpy array
            return [emb.tolist() for emb in embeddings_tensor]
