FROM python:3.12-slim
WORKDIR /app

# Pinned; scikit-learn must match the version that produced model.pkl (1.7.0)
RUN pip install --no-cache-dir flask==3.1.1 gunicorn==23.0.0 scikit-learn==1.7.0 joblib==1.5.1 numpy==2.2.6

# Copy model files
COPY model/ ./model/

# Copy the Flask app
COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
