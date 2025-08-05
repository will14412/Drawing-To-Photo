"""
Run the FastAPI app by typing `python run.py`

Exactly the same as `uvicorn app.main:app --reload`,
but convenient for folks used to Flask's “just run app.py”.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)