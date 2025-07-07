import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from utils import add_file_to_metadata

def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    return loader.load()

def add_docs_to_collection(collection_name, docs, filename=None):
    index_path = f"collections/{collection_name}"
    os.makedirs(index_path, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    texts = splitter.split_documents(docs)

    embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

    if os.path.exists(f"{index_path}/index.faiss"):
        vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        vectordb.add_documents(texts)
    else:
        vectordb = FAISS.from_documents(texts, embeddings)
    vectordb.save_local(index_path)

    if filename:
        add_file_to_metadata(collection_name, filename)

def get_conversational_chain(collection_name):
    index_path = f"collections/{collection_name}"
    index_file = os.path.join(index_path, "index.faiss")

    if not os.path.exists(index_file):
        raise FileNotFoundError(
            f"Collection '{collection_name}' doesn't have any documents yet. "
            f"Please upload PDFs before chatting."
        )

    embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
    vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vectordb.as_retriever()

    llm = Ollama(model="llama3.2:latest")

    prompt = PromptTemplate(
        input_variables=["chat_history", "context", "question"],
        template="""
You are an intelligent assistant. Use only the information retrieved from the context to answer the user's question.

If the answer is not found in the context, say: "I'm sorry, I couldn't find information about that in the uploaded documents."

Do not use any outside knowledge. Never make up information. If the context includes multiple possible answers, explain them all clearly.

Maintain a friendly, clear, and professional tone.

Context:
{context}

Chat History:
{chat_history}

Question:
{question}

Answer:
"""
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt}
    )

    return chain, memory
