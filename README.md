# Heart Health Assistant (Backend)

AI assistant for elderly people: reads heart-related reports, flags risky values, predicts
heart-disease risk with a locally trained model, and gives diet and lifestyle guidance by voice.
Everything runs locally and is free and open source.

## Features
- Report upload (PDF or photo) with OCR, or values by form or voice
- Normal-range flags and a heart-disease risk score with reasons
- Personal diet and lifestyle plan from a local LLM (Ollama), with a safe fallback
- Voice input (Whisper, offline), reminders, daily tasks, emergency SOS

## Tech stack
FastAPI, SQLite, SQLAlchemy, scikit-learn, XGBoost, PyMuPDF, Tesseract, faster-whisper, Ollama (qwen2.5)

## Setup
1. Install Python, Ollama and Tesseract
2. python -m venv venv, then venv\Scripts\activate
3. python -m pip install -r requirements.txt
4. Copy .env.example to .env and fill it in
5. ollama pull qwen2.5:3b

## Train the model
python -m ml.train_risk_model

## Run
python -m uvicorn app.main:app --reload, then open http://localhost:8000/docs

## Results
| Model | CV ROC-AUC | Test accuracy | Recall | ROC-AUC |
|---|---|---|---|---|
| Logistic regression | ... | ... | ... | ... |
| Random forest | ... | ... | ... | ... |
| XGBoost | ... | ... | ... | ... |

Report extraction accuracy: PDF ...%, photo (OCR) ...%
Tests: 11 passed

## Data sources
- Heart Failure Prediction dataset (fedesoriano, Kaggle)
- Diet guidance written from WHO, American Heart Association and ICMR-NIN guidelines

## Disclaimer
This project gives general guidance and is not a medical diagnosis.
Users should always consult a doctor before changing medicines, diet or exercise.