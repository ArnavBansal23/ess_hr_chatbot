# 🧠 ESS HR Chatbot
> An intelligent Employee Self-Service chatbot built with **Flask**, **React**, **LangChain**, **FAISS**, and **LLMs**. Handles HR policy Q&A, employee data queries, and secure user sessions all via a chat interface.

---

## 🚀 Features:

- 🔐 **User Authentication:** JWT-based login/signup with role-based access (Employee, Manager, HR Admin)
- 🧠 **RAG (Retrieval-Augmented Generation):** Answers HR policy questions using LangChain, FAISS, and LLMs
- 📋 **Employee Data Management:** MySQL-backed leave, salary, and info queries
- 💬 **Modern Chat UI:** React frontend with themes and responsive layout
- 🧠 **Session-based Memory:** Multi-turn memory per user session
- ⚙️ **Environment Variables:** `.env`-based config for backend and frontend

---

## 📁 Project Structure
<pre>
ess-hr-chatbot/
│
├── backend/                        # All backend (Flask) code
│   ├── flask_server_a.py           # Main Flask app (API, chat, RAG)
│   ├── auth.py                     # Auth logic (JWT, password hashing, roles)
│   ├── auth_routes.py              # Auth endpoints (login, signup, etc.)
│   ├── db.py                       # Database connection/init logic
│   ├── config.py                   # Configuration (loads .env)
│   ├── rag_graph2.py               # RAG (Retrieval-Augmented Generation) logic
│   ├── rag_index.py                # Script to build FAISS vector store
│   ├── mem_store.py                # In-memory chat/session storage
│   ├── synthetic_hr_policy         # HR Policy Document for RAG
│   └── ... (other backend files)
│
├── frontend/                       # All frontend (React) code
│   ├── src/                        # React components, pages, assets
│   ├── public/                     # Static files (index.html, favicon, etc.)
│   ├── package.json                # React dependencies and scripts
│   ├── .env                        # Frontend environment variables (not committed)
│   └── ... (other frontend files)
│
├── requirements.txt                # Python dependencies for backend
├── README.md                       # Project documentation (this file)
├── .gitignore                      # Git ignore rules (root)
├── .env                            # Environment variables for backend (not committed)  
│
├── synthetic_hr_policy/            # FAISS index files for RAG (ignored in git)
├── .venv/                          # Python virtual environment (ignored in git)
├── .idea/                          # PyCharm project files (ignored in git)
├── .chainlit/                      # Chainlit cache/logs (ignored in git)
├── .files/                         # Miscellaneous or generated files (ignored in git)
├── folder/                         # (Legacy/experimental scripts or data)
└── streamlit_app/                  # (Legacy Streamlit UI, not used in production)
</pre>



## 🛠️ Setup Instructions

### 1. **Clone the Repository**
```bash
git clone https://github.com/your-username/ess-hr-chatbot.git
cd ess-hr-chatbot
```

### 2. **Backend Setup**
```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate  # On Windows: ../.venv/Scripts/activate
pip install -r ../requirements.txt
```
- **Create a `.env` file in the project root:**
  ```
  SECRET_KEY=your-secret-key
  JWT_SECRET_KEY=your-jwt-secret
  MYSQL_USER=your-db-user
  MYSQL_PASSWORD=your-db-password
  MYSQL_HOST=your-db-host
  MYSQL_PORT=3306
  MYSQL_DB_NAME=your-db-name
  GROQ_API_KEY=your-groq-key
  ```

- **Run the backend:**
  ```bash
  python flask_server_a.py
  ```

### 3. **Frontend Setup**
```bash
cd ../frontend
npm install
```
- **Create a `.env` file in the `frontend/` folder:**
  ```
  REACT_APP_API_BASE_URL= "Your backend URL"
  ```

- **Run the frontend:**
  ```bash
  npm start
  ```

---

## 🌐 Deployment

- **Backend:** Deploy Flask app using Gunicorn, Render, Heroku, or PythonAnywhere. Set all environment variables in your deployment platform.
- **Frontend:** Deploy React app to Vercel, Netlify, or Render. Set `REACT_APP_API_BASE_URL` to your backend’s public URL.
- **Database:** Use a managed MySQL service or set up your own.

---

## ⚙️ Environment Variables

**Backend (`.env` in project root):**

- `SECRET_KEY=...`
- `JWT_SECRET_KEY=...`
- `MYSQL_USER=...`
- `MYSQL_PASSWORD=...`
- `MYSQL_HOST=...`
- `MYSQL_PORT=3306`
- `MYSQL_DB_NAME=...`
- `GROQ_API_KEY=...`


**Frontend (`frontend/.env`):**
- `REACT_APP_API_BASE_URL=https://your-backend-url.com`



---

## 🛡️ Security & Best Practices

- **Secrets:** All secrets are loaded from `.env` files and never committed.
- **CORS:** Configured for cross-origin requests.
- **Input Validation:** Passwords and emails validated on both frontend and backend.
- **Session Management:** Chat memory is per-session (in-memory, can be upgraded to Redis).
- **.gitignore:** Properly ignores virtual environments, node_modules, data/index folders, and secrets.

---

## 🧩 Key Technologies

- **Backend:** Flask, Flask-JWT-Extended, Flask-Limiter, Flask-CORS, LangChain, FAISS, MySQL, python-dotenv
- **Frontend:** React, Material UI, Axios, environment variables
- **RAG:** LangChain, HuggingFace Embeddings, FAISS vector store
- **Other:** Gunicorn (for production), dotenv, logging

---

## 📄 License

[MIT](LICENSE)

---

## 🙏 Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [React](https://react.dev/)
- [LangChain](https://www.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Material UI](https://mui.com/)

---

