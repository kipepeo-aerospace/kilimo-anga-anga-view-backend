# Anga View Backend

This is the FastAPI backend for the Anga View web application.

## 📦 Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt

```

### 2. Run the development server

```bash
uvicorn main:app --reload

```
---

## 📦 Docker Build & Run

### Build Image

```bash
docker build -t angaview-backend .
```

### Run Container

```bash
docker run --env-file .env -p 8000:8000 angaview-backend
```


## 📁 Project Structure
backend/
├── main.py
├── routes/
│ ├── farms.py
│ ├── gallery.py
│ ├── profile.py
│ └── upload.py
├── helpers/
│ ├── __init__.py
│ └── container_launcher.py
│ └── image_conversion.py
├── requirements.txt
├── DokcerFile
├── README.md (this document)
├── .env.example - to give an idea of what needs to be used
├── .dockerignore
└── .gitignire

## 📁 Endpoints

- farms.py
  - `GET /users/{user_id}/farms` (`get_user_farms`)

- profile.py
  - `GET /users/{user_id}/profile` (`get_user_profile`)

- upload.py
  - `POST /upload` (`upload_image`)

- gallery.py
  - `GET /users/{client_id}/gallery` (`list_user_images`)

- process.py
  - `POST /process` (`start_processing_job`)
  - `GET /status` (`get_job_status`)

---

## 🧠 Notes

Image processing is offloaded to Azure Container Apps via start_processing_container(...).

Blob operations use Azure SDK (azure-storage-blob).

The frontend must supply correct clientId, farmId, and selected vegetation index in API calls.

---

## 🚀 Deployment
Deployment instructions (containerization, pushing to ACR, deploying to Azure Container Apps) to be added.

---

## ✍️ Maintained By
Kilimo Anga, an initiative by Kipepeo Aersoapce 