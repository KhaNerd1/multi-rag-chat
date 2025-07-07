import os
import streamlit as st
from utils import (
    save_uploaded_file,
    list_collections,
    collection_exists,
    create_collection,
    delete_collection,
    get_collection_files
)
from rag_chain import load_pdf, add_docs_to_collection, get_conversational_chain

st.set_page_config(page_title="📚 Multi-RAG Chatbot", layout="wide")
st.title("📚 Chat With Your Document Collections")

# --- Session state init ---
if "created_collection" not in st.session_state:
    st.session_state.created_collection = None
if "memories" not in st.session_state:
    st.session_state.memories = {}
if "chains" not in st.session_state:
    st.session_state.chains = {}
if "chat_history_ui" not in st.session_state:
    st.session_state.chat_history_ui = {}
if "ingestion_success" not in st.session_state:
    st.session_state.ingestion_success = False

# --- UI: collection select/create ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📂 Select a Collection")
    collections = list_collections()
    selected_collection = st.selectbox("Choose a collection:", [""] + collections)

with col2:
    st.subheader("🆕 Create New Collection")
    new_collection = st.text_input("Collection name")
    if st.button("Create Collection"):
        if collection_exists(new_collection):
            st.warning("Collection already exists.")
        elif not new_collection.strip():
            st.error("Please enter a valid name.")
        else:
            create_collection(new_collection)
            st.session_state.created_collection = new_collection
            st.rerun()

    if st.session_state.created_collection:
        st.success(f"Created collection: '{st.session_state.created_collection}' ✅")
        st.session_state.created_collection = None

st.divider()

# --- Main content ---
if selected_collection:
    index_path = f"collections/{selected_collection}/index.faiss"

    st.subheader(f"📄 Upload PDFs to '{selected_collection}'")

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"uploader_{selected_collection}"
    )

    if uploaded_files and st.button("➕ Add Files"):
        with st.spinner("📥 Ingesting files..."):
            for file in uploaded_files:
                file_path = save_uploaded_file(file)
                docs = load_pdf(file_path)
                add_docs_to_collection(selected_collection, docs, filename=file.name)
        st.session_state.ingestion_success = True

    if st.session_state.ingestion_success:
        st.success("✅ Ingestion complete.")
        st.session_state.ingestion_success = False

    if st.button("📂 Show Ingested Files"):
        files = get_collection_files(selected_collection)
        if files:
            st.info("Files in this collection:")
            for f in files:
                st.markdown(f"- {f}")
        else:
            st.warning("No files found in this collection.")

    st.markdown("### ⚠️ Danger Zone")
    if st.button(f"🗑️ Delete Collection '{selected_collection}'"):
        delete_collection(selected_collection)

        # 🧹 Clean up all session state for this collection
        st.session_state.chains.pop(selected_collection, None)
        st.session_state.memories.pop(selected_collection, None)
        st.session_state.chat_history_ui.pop(selected_collection, None)

        st.success(f"Collection '{selected_collection}' deleted and history cleared.")
        st.rerun()

    st.divider()
    st.subheader("💬 Ask Your Document a Question")

    if os.path.exists(index_path):
        if selected_collection not in st.session_state.chains:
            chain, memory = get_conversational_chain(selected_collection)
            st.session_state.chains[selected_collection] = chain
            st.session_state.memories[selected_collection] = memory
            st.session_state.chat_history_ui[selected_collection] = []

        user_query = st.text_input("Ask something...", key=f"text_input_{selected_collection}")
        submit = st.button("💬 Submit Question")

        if submit and user_query.strip():
            with st.spinner("🔎 Thinking..."):
                chain = st.session_state.chains[selected_collection]
                result = chain.run(question=user_query)
                st.session_state.chat_history_ui[selected_collection].append({
                    "question": user_query,
                    "answer": result
                })
            st.rerun()  # only rerun for chat clear

        if st.session_state.chat_history_ui[selected_collection]:
            st.markdown("### 🕘 Chat History")
            for i, chat in enumerate(st.session_state.chat_history_ui[selected_collection][::-1]):
                st.markdown(f"**Q{i+1}:** {chat['question']}")
                st.markdown(f"**A{i+1}:** {chat['answer']}")
                st.markdown("---")

    else:
        st.info("This collection is empty. Upload documents to begin chatting.")

else:
    st.info("Select a collection to begin.")
