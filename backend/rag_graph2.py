import os
from dotenv import load_dotenv
import logging
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from typing_extensions import TypedDict, List
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def format_chat_history_for_llm(chat_history: List[BaseMessage]) -> str: # Changed type hint
    """
    Converts a list of Langchain BaseMessage objects into a single, readable string for LLM prompts.
    """
    formatted_history = []
    for message in chat_history:
        # Now accessing .type and .content attributes directly from BaseMessage objects
        if isinstance(message, HumanMessage):
            role = "User"
        elif isinstance(message, AIMessage):
            role = "Assistant"
        else:
            role = message.type # Fallback for other message types if they appear

        formatted_history.append(f"{role}: {message.content}")
    return "\n".join(formatted_history)




def build_rag_graph(rag_llm):
    """
    Builds and compiles the RAG LangGraph.
    Args:
        rag_llm: The LLM instance to be used for RAG operations (e.g., LLaMA 3.3 70B).
    """
    if not rag_llm:
        logger.error("No LLM instance provided to build_rag_graph. RAG functionality will be limited.")
        return None  # Return None if LLM is not available
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    try:
        vector_store = FAISS.load_local("../synthetic_hr_policy", embedding_model, allow_dangerous_deserialization=True)
        logger.info("FAISS vector store loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load FAISS vector store: {e}. RAG retrieval will not work.")
        vector_store = None

    rag_prompt = PromptTemplate.from_template("""
    You are an HR assistant. Use the following policy documents and the conversation history to answer the question.
    Keep the answer brief, professional, and directly address the user's query.
    
    Conversation History:
    {chat_history}

    Context:
    {context}

    Question:
    {question}
    """)

    class RAGState(TypedDict):
        question: str
        chat_history: List[BaseMessage]
        context: List[Document]
        answer: str
        error: str

    def retrieve(state: RAGState):
        if not vector_store:
            logger.error("Vector store not available for retrieval.")
            return {"context": [], "error": "RAG retrieval system not available."}
        if not rag_llm:
            logger.error("LLM not available for query rephrasing in retrieval.")
            return {"context": [], "error": "LLM not available for RAG query rephrasing."}

        # FIX: Format the chat_history for the rephrasing LLM prompt
        formatted_chat_history = format_chat_history_for_llm(state["chat_history"])

        rephrase_prompt = PromptTemplate.from_template("""
        Given the following conversation history and a follow-up question, rephrase the follow-up question
        to be a standalone, clear search query for a policy document.
        Focus on extracting the core subject of the query.
        
        Conversation History:
        {chat_history}
        
        Follow-up Question:
        {question}
        
        Rephrased Search Query:
        """)

        try:
            rephrased_query_response = rag_llm.invoke(
                rephrase_prompt.invoke({"question": state["question"], "chat_history": formatted_chat_history})
            )
            search_query = rephrased_query_response.content.strip()
            logger.info(f"Original RAG question: '{state['question']}'")
            logger.info(f"Rephrased RAG search query: '{search_query}'")
        except Exception as e:
            logger.error(f"Error rephrasing RAG query: {e}. Using original question for search.")
            search_query = state["question"]  # Fallback to original question

        try:
            retrieved_docs = vector_store.similarity_search(search_query, k=5)
            return {"context": retrieved_docs}
        except Exception as e:
            logger.error(f"Error during vector store similarity search: {e}")
            return {"context": [], "error": f"RAG retrieval failed: {str(e)}"}




    def generate(state: RAGState):
        if not rag_llm:
            logger.error("LLM not available for RAG answer generation.")
            return {"answer": "", "error": "LLM not available for RAG answer generation."}

        if not state["context"]:
            logger.warning("No context retrieved for RAG generation.")
            return {"answer": "I couldn't find relevant policy information for your question.",
                    "error": "No context for RAG."}

        context = "\n\n".join(doc.page_content for doc in state["context"])

        # FIX: Format the chat_history for the final RAG answer generation prompt
        formatted_chat_history = format_chat_history_for_llm(state["chat_history"])

        prompt = rag_prompt.invoke({
            "context": context,
            "question": state["question"],
            "chat_history": formatted_chat_history  # Pass chat_history here
        })

        try:
            response = rag_llm.invoke(prompt)
            return {"answer": response.content}
        except Exception as e:
            logger.error(f"Error generating RAG answer: {e}")
            return {"answer": "", "error": f"RAG answer generation failed: {str(e)}"}

    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    return graph.compile()






