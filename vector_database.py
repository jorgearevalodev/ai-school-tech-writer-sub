import chromadb
from chromadb.config import Settings

class VectorDatabase:
    def __init__(self, persist_directory="data"):
        # Setup Chroma with persistent storage
        self.client = chromadb.PersistentClient(
            path=persist_directory  # Directory where the data will be stored
        )

        # Create or get the collection. This will reuse the existing collection if it already exists.
        self.collection = self.client.get_or_create_collection("all-my-documents")

    def add_documents_params(self, documents, metadatas, ids):
        # Add docs to the collection. Can also update and delete. Row-based API coming soon!
        self.collection.add(
            documents=documents,  # we handle tokenization, embedding, and indexing automatically. You can skip that and add your own embeddings as well
            metadatas=metadatas,  # filter on these!
            ids=ids  # unique for each doc
        )


    def add_documents(self, docs: list):
        # Extract documents, metadatas, and ids from the list of dictionaries
        documents = [doc['document'] for doc in docs]
        metadatas = [doc['metadata'] for doc in docs]
        ids = [doc['id'] for doc in docs]

        # Add docs to the collection
        self.add_documents_params(documents, metadatas, ids)

    def query_documents(self, query_texts, n_results=2):
        # Query/search n most similar results. You can also .get by id
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            # where={"metadata_field": "is_equal_to_this"}, # optional filter
            # where_document={"$contains": "search_string"}  # optional filter
        )
        print(results)
        list_results = []   
        for i in range(len(results['ids'][0])):
            list_results.append({
                "id": results['ids'][0][i],
                "metadata": results['metadatas'][0][i], # Changed 'metadata' to 'metadatas'
                "document": results['documents'][0][i], # Changed 'document' to 'documents
                "distance": results['distances'][0][i] # Changed 'distance' to 'distances'
            })
        return list_results

# Example usage
if __name__ == "__main__":
    vector_db = VectorDatabase()

    # Add documents
    #vector_db.add_documents(
    #    documents=["This is document1", "This is document2", "This is a spreadsheet"],
    #    metadatas=[{"source": "notion"}, {"source": "google-docs"}, {"source": "excel"}],
    #    ids=["doc1", "doc2", "sheet1"]
    #)
    vector_db.add_documents([
        {"document": "This is document3", "metadata": {"source": "notion"}, "id": "doc3"},
        {"document": "This is document4", "metadata": {"source": "google-docs"}, "id": "doc4"},
        {"document": "This is a spreadsheet document", "metadata": {"source": "excel"}, "id": "sheet2"}
    
    ])

    # Query documents
    results = vector_db.query_documents(query_texts=["This is a spreadsheet document"], n_results=5)
    print(results)