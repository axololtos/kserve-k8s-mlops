from flask import Flask, request, jsonify
import os

import joblib
import numpy as np

app = Flask(__name__)

# Load the model
try:
    model = joblib.load("./model/model.pkl")
    print(f"Model loaded successfully. Type: {type(model)}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.route("/predict", methods=["POST"])
def predict():
    try:
        if model is None:
            return {"error": "Model not loaded"}, 500
            
        data = request.get_json()
        if not data:
            return {"error": "Missing request body"}, 400
        
        # Handle both text and features input
        if "text" in data:
            # Text classification model
            text_input = data["text"]
            if isinstance(text_input, list):
                prediction = model.predict(text_input)
            else:
                prediction = model.predict([text_input])
        elif "features" in data:
            # Try numerical features first
            try:
                features = np.array(data["features"], dtype=np.float64).reshape(1, -1)
                prediction = model.predict(features)
            except (ValueError, TypeError):
                # If numerical fails, try as text
                features = data["features"]
                if isinstance(features, list) and len(features) > 0:
                    # Convert to text if it's a list of strings
                    if isinstance(features[0], str):
                        prediction = model.predict(features)
                    else:
                        # Convert numbers to text
                        text_features = [str(f) for f in features]
                        prediction = model.predict([" ".join(text_features)])
                else:
                    prediction = model.predict([str(features)])
        else:
            return {"error": "Missing 'text' or 'features' in request body"}, 400
        
        # Handle different prediction output types
        if hasattr(prediction, 'tolist'):
            result = prediction.tolist()
        elif hasattr(prediction, 'item'):
            result = prediction.item()
        else:
            result = str(prediction)
        
        return {"prediction": result}
    except Exception as e:
        app.logger.exception("prediction failed")
        return {"error": str(e)}, 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=os.environ.get("FLASK_DEBUG") == "1")
