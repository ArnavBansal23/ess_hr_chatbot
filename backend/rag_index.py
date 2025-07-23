from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader


def build_vectorstore():
    # 1. loading the document
    loader = TextLoader("backend/synthetic_hr_policy.txt")
    docs = loader.load()

    #2. splitting the text into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    # 3. Embed and store in FAISS
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embedding_model)
    print("Vector store created successfully!")

    #5. saving the vector store locally
    vectorstore.save_local("index_folder")
    print("✅ Vector store saved!")

if __name__ == "__main__":
    build_vectorstore()




