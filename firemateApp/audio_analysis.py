from google.cloud import speech
from pydub import AudioSegment
import soundfile as sf
import io
import os
import logging
from .ai_analysis import analyze_text_sentiment
import librosa
import numpy as np
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

def convert_audio_to_wav(audio_data, source_format):
    """
    Convert audio data to WAV format required by Google Speech-to-Text.
    Supports common formats like MP3, M4A, OGG, etc.
    """
    try:
        # Load audio from bytes
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)
        
        # Convert to WAV
        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        
        return wav_io.getvalue()
    except Exception as e:
        logger.error(f"Error converting audio to WAV: {str(e)}")
        return None

def transcribe_audio(audio_data, source_format='mp3', language_code='en-US'):
    """
    Transcribe audio to text using Google Cloud Speech-to-Text.
    
    Args:
        audio_data (bytes): Raw audio data
        source_format (str): Source audio format (e.g., 'mp3', 'm4a', 'ogg')
        language_code (str): Language code for transcription
    
    Returns:
        tuple: (transcription text, status message)
    """
    try:
        # Convert audio to WAV if it's not already
        if source_format.lower() != 'wav':
            audio_data = convert_audio_to_wav(audio_data, source_format)
            if audio_data is None:
                return None, "Error converting audio format"

        # Create speech client
        client = speech.SpeechClient()

        # Create recognition audio object
        audio = speech.RecognitionAudio(content=audio_data)

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=language_code,
            enable_automatic_punctuation=True,
            model='default',  # Use 'phone_call' for low-quality audio
            use_enhanced=True,  # Better model for emergency-related content
        )

        # Perform transcription
        response = client.recognize(config=config, audio=audio)

        # Combine all transcriptions
        transcription = ' '.join(
            result.alternatives[0].transcript
            for result in response.results
        )

        return transcription, "Success"
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return None, f"Error: {str(e)}"

def analyze_voice_note(audio_data, source_format='mp3', language_code='en-US'):
    """
    Analyze voice note for sentiment by first converting speech to text.
    
    Args:
        audio_data (bytes): Raw audio data
        source_format (str): Source audio format
        language_code (str): Language code for transcription
    
    Returns:
        tuple: (sentiment score, transcription, status message)
    """
    try:
        # First transcribe the audio
        transcription, status = transcribe_audio(
            audio_data, 
            source_format=source_format,
            language_code=language_code
        )
        
        if transcription is None or 'Error' in status:
            return 0.0, None, status
            
        # Then analyze the transcribed text
        sentiment_score, sentiment_status = analyze_text_sentiment(transcription)
        
        if 'Error' in sentiment_status:
            return 0.0, transcription, sentiment_status
            
        return sentiment_score, transcription, "Success"
        
    except Exception as e:
        logger.error(f"Error analyzing voice note: {str(e)}")
        return 0.0, None, f"Error: {str(e)}"

class VoiceStressAnalyzer:
    def __init__(self):
        # Initialize scaler for feature normalization
        self.scaler = MinMaxScaler()
        
        # Define stress indicators thresholds
        self.thresholds = {
            'pitch_variation': 0.6,  # High pitch variation indicates stress
            'energy_threshold': 0.7,  # High energy indicates urgency
            'speech_rate': 0.65,     # Fast speech rate indicates urgency
            'jitter': 0.5,           # Voice irregularity threshold
            'shimmer': 0.5,          # Amplitude variation threshold
        }

    def convert_audio_to_wav(self, audio_data, source_format):
        """
        Convert audio data to WAV format for analysis.
        """
        try:
            # Load audio from bytes
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)
            
            # Convert to WAV
            wav_io = io.BytesIO()
            audio.export(wav_io, format='wav')
            
            return wav_io.getvalue()
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {str(e)}")
            return None

    def extract_audio_features(self, y, sr):
        """
        Extract relevant acoustic features for stress analysis.
        """
        try:
            features = {}
            
            # 1. Pitch (fundamental frequency) features
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitches_nonzero = pitches[pitches > 0]
            features['pitch_mean'] = np.mean(pitches_nonzero) if len(pitches_nonzero) > 0 else 0
            features['pitch_std'] = np.std(pitches_nonzero) if len(pitches_nonzero) > 0 else 0
            
            # 2. Energy features
            features['energy'] = np.mean(librosa.feature.rms(y=y)[0])
            features['energy_variance'] = np.std(librosa.feature.rms(y=y)[0])
            
            # 3. Speech rate estimation using zero crossing rate
            zero_crossings = librosa.zero_crossings(y)
            features['speech_rate'] = sum(zero_crossings)
            
            # 4. Voice quality features
            # Jitter (variation in pitch)
            if len(pitches_nonzero) > 1:
                features['jitter'] = np.mean(np.abs(np.diff(pitches_nonzero)))
            else:
                features['jitter'] = 0
                
            # Shimmer (variation in amplitude)
            mfccs = librosa.feature.mfcc(y=y, sr=sr)
            features['shimmer'] = np.mean(np.abs(np.diff(mfccs[0])))
            
            # 5. Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid'] = np.mean(spectral_centroids)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {str(e)}")
            return None

    def calculate_stress_score(self, features):
        """
        Calculate stress/urgency score based on extracted features.
        Returns a score between 0 and 100.
        """
        try:
            scores = []
            
            # 1. Pitch variation score
            pitch_variation = min(features['pitch_std'] / features['pitch_mean'] if features['pitch_mean'] > 0 else 0, 1)
            scores.append(pitch_variation if pitch_variation > self.thresholds['pitch_variation'] else 0)
            
            # 2. Energy level score
            energy_score = min(features['energy'] * 100, 1)
            scores.append(energy_score if energy_score > self.thresholds['energy_threshold'] else 0)
            
            # 3. Speech rate score
            speech_rate_normalized = min(features['speech_rate'] / 1000, 1)  # Normalize by expected maximum
            scores.append(speech_rate_normalized if speech_rate_normalized > self.thresholds['speech_rate'] else 0)
            
            # 4. Voice quality scores
            jitter_score = min(features['jitter'] * 10, 1)  # Normalize jitter
            scores.append(jitter_score if jitter_score > self.thresholds['jitter'] else 0)
            
            shimmer_score = min(features['shimmer'] * 10, 1)  # Normalize shimmer
            scores.append(shimmer_score if shimmer_score > self.thresholds['shimmer'] else 0)
            
            # Calculate weighted average
            weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Weights for each feature
            final_score = sum(score * weight for score, weight in zip(scores, weights))
            
            # Convert to 0-100 scale
            return final_score * 100
            
        except Exception as e:
            logger.error(f"Error calculating stress score: {str(e)}")
            return 0

    def analyze_voice_stress(self, audio_data, source_format='mp3'):
        """
        Analyze voice recording for stress and urgency indicators.
        
        Args:
            audio_data (bytes): Raw audio data
            source_format (str): Source audio format (e.g., 'mp3', 'm4a', 'ogg')
        
        Returns:
            tuple: (stress_score, analysis_details, status)
        """
        try:
            # Convert audio to WAV if needed
            if source_format.lower() != 'wav':
                audio_data = self.convert_audio_to_wav(audio_data, source_format)
                if audio_data is None:
                    return 0.0, None, "Error converting audio format"

            # Load audio file
            y, sr = librosa.load(io.BytesIO(audio_data), sr=None)
            
            # Extract features
            features = self.extract_audio_features(y, sr)
            if features is None:
                return 0.0, None, "Error extracting audio features"
            
            # Calculate stress score
            stress_score = self.calculate_stress_score(features)
            
            # Prepare analysis details
            analysis_details = {
                'pitch_variation': features['pitch_std'] / features['pitch_mean'] if features['pitch_mean'] > 0 else 0,
                'energy_level': features['energy'],
                'speech_rate': features['speech_rate'],
                'voice_quality': {
                    'jitter': features['jitter'],
                    'shimmer': features['shimmer']
                }
            }
            
            return stress_score, analysis_details, "Success"
            
        except Exception as e:
            logger.error(f"Error analyzing voice stress: {str(e)}")
            return 0.0, None, f"Error: {str(e)}" 