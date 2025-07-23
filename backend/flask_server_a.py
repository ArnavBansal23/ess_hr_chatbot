from dotenv import load_dotenv
load_dotenv()
from config import Config
from db import init_db
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from flask import Flask, request, jsonify
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing_extensions import TypedDict, List, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.graph import StateGraph
from langchain_core.documents import Document
# from langchain.chat_models import init_chat_model
from langchain_groq import ChatGroq

from langchain_core.runnables.history import RunnableWithMessageHistory  # For memory management
from typing import Literal
from collections import defaultdict
from mem_store import get_session_history  # Import get_session_history from your new memory_store.py file
from rag_graph2 import build_rag_graph
from auth_routes import create_auth_blueprint
from auth import get_current_user
# from typing import Union
# from pydantic import BaseModel
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address


from flask_cors import CORS
# Step 1: Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["200 per day", "50 per hour"],  # Example global limits
# )

from flask_jwt_extended import JWTManager
jwt = JWTManager(app)

@jwt.unauthorized_loader
def handle_missing_token(reason):
    return jsonify({"error": "Missing or invalid access token", "details": reason}), 401

@jwt.invalid_token_loader
def handle_invalid_token(reason):
    return jsonify({"error": "Invalid token", "details": reason}), 422

@jwt.expired_token_loader
def handle_expired_token(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llama3_api_key = app.config["GROQ_API_KEY"]
if not llama3_api_key:
    logger.error("GROQ_API_KEY environment variable not set. LLM initialization might fail.")

# LLM
try:
    # llm = init_chat_model("llama-3.3-70b-versatile", model_provider="groq", groq_api_key=llama3_api_key)
    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=llama3_api_key)
    logger.info("LLM initialized successfully")

except Exception as e:
    logger.error(f"Failed to initialize LLM: {e}")
    llm = None

# Build the RAG chain once
try:
    rag_chain = build_rag_graph(llm)
    logger.info("RAG chain built successfully.")
except Exception as e:
    logger.error(f"Failed to build RAG graph: {e}. Policy queries might not work.")
    rag_chain = None  # Set to None if it fails to initialize



# NEW: Initialize session_histories directly on the Flask app object
# This ensures the dictionary persists across requests for the life of the app instance.

app.session_histories = defaultdict(InMemoryChatMessageHistory)


# Connecting to MySQL DB
db = init_db()
if not db:
    logger.error("Database connection failed. Exiting...")
    exit(1)



# Define supported query categories
QueryType = Literal["DATABASE", "POLICY", "HYBRID"]




def format_chat_history_for_llm(chat_history: List[BaseMessage]) -> str:
    """
    Convert list of LangChain messages to readable plain-text format for prompts.
    Differentiates between user and assistant messages.
    """
    formatted_history = []
    for message in chat_history:
        # Now accessing .type and .content attributes directly from BaseMessage objects
        if isinstance(message, HumanMessage):
            role = "User"
        elif isinstance(message, AIMessage):
            role = "Assistant"
        else:
            role = message.type  # Fallback for other message types if they appear

        formatted_history.append(f"{role}: {message.content}")
    return "\n".join(formatted_history)


class State(TypedDict):
    employee_code: int
    role: str
    question: str
    chat_history: List[BaseMessage]
    query_type: QueryType
    sql_query: str
    sql_result: str
    retrieved_docs: List[Document]
    rag_result: str
    final_answer: str
    error: str


# def validate_sql_query(query_result: Union[dict, BaseModel]) -> bool:
#     """Basic SQL query validation for security."""
#     # Extract SQL query string from result object
#     if isinstance(query_result, dict):
#         query = query_result.get("query", "")
#     elif hasattr(query_result, 'query'):
#         query = query_result.query
#     else:
#         query = str(query_result)
#     if not query or not query.strip():
#         return False
#
#     # Convert to lowercase for checking
#     query_lower = query.lower().strip()
#
#     # Block potentially dangerous operations
#     dangerous_keywords = [
#         'drop', 'delete', 'insert', 'update', 'alter', 'create',
#         'truncate', 'replace', 'grant', 'revoke'
#     ]
#
#     for keyword in dangerous_keywords:
#         if keyword in query_lower:
#             logger.warning(f"Blocked potentially dangerous SQL keyword: {keyword}")
#             return False
#
#     # # Must start with SELECT
#     # if not query_lower.startswith('select'):
#     #     logger.warning("SQL query must start with SELECT")
#     #     return False
#
#     return True


def classify_query(state: State):
    """
    Determine if query is about database data, policies, or both.
    Uses chat_history for context-aware classification.
    """

    try:
        if not llm:
            logger.error("LLM not available for classification.")
            return {"error": "LLM not available", "query_type": "DATABASE"}

        formatted_chat_history = format_chat_history_for_llm(state["chat_history"])
        # logger.info(f"Classify Query - Formatted Chat History:\n{formatted_chat_history}")

        classification_template = PromptTemplate.from_template("""
         You are a query classifier for an HR chatbot. Classify the user's question into one of these categories:
         1. DATABASE – Ask for employee-specific data only.
            Examples:
             - "How many earned leaves do I have?"
             - "What is my designation?"
             - "Show Neha Reddy's salary slip for June"

         2. POLICY – Ask about HR policies or procedures, no data lookup needed.
            Examples:
             - "What is the paternity leave policy?"
             - "Can interns get LTA?"
             - "What are the conditions for getting a bonus?"
             - "What are the working hours?"
             - 

         3. HYBRID – Require both personal data + HR policy to answer.
            Examples:
             - "Am I eligible for maternity leave?" (needs gender + employment_status + policy)
             - "Can I take sick leave tomorrow?" (needs leave balance + rules)
             - "Why didn't Neha Reddy get a bonus this year?" (needs salary data + employment_status + bonus eligibility rules)
             - "Can I claim LTA this year?" (needs history + employment_status + policy)
             - "Is Neha eligible for paid leaves?" (needs employment_status + leave policy)


         Only return one of the following values exactly: DATABASE, POLICY, HYBRID

         Chat History: {chat_history}
         Question: {question}
         """)

        prompt = classification_template.invoke({"question": state["question"], "chat_history": formatted_chat_history})
        response = llm.invoke(prompt)
        query_type = response.content.strip().upper()

        if query_type not in ["DATABASE", "POLICY", "HYBRID"]:
            logger.warning(f"Invalid query type returned: {query_type}, defaulting to DATABASE")
            query_type = "DATABASE"

        logger.info(f"Query classified as: {query_type}")
        return {"query_type": query_type}

    except Exception as e:
        logger.error(f"Error in query classification: {e}")
        return {"error": f"Classification failed: {str(e)}", "query_type": "DATABASE"}


# System Prompt + User Prompt for SQL Query generation
system_message = """
You are an expert SQL query generator for an Employee Self-Service (ESS) HR assistant.

The user input **may include a step-by-step reasoning explanation before the actual question**.
Use this reasoning carefully to understand the query intent and build a better SQL query.

You also have access to the chat history. Use the chat history to understand context and resolve
ambiguities in the current question, such as pronouns (e.g., "her", "his") or implied entities.

---

USER CONTEXT:

- Employee Code: {employee_code}
- User Role: {role}

ROLE BASED ACCESS CONTROL RULES:

- If the user is an **employee**:
  - They can only access their own data.
  - Always add `WHERE employee_code = {employee_code}` or equivalent constraints.

- If the user is a **manager**:
  - They can access their own data.
  - They can access ONLY these types of data for employees who report to them:
    - Leave requests
    - Leave balances
    - Basic employee info (name, designation, department, employment status)
  - They CANNOT access:
    - Salary details
    - Contact information (email, phone, address)
    - Personal identifiers (date of birth etc.)
  - Apply filters like `WHERE supervisor_id = {employee_code}` AND restrict columns accordingly.

- If the user is an **hr_admin**:
  - They can access their own data
  - They can access all employee data. No filters are required.

If the user asks for someone else's data and is not authorized, DO NOT write a query.
Instead, respond with:
> "You are not authorized to access this information."

---        


VERY IMPORTANT INSTRUCTIONS:

- Only use the tables and columns provided below:
{table_info}

- NEVER guess or assume columns or table names. If something is not available in the schema, do not use it.
- NEVER select all columns (`SELECT *`). Only select columns directly relevant to answering the question.
- NEVER generate queries if the question is unrelated to employee data (e.g., general policy questions) — respond politely that this information is not stored in the database.

Step-by-Step Reasoning (before query generation):

1. Understand the **intent** of the question:
   - Is the user asking about eligibility, leave balance, salary, personal info, reporting structure, or something else?

2. Identify the **minimum required columns** to answer it.
3. Identify any **filter conditions** (e.g., employee name, leave type).
4. Choose the correct **tables** and valid **joins** if needed.
5. Enforce role-based access control before generating the query.

Examples:

- **Eligibility Check** (e.g., "Am I eligible for bonus, LTA or any other benefits?")
  → Must Check `employment_status`, `tenure_years`, and possibly `hire_date`

- **Leave Balance Inquiry** (e.g., "How many casual leaves do I have?")
  → Use `leave_balances`, filter by `employee_id` or `employee_name` and `leave_type`

- **Salary Info** (e.g., "What is my gross salary?")
  → Use `salary_summary` or aggregate from `salary_components`

- **Reporting Structure** (e.g., "Who is my manager?")
  → Use `employees` table, retrieve `supervisor_id`, and join back to get manager name

- **Personal Details** (e.g., "What is my  designation and department?")
  → Use `employees`, `departments`, and `designations` tables with appropriate joins
  
NEGATIVE EXAMPLES (AVOID THESE):

- **"What is Neha's salary?"**  
  → Unauthorized for non-HR users. Only `hr_admin` can view other employees’ salary info.  

- **"Show me salary and phone numbers of my team members."**  
  → Managers are not allowed to access salary and personal identifiers or contact info of reportees.  

- **"What is the company's sick leave policy?"**  
  → This is a general policy question. Do not generate SQL; this is handled by a different system.  

- **"What is Karan’s blood group?"**  
  → `blood_group` is not in the schema. Never guess columns or generate queries on non-existent fields.  

- **"SELECT * FROM employees;"**  
  → Never use `SELECT *`. Always specify relevant columns only.  

- **"Can you show me Neha's expense reports?"**  
  → Table `expense_reports` is not defined. Only use available tables in schema.

DO NOT:
- Select irrelevant or all columns
- Use data from synthetic HR policy docs — this is handled separately by the policy RAG
- Attempt to answer questions outside the database (e.g., "What is the leave policy?")
- Generate queries that bypass user access level

GOAL: Output a clean, precise SQL query in {dialect} that answers the question using only the available database tables.

"""

user_prompt = "Chat History: {chat_history}\nQuestion: {input}"

# Prompt template combining system and user messages
query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)


# Define Expected Output Format for Structured SQL Generation
class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


# Writing the SQL Query
def write_query(state: State):
    """
    Generate SQL query with explicit reasoning about required data.
    Uses chat_history for context-aware query generation.
    """
    if state["query_type"] in ["DATABASE", "HYBRID"]:
        if not db:
            logger.error("Database connection not available for writing query.")
            return {"sql_query": "", "error": "Database not connected. Cannot generate SQL query."}
        if not llm:
            logger.error("LLM not available for writing query.")
            return {"sql_query": "", "error": "LLM not available for SQL generation."}

        # FIX: Use formatted_chat_history in the reasoning prompt
        formatted_chat_history = format_chat_history_for_llm(state["chat_history"])
        # logger.info(f"Classify Query - Formatted Chat History:\n{formatted_chat_history}")

        # Reasoning prompt
        reasoning_prompt = PromptTemplate.from_template("""
        You are a helpful assistant for an HR chatbot.

        Analyze the user's HR-related question and explain **what specific data** needs to be fetched from the SQL database to answer it.
        Consider the chat history for context to resolve ambiguities like pronouns
         
        
        THINK STEP BY STEP:
        1. Identify the **intent** of the question: 
            - Eligibility check, leave balance, personal info, salary details, reporting manager lookup, etc.
            
        2. **User Role & Access Rules**:
           - Role: {role}
           - Employee Code: {employee_code}
           
           Apply these rules:
           - `employee`: can access only their own data
           - `manager`: can access their own data and these **ONLY** for direct reportees:
             - leave balances, leave requests, basic employee info (name, department, designation)
             - No access to salary, contact details, personal identifiers
           - `hr_admin`: can access all employee data
           
        3. **Authorization Check**:
           - Is the user allowed to access the requested info?
           - If not, clearly state: "Unauthorized access – user is not allowed to view this data."

        4. List the **required tables and columns** (only use actual tables/columns from schema).

        5. **Filter Conditions**:
           - Self lookup → filter with employee_code = {employee_code}
           - Manager view → filter with supervisor_id = {employee_code} + role-based column restriction
           - Name-based queries → if name ≠ self, check if manager/admin or deny access

        6. Specify any **joins** needed (e.g., employee with leave_balances or manager name from employees table).


        **Important Examples** to guide your thinking:
        
          - POSITIVE EXAMPLES:
          
            - "How many sick leaves do I have?" (Employee asking for self)  
              → Use `leave_balances`, filter by `employee_code` and `leave_type`
            
            - "Who are my direct reports?" (Manager)  
              → Use `employees`, filter `supervisor_id = {employee_code}`
            
            - "What is Karan’s department and designation?" (Manager)  
              → Allowed if Karan reports to the manager
              
            ---   
            
          - NEGATIVE EXAMPLES (Reject These):

            - "Show me Neha’s salary" (Manager or Employee)  
              → Reject: Not authorized
            
            - "What is someone’s phone number or email?"  
              → Reject: Not accessible unless HR Admin
            
            - "What is the company policy on sabbaticals?"  
              → Reject: Policy questions are not in database

            - "How many employees are in marketing with DOB after 1990?" (Manager)  
              → Reject: Date of birth is not accessible to managers
        
        ---

        Use only these available tables and columns:
        {table_info}

        Chat History: {chat_history}

        Now answer:
        What data needs to be fetched to answer this question?

        Question: {question}
        """)

        reasoning_response = llm.invoke(
            reasoning_prompt.invoke({
                "question": state["question"],
                "chat_history": formatted_chat_history,  # FIX: Pass formatted_chat_history here
                "table_info": db.get_table_info(),  # Also pass table info for reasoning
                "employee_code": state["employee_code"],  # ✅ Add this
                "role": state["role"],
            })
        )
        logger.info(f"SQL Reasoning:\n{reasoning_response.content}")

        prompt = query_prompt_template.invoke(
            {
                "dialect": db.dialect,
                "top_k": 10,
                "table_info": db.get_table_info(),
                "input": f"Question: {state['question']}\n\nReasoning:\n{reasoning_response.content}",
                "chat_history": formatted_chat_history,  # FIX: Pass formatted_chat_history here
                "employee_code": state["employee_code"],
                "role": state["role"]

            }
        )
        try:
            structured_llm = llm.with_structured_output(QueryOutput)
            result = structured_llm.invoke(prompt)

            # if not validate_sql_query(result):
            #     logger.error(f"Invalid or dangerous SQL query generated: {result}")
            #     return {"error": "Generated query failed security validation", "query": ""}

            return {"sql_query": result["query"]}
        except Exception as e:
            logger.error(f"Failed to parse SQL output: {e}")
            return {"sql_query": "", "error": "SQL generation failed."}
    else:
        return {"sql_query": ""}


# Executing the SQL Query on the DB
def execute_query(state: State):
    """Execute SQL query."""
    if not state.get("sql_query"):
        logger.info("No SQL query to execute.")
        return {"sql_result": "No SQL query generated."}
    if not db:
        logger.error("Database connection not available for execution.")
        return {"sql_result": "", "error": "Database not connected. Cannot execute SQL query."}
    try:
        execute_query_tool = QuerySQLDatabaseTool(db=db)
        result = execute_query_tool.invoke(state["sql_query"])
        logger.info(f"SQL Execution Result: {result}")
        return {"sql_result": result}
    except Exception as e:
        logger.error(f"Error executing SQL query '{state['sql_query']}': {e}")
        return {"sql_result": "", "error": f"Error executing SQL query: {str(e)}"}


def handle_policy_query(state: State):
    """
    Handle policy-related queries using RAG.
    Passes chat_history to the RAG chain for better contextual retrieval/generation.
    """
    try:
        if state["query_type"] in ["POLICY", "HYBRID"]:
            if not rag_chain:
                logger.warning("RAG chain not initialized. Cannot handle policy queries.")
                return {"retrieved_docs": [], "rag_result": "", "error": "Policy RAG system not available."}

            # FIX: Use formatted_chat_history in the RAG chain invoke
            formatted_chat_history = format_chat_history_for_llm(state["chat_history"])
            # logger.info(f"Classify Query - Formatted Chat History:\n{formatted_chat_history}")

            rag_output = rag_chain.invoke({"question": state["question"], "chat_history": state["chat_history"]})
            logger.info(f"RAG Result: {rag_output.get('answer', 'No RAG answer.')}")
            return {
                "retrieved_docs": rag_output.get("context", []),
                "rag_result": rag_output.get("answer", "")
            }
        else:
            # No need to run RAG for DATABASE queries
            return {
                "retrieved_docs": [],
                "rag_result": ""
            }

    except Exception as e:
        logger.error(f"Error in handle_policy_query: {e}")
        return {
            "retrieved_docs": [],
            "rag_result": "",
            "error": f"Policy query handling failed: {str(e)}"
        }


# sql to natural language for hybrid queries
def format_sql_result(llm, question: str, sql_query: str, sql_result: str, chat_history: List[BaseMessage]) -> str:
    """
    Use the LLM to convert SQL query result into human-readable natural language for hybrid queries
    Includes chat_history for better context.
    """
    if not sql_result:
        return "No relevant employee data was found in the database."
    if not llm:
        logger.error("LLM not available for formatting SQL result.")
        return "LLM not available to format SQL result."

    # FIX: Use formatted_chat_history in the prompt
    formatted_chat_history = format_chat_history_for_llm(chat_history)

    prompt = (
        "You are Employee Self Service Bot, a helpful and professional HR assistant.\n"
        "The user has asked a question that may involve both database information and company policy.\n"
        "You are now only provided with the database SQL result — your job is to explain what this part of the data tells us in natural language.\n\n"
        "Do not attempt to fully answer the user's question yet — this is only a partial answer.\n\n"
        "Given the following chat history, user question, SQL query, and its result, explain clearly and briefly what the SQL result tells us. "
        "Only summarize the actual result — do not assume, speculate, or fabricate.\n\n"
        f"Chat History: {formatted_chat_history}\n"
        f"Question: {question}\n"
        f"SQL Query: {sql_query}\n"
        f"SQL Result: {sql_result}"
    )

    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f"Error formatting SQL result: {str(e)}"


# generating the natural langauge answer
def generate_answer(state: State):
    """Generate the final answer based on DB and/or policy RAG results, considering chat history."""
    try:
        if state.get("error"):
            return {"final_answer": f"I encountered an issue: {state['error']}. Please try rephrasing your question."}

        if not llm:
            return {"final_answer": "AI model is currently unavailable. Please try again later."}

        query_type = state["query_type"]
        # FIX: Use formatted_chat_history for the final answer generation
        formatted_chat_history = format_chat_history_for_llm(state["chat_history"])

        if query_type == "DATABASE":
            if not state.get("sql_result"):
                return {"final_answer": "No relevant employee data was found in the database."}

            prompt = (
                "You are Employee self service Bot, a helpful and professional HR assistant."
                "Given the following chat history, user question, corresponding SQL query, "
                "and SQL result, generate generate a clear and friendly brief response in natural human language."
                "Only use the data present in the SQL result — do not assume, speculate, or fabricate any information. "
                "If the SQL result is empty or invalid, politely say that no information was found.\n\n"
                f'Chat History: {formatted_chat_history}\n'
                f'Question: {state["question"]}\n'
                f'SQL Query: {state["sql_query"]}\n'
                f'SQL Result: {state["sql_result"]}'
            )


        elif query_type == "POLICY":
            if not state.get("rag_result"):
                return {"final_answer": "I couldn't find any relevant policy documents to answer your question."}

            prompt = (
                "You are Employee Self Service Bot, a helpful and professional HR assistant. "
                "Based on the following chat history and HR policy context, answer the user's question clearly and professionally.\n\n"
                f"Chat History: {formatted_chat_history}\n"
                f"Question: {state['question']}\n"
                f"Policy Info: {state['rag_result']}"
            )

        elif query_type == "HYBRID":
            if not state.get("sql_result") and not state.get("rag_result"):
                return {
                    "final_answer": "I couldn't find any relevant database or policy information to answer your question."}

                # Format SQL result into natural language for better context
            sql_natural = format_sql_result(
                llm,
                state["question"],
                state["sql_query"],
                state["sql_result"],
                state["chat_history"]

            )

            logger.info(f"Formatted SQL Result (natural language):\n{sql_natural}")

            prompt = (
                "You are Employee Self Service Bot, a helpful and professional HR assistant. "
                "Use the following chat history, database and policy information to generate a complete and brief answer. "
                "If one source is missing, acknowledge that and use the available one.\n\n"
                f"Chat History: {formatted_chat_history}\n"
                f"Question: {state['question']}\n"
                f"Database info: {sql_natural}\n"
                f"Policy Info: {state.get('rag_result', 'Not available')}"
            )

        else:
            return {"final_answer": "Unsupported query type."}

        # Generate final answer
        response = llm.invoke(prompt)
        return {"final_answer": response.content}


    except Exception as e:
        logger.error(f"Error in generate_answer: {e}")
        return {"final_answer": "Sorry, an error occurred while generating your answer. Please try again."}


# connecting all steps in a graph using Langgraph
graph_builder = StateGraph(State)

graph_builder.add_node("classify_query", classify_query)
graph_builder.add_node("write_query", write_query)
graph_builder.add_node("execute_query", execute_query)
graph_builder.add_node("handle_policy_query", handle_policy_query)
graph_builder.add_node("generate_answer", generate_answer)

graph_builder.set_entry_point("classify_query")
graph_builder.add_edge("classify_query", "write_query")
graph_builder.add_edge("write_query", "execute_query")
graph_builder.add_edge("execute_query", "handle_policy_query")
graph_builder.add_edge("handle_policy_query", "generate_answer")

graph = graph_builder.compile()


# Wrapper to integrate session-based memory into LangGraph pipeline
def get_session_history_wrapper(session_id: str) -> BaseChatMessageHistory:
    return get_session_history(session_id, app.session_histories)


# Wrap LangGraph pipeline with memory for contextual multi-turn conversations
graph_with_history = RunnableWithMessageHistory(
    graph,
    get_session_history_wrapper,  # Use the wrapper function
    input_messages_key="question",
    history_messages_key="chat_history",
    output_messages_key="final_answer"
)


@app.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """
    Main endpoint that receives user messages,
    runs LangGraph pipeline with memory,
    and returns natural language answer.
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 401

    employee_code = user["employee_code"]
    email = user["email"]
    role = user["role"]
    user_id = int(user["user_id"])

    logger.info(f"User E-code: {employee_code}")
    logger.info(f"User email: {email}")
    logger.info(f"User role: {role}")
    logger.info(f"User id: {user_id}")

    data = request.get_json()
    user_query = data.get("message")
    session_id = data.get("session_id", "default_session")

    logger.info("\n--- NEW REQUEST RECEIVED ---")
    logger.info(f"Query: {user_query}")
    logger.info(f"Session ID: {session_id}")

    if not user_query:
        return jsonify({"response": "No message provided."}), 400

    try:

        # Run memory-aware LangGraph pipeline
        ans = graph_with_history.invoke(
            {
                "question": user_query,
                "employee_code": employee_code,  # ✅ FIXED
                "role": role
            },

            config={"configurable": {"session_id": session_id}}
        )

        logger.info(f"Query Type: {ans.get('query_type')}")
        logger.info(f"SQL Query generated: {ans.get('sql_query')}")
        logger.info(f"SQL result found in DB: {ans.get('sql_result')}")
        logger.info(f"Policy RAG Result: {ans.get('rag_result')}")
        logger.info(f"Final Answer: {ans.get('final_answer')}")
        logger.info(f"Error: {ans.get('error')}")

        # Send only the final natural language answer to frontend
        return jsonify({"response": ans["final_answer"]})

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return jsonify({"response": "Sorry, something went wrong on the server. Please try again later."}), 500


auth_bp = create_auth_blueprint(db)
app.register_blueprint(auth_bp, url_prefix="/auth")

@app.route('/healthz')
def healthz():
    return "ok", 200

if __name__ == '__main__':
    # app.run(port=5000, debug=False)
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




