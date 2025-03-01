import streamlit as st
import os
from typing import List, Dict
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import tempfile
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = 'AIzaSyAATpS-kHvki7Oclgd_6Quz4hlIYH3wXwQ'
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Add to .env")
genai.configure(api_key=GOOGLE_API_KEY)

# --- Helper Functions ---

def load_and_split_pdf(pdf_file_path: str, chunk_size: int, chunk_overlap: int, text_splitter_type: str) -> List[str]:
    try:
        loader = PyPDFLoader(pdf_file_path)
        documents = loader.load()

        if text_splitter_type == "recursive":
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif text_splitter_type == "character":
            text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator="\n")
        else:
            raise ValueError("Invalid text_splitter_type. Choose 'recursive' or 'character'.")

        texts = text_splitter.split_documents(documents)
        return texts

    except FileNotFoundError:
        st.error(f"File not found: {pdf_file_path}")
        return []
    except Exception as e:
        st.error(f"PDF processing error: {e}")
        return []


def create_embeddings(texts: List[str], embedding_model_name: str) -> FAISS:
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model_name)
        db = FAISS.from_documents(texts, embeddings)
        return db
    except Exception as e:
        st.error(f"Embedding error: {e}")
        return None


def setup_qa_chain(db: FAISS, model_name: str, temperature: float, chain_type: str) -> RetrievalQA:
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=GOOGLE_API_KEY,
                                    convert_system_message_to_human=True)
        qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type=chain_type, retriever=db.as_retriever())
        return qa_chain
    except Exception as e:
        st.error(f"QA chain setup error: {e}")
        return None


# --- Streamlit App ---

def main():
    st.set_page_config(page_title="Document Q&A with Gemini", page_icon=":book:")
    st.title("Document Q&A with Gemini")

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    with st.sidebar:
        st.header("Configuration")

        # --- Model Selection ---
        # Get available Gemini models dynamically
        available_models = [m.name for m in genai.list_models()]
        #Filter out non chat models
        chat_models = [model for model in available_models if 'generateContent' in genai.get_model(model).supported_generation_methods]
        llm_model_name = st.selectbox("Select Gemini LLM Model:", chat_models, index=0, help="Choose the Gemini model for question answering.")
        
        embedding_models = [model for model in available_models if 'embedContent' in genai.get_model(model).supported_generation_methods]
        embedding_model_name = st.selectbox("Select Gemini Embedding Model:",
                                            embedding_models,
                                            index=0,
                                            help="Choose the Gemini model for creating embeddings.") # Keep separate embedding model selection

        temperature = st.slider("Temperature:", 0.0, 1.0, 0.0, 0.1)
        chain_type = st.selectbox("Chain Type:", ["stuff", "map_reduce", "refine"], index=0)
        chunk_size = st.number_input("Chunk Size:", min_value=100, max_value=8192, value=1000, step=100)
        chunk_overlap = st.number_input("Chunk Overlap:", min_value=0, max_value=4096, value=200, step=50)
        text_splitter_type = st.selectbox("Text Splitter:", ["recursive", "character"], index=0)


    if uploaded_file:
        with st.spinner("Processing..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_file_path = tmp_file.name

            texts = load_and_split_pdf(temp_file_path, chunk_size, chunk_overlap, text_splitter_type)
            if not texts: return

            db = create_embeddings(texts, embedding_model_name)
            if not db: return

            qa_chain = setup_qa_chain(db, llm_model_name, temperature, chain_type)  # Use selected LLM model
            if not qa_chain: return
            os.remove(temp_file_path)

        st.write("---")
        question = st.text_input("Ask a question:")
        if question:
            with st.spinner("Generating..."):
                result = qa_chain.invoke({"query": question})
                st.write("**Answer:**")
                st.write(result['result'])


if __name__ == "__main__":
    main()