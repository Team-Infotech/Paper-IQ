
# PaperIQ — AI-Powered Research Insight Analyzer (Full Version)

This package contains a runnable prototype of PaperIQ with a **FastAPI** backend and a **Streamlit** frontend.

## Contents
- `backend/main.py` - FastAPI app exposing `/analyze` endpoint.
- `frontend/streamlit_app.py` - Streamlit UI that calls the API.
- `dataset_preprocessing.py` - Helper script to preprocess ASAP and PERSUADE datasets (scaffold).
- `feature_extraction_notebook.ipynb` - Notebook showing how to extract features and embeddings.
- `requirements.txt` - Python dependencies.

## How to run (local)
1. Create and activate a Python environment (recommended).
2. Install dependencies: `pip install -r requirements.txt`.
3. Run the backend:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```
4. Run the frontend in a new terminal:
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```
5. In the Streamlit app, paste text and press **Analyze** to call the backend and see results.

## Dataset notes
- This repo does **not** include copyrighted datasets. Please download ASAP-AES and PERSUADE datasets manually (links below) and place them under `data/asap` and `data/persuade` respectively:
  - ASAP-AES: https://www.kaggle.com/c/asap-aes/data
  - PERSUADE: https://www.the-learning-agency-lab.com/learning-exchange/persuade-dataset/
- Use `python dataset_preprocessing.py --asap data/asap --persuade data/persuade --out data/combined_clean.csv` to generate cleaned CSVs.

## Notes & next steps
- The scoring functions used here are **heuristic placeholders**. Replace them with a trained ML model for production.
- Consider adding authentication, logging, and secure storage for any uploaded texts.
- For deployment, use Docker + a managed service (Heroku, AWS, GCP) and secure the API endpoint.

