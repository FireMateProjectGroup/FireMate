import tensorflow as tf
import tensorflow_hub as hub
from transformers import pipeline
from PIL import Image
import numpy as np
import io
import logging

logger = logging.getLogger(__name__)

# Initialize models
try:
    # Load pre-trained image classification model from TensorFlow Hub
    IMAGE_MODEL = hub.load('https://tfhub.dev/google/imagenet/efficientnet_v2_imagenet1k_b0/classification/2')
    
    # Initialize sentiment analysis pipeline
    SENTIMENT_ANALYZER = pipeline('sentiment-analysis')
except Exception as e:
    logger.error(f"Error loading AI models: {str(e)}")
    IMAGE_MODEL = None
    SENTIMENT_ANALYZER = None

def preprocess_image(image_data):
    """
    Preprocess image for the EfficientNet model.
    """
    try:
        # Convert bytes to PIL Image if needed
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = Image.open(image_data)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to model's expected input size
        image = image.resize((224, 224))
        
        # Convert to numpy array and preprocess
        img_array = tf.keras.preprocessing.image.img_to_array(image)
        img_array = tf.expand_dims(img_array, 0)
        
        # Normalize pixel values
        img_array = tf.keras.applications.efficientnet_v2.preprocess_input(img_array)
        
        return img_array
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def analyze_image(image_data):
    """
    Analyze image to detect presence of fire/smoke and calculate confidence score.
    """
    if IMAGE_MODEL is None:
        return 0.0, "Error: Image model not loaded"

    try:
        # Preprocess image
        processed_image = preprocess_image(image_data)
        if processed_image is None:
            return 0.0, "Error: Failed to process image"

        # Get model predictions
        predictions = IMAGE_MODEL(processed_image)
        predictions = tf.nn.softmax(predictions)

        # Get the predicted class and confidence
        class_names = ['fire', 'smoke', 'emergency', 'flame']  # Relevant classes for fire detection
        confidence_scores = []
        
        # Get confidence scores for fire-related classes
        for class_name in class_names:
            # Find indices of classes that contain our target words
            indices = [i for i, label in enumerate(tf.keras.applications.efficientnet_v2.decode_predictions(predictions.numpy())[0]) 
                      if class_name in label[1].lower()]
            
            if indices:
                confidence_scores.extend([predictions[0][i].numpy() for i in indices])

        # Calculate final confidence score
        if confidence_scores:
            final_score = max(confidence_scores) * 100
        else:
            final_score = 0.0

        return final_score, "Success"
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return 0.0, f"Error: {str(e)}"

def analyze_text_sentiment(text):
    """
    Analyze text sentiment to help detect panic/urgency in the description.
    Returns a normalized score between 0 and 100.
    """
    if SENTIMENT_ANALYZER is None:
        return 0.0, "Error: Sentiment analyzer not loaded"

    try:
        # Analyze sentiment
        result = SENTIMENT_ANALYZER(text)
        
        # Convert the sentiment score to a 0-100 scale
        # Negative sentiment (panic/urgency) will result in a higher score
        if result[0]['label'] == 'NEGATIVE':
            score = result[0]['score'] * 100
        else:
            score = (1 - result[0]['score']) * 100
            
        return score, "Success"
    except Exception as e:
        logger.error(f"Error analyzing text sentiment: {str(e)}")
        return 0.0, f"Error: {str(e)}"

def calculate_incident_confidence(image_score, sentiment_score):
    """
    Calculate overall incident confidence score based on image and sentiment analysis.
    Returns a score between 0 and 100.
    """
    # Weight factors for each component
    IMAGE_WEIGHT = 0.7
    SENTIMENT_WEIGHT = 0.3
    
    # Calculate weighted average
    confidence_score = (image_score * IMAGE_WEIGHT) + (sentiment_score * SENTIMENT_WEIGHT)
    
    # Ensure the score is between 0 and 100
    return max(0, min(100, confidence_score)) 