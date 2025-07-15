# Anga View Backend

This is the FastAPI backend for the Anga View web application.

## 📦 Setup Instructions

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn python-dotenv pydantic azure-storage-blob
```

---

### 3. Run the development server

```bash
uvicorn main:app --reload

```
---

## 🔐 Environment Variables

Create a .env file and define:
```bash
AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
```
---

## 📁 Endpoints (In Progress)

GET /users/{user_id}/profile — returns mock user profile data

GET /users/{user_id}/farms — returns mock farm list

POST /upload — (soon) receives image files and uploads them to Azure Blob Storage


---
