import tensorflow as tf
from flask import Flask, request, jsonify, send_file
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences
from gtts import gTTS
import numpy as np
import pickle
import io
from io import BytesIO
import keras  # For enabling unsafe deserialization
import builtins
builtins.tf = tf
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) # This enables CORS for all routes and origins by default


# === Configuration ===
MODEL_PATH = './mymodel.keras'
TOKENIZER_PATH = './tokenizer.pkl'
MAX_CAPTION_LENGTH = 74

# Enable unsafe deserialization (for loading Lambda layers with Python lambdas)
keras.config.enable_unsafe_deserialization()

# === Load model and tokenizer with error handling ===
try:
    caption_model = load_model(MODEL_PATH)
except Exception as e:
    print(f"Error loading model: {e}")
    caption_model = None

try:
    with open(TOKENIZER_PATH, 'rb') as f:
        tokenizer = pickle.load(f)
except Exception as e:
    print(f"Error loading tokenizer: {e}")
    tokenizer = None

# Load VGG16 for feature extraction
vgg = VGG16()
vgg_model = Model(inputs=vgg.inputs, outputs=vgg.layers[-2].output)

# === Utility functions ===

def get_word_from_index(index, tokenizer):
    """Map an index back to its corresponding word in the tokenizer."""
    for word, idx in tokenizer.word_index.items():
        if idx == index:
            return word
    return None

def extract_features(image_file):
    """Extract VGG16 features from the input image file."""
    img_bytes = BytesIO(image_file.read())
    img_bytes.seek(0)
    image = load_img(img_bytes, target_size=(224, 224))
    image = img_to_array(image)
    image = image.reshape((1, *image.shape))
    image = preprocess_input(image)
    features = vgg_model.predict(image, verbose=0)
    return features

def predict_caption(model, image_features, tokenizer, max_caption_length):
    """Generate a caption for the image based on the features and tokenizer."""
    caption = "startseq"
    for _ in range(max_caption_length):
        seq = tokenizer.texts_to_sequences([caption])[0]
        seq = pad_sequences([seq], maxlen=max_caption_length, padding='post')
        yhat = model.predict([image_features, seq], verbose=0)
        index = np.argmax(yhat)
        word = get_word_from_index(index, tokenizer)
        if word is None or word == "endseq":
            break
        caption += " " + word
    return caption.replace("startseq", "").strip()

# === API Routes ===

@app.route('/generate-caption', methods=['POST'])
def generate_caption():
    if caption_model is None or tokenizer is None:
        return jsonify({'error': 'Model or tokenizer not loaded.'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'}), 400

    image_file = request.files['image']
    features = extract_features(image_file)
    caption = predict_caption(caption_model, features, tokenizer, MAX_CAPTION_LENGTH)
    return jsonify({'caption': caption})

@app.route('/speak-caption', methods=['POST'])
def speak_caption():
    data = request.get_json()
    caption = data.get('caption', '').strip()
    if not caption:
        return jsonify({'error': 'No caption provided'}), 400

    tts = gTTS(text=caption, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    return send_file(mp3_fp, mimetype='audio/mpeg', as_attachment=False, download_name='caption.mp3')

@app.route('/')
def home():
    return jsonify({"message": "Image Captioning API is running."})

# === Run the Flask app ===
if __name__ == '__main__':
    app.run(debug=True)
