Intelligent Stroke Severity Clinical Decision Support System
==================================================

### 1. Overview

This project implements an end-to-end Clinical Decision Support System (CDSS)
for predicting stroke severity levels using patient clinical data. The system
exposes RESTful APIs via FastAPI, performs machine learning inference, and
persists prediction history in a MySQL database.

### 2. Tech Stack

- **Backend**: FastAPI
- **ML**: Scikit-learn (Decision Tree, Gradient Boosting)
- **Database**: PostgreSQL (via SQLAlchemy + psycopg2)
- **Model persistence**: Joblib
- **Testing**: Pytest
- **Containerization**: Docker (optional)

### 3. Project Structure

```text
Stroke-severity-prediction/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   └── schemas.py
├── model/
│   └── README.md
├── tests/
│   └── test_api.py
├── requirements.txt
└── README.md
```

You will later add:

- `decision_tree.joblib` and `gradient_boosting.joblib` under `model/`
- Notebooks for preprocessing and model training if desired

If the `.joblib` files are missing, the API automatically falls back to a
simple rule-based model so that `/predict` continues to work.

### 4. PostgreSQL Setup

Create a database and table in PostgreSQL:

```sql
CREATE DATABASE stroke_cds;

\c stroke_cds;

CREATE TABLE predictions (
  id SERIAL PRIMARY KEY,
  age DOUBLE PRECISION NOT NULL,
  bmi DOUBLE PRECISION NOT NULL,
  avg_glucose_level DOUBLE PRECISION NOT NULL,
  hypertension SMALLINT NOT NULL,
  heart_disease SMALLINT NOT NULL,
  severity VARCHAR(32) NOT NULL,
  model VARCHAR(64) NOT NULL,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Environment variables (optional, with defaults in code):

- `POSTGRES_USER` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: `password`)
- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_DB` (default: `stroke_cds`)

### 5. Setup & Run (Local)

Create and activate a virtual environment:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. API Endpoints

- **GET `/health`**
  - Returns API and model status.

- **POST `/predict`**
  - Request body (JSON):

    ```json
    {
      "age": 70,
      "bmi": 33.2,
      "avg_glucose_level": 165,
      "hypertension": 1,
      "heart_disease": 1
    }
    ```

  - Example response:

    ```json
    {
      "prediction_id": 1,
      "severity": "moderate",
      "model": "gradient_boosting",
      "probabilities": {
        "mild": 0.10,
        "moderate": 0.70,
        "severe": 0.20
      }
    }
    ```

- **GET `/predictions`**
  - Query params: `limit` (default 50), `offset` (default 0).
  - Returns a paginated list of previous predictions.

- **GET `/predictions/{prediction_id}`**
  - Returns details of a single stored prediction.

### 7. Testing

Run all tests:

```bash
pytest
```
