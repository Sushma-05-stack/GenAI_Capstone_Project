from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
ef = DefaultEmbeddingFunction()
r = ef(["test sentence about RAG systems"])
print("ChromaDB ONNX OK, dim=", len(r[0]))
