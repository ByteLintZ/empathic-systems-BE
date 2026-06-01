# Empathic Systems — Backend API 🧠🤖

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-yellow?style=for-the-badge&logo=huggingface)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> **Backend Service** for the EduChat Empathic AI Platform. Designed to detect student frustration in real-time and provide adaptive, emotionally intelligent AI responses.

This repository contains the backend infrastructure powering [EduChat Live Demo](https://empathic-systems-fe.vercel.app), originally developed for research on mitigating student frustration in learning environments.

---

## 🎯 Key Features

- **Real-time Emotion Classification**: Integrates IndoBERT via Hugging Face Transformers to analyze user inputs and classify emotions (e.g., Happy, Sad, Frustrated, Angry) before response generation.
- **Blazingly Fast LLM Integration**: Powered by the [Groq API](https://groq.com/) (Llama-3.3-70b-versatile) for ultra-low latency inference.
- **Intelligent Rate Limiting**: Token/quota-based request limiting to prevent abuse and manage API loads effectively.
- **Robust Telemetry & Logging**: Structured logging system tracking latency, token usage, and AI response statistics.
- **Clean Architecture**: Highly modular, maintainable structure utilizing FastAPI best practices (routes, services, models, utils).

## 🛠️ Technology Stack

- **Framework:** FastAPI / Python 3.10+
- **LLM Engine:** Groq API
- **Machine Learning (NLP):** Hugging Face Transformers ([ZenyxS/indobert-emotion-emotionclf](https://huggingface.co/ZenyxS/indobert-emotion-emotionclf))
- **Server:** Uvicorn

---

## 🚀 Local Development Setup

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/ByteLintZ/empathic-systems-BE.git
cd empathic-systems-BE
python -m venv venv

# Activate venv (Windows):
venv\Scripts\activate
# Activate venv (Mac/Linux):
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the template environment file:
```bash
cp .env.example .env
```
Ensure you populate the GROQ_API_KEY inside .env.

### 4. Run the Server
```bash
python run.py
```
The server will start at [http://0.0.0.0:8000](http://0.0.0.0:8000) or http://localhost:7860.
Interactive API documentation (Swagger UI) is auto-generated and accessible at http://localhost:7860/docs.

---

## 🏗️ Deployment (Docker)

This project includes a production-ready Dockerfile optimized for environments like AWS, GCP, VPS, or Hugging Face Spaces.

1. **Build image:** 
   ```bash
   docker build -t empathic-systems-be .
```
2. **Run container:** 
   ```bash
   docker run -p 7860:7860 --env-file .env empathic-systems-be
```

---

## 🛡️ Best Practices & Security

- **Environment Variables**: All secrets must be kept in .env. The .gitignore is strictly configured to prevent accidental credential leaks.
- **Traffic Control**: Rate limiters are implemented in `app/services/user_limiter.py`.
- **CORS Handling**: Cross-Origin Resource Sharing is appropriately parsed from the `.env` via `FRONTEND_URL` and `EXTRA_CORS_ORIGINS`.

---

## 🔒 Data Privacy Disclaimer

This application includes a local CSV logger (in `app/utils/logger.py`) that actively records conversation histories, user prompts, and classified emotions for analytics. If you plan to deploy this system in a production environment, please ensure that you comply with relevant data privacy laws (e.g., GDPR, CCPA). You may want to anonymize personal data, add a privacy policy to your frontend, or disable/modify the local CSV logger depending on your use case.

---

## 📄 License
[MIT License](LICENSE)
