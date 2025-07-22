import logging
from typing import Dict

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory


# Set up logging for debugging and tracking memory behavior
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Ensure logging is configured for this module too

# ---------------------------------------------------------------------
# This module handles session-specific chat memory for your chatbot.
# It provides a function `get_session_history` to return or create
# memory for a unique session_id. This memory helps your LangChain
# chatbot maintain contextual conversation for each user.
#
# NOTE: Memory is currently in-memory (RAM only), which means all
# chat history will be lost when the server restarts. In production,
# this should be replaced with persistent memory (e.g. Redis, Firestore).
# ---------------------------------------------------------------------

def get_session_history(session_id: str, app_session_histories: Dict[str, InMemoryChatMessageHistory]) -> BaseChatMessageHistory:
    """
     Retrieve or create a chat message history object for a specific session.

    Args:
        session_id (str): A unique identifier for the user's session.
        app_session_histories (Dict[str, InMemoryChatMessageHistory]):
            A global dictionary storing session-wise memory objects.

    Returns:
        BaseChatMessageHistory: The memory object storing chat history for this session.
    """

    # If no history exists for this session, initialize a new memory object
    if session_id not in app_session_histories:
        app_session_histories[session_id] = InMemoryChatMessageHistory()
        logger.info(f"Creating new session history for session_id: {session_id}")
    else:
        logger.info(f"Retrieving existing session history for session_id: {session_id}")

    # Fetch the memory object for this session
    history = app_session_histories[session_id]

    # --- NEW DEBUG LOGS ---
    logger.info(f"DEBUG: mem_store - History for session '{session_id}' contains {len(history.messages)} messages:")
    # for i, msg in enumerate(history.messages):
    #     logger.info(f"  [{i}] {msg.type}: {msg.content}")
    # --- END NEW DEBUG LOGS ---

    return history

# You could add functions here for clearing history, loading/saving from disk/DB, etc.
# For now, this is all you need for in-memory session management.
