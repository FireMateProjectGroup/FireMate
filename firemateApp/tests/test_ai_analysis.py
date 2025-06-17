import unittest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from ..models import FireIncident, IncidentMedia
from ..ai_analysis import (
    analyze_image, analyze_text_sentiment, 
    calculate_incident_confidence, preprocess_image
)
import os
import numpy as np
from PIL import Image
import io

class AIAnalysisUnitTests(TestCase):
    def setUp(self):
        # Create test image
        self.test_image = Image.new('RGB', (224, 224), color='red')
        img_byte_arr = io.BytesIO()
        self.test_image.save(img_byte_arr, format='PNG')
        self.test_image_bytes = img_byte_arr.getvalue()

    def test_preprocess_image(self):
        """Test image preprocessing function"""
        # Test with PIL Image
        processed = preprocess_image(self.test_image)
        self.assertIsNotNone(processed)
        self.assertEqual(processed.shape, (1, 224, 224, 3))

        # Test with bytes
        processed = preprocess_image(self.test_image_bytes)
        self.assertIsNotNone(processed)
        self.assertEqual(processed.shape, (1, 224, 224, 3))

        # Test with invalid input
        processed = preprocess_image(None)
        self.assertIsNone(processed)

    def test_analyze_text_sentiment(self):
        """Test sentiment analysis function"""
        # Test positive case
        score, status = analyze_text_sentiment(
            "EMERGENCY! Large fire spreading quickly in the building!"
        )
        self.assertGreater(score, 50)  # Should detect urgency
        self.assertEqual(status, "Success")

        # Test neutral case
        score, status = analyze_text_sentiment(
            "Small smoke coming from the kitchen."
        )
        self.assertIsInstance(score, float)
        self.assertEqual(status, "Success")

        # Test empty text
        score, status = analyze_text_sentiment("")
        self.assertEqual(score, 0.0)

    def test_calculate_incident_confidence(self):
        """Test confidence score calculation"""
        # Test high confidence case
        score = calculate_incident_confidence(90.0, 80.0)
        self.assertGreater(score, 80)

        # Test low confidence case
        score = calculate_incident_confidence(10.0, 20.0)
        self.assertLess(score, 20)

        # Test edge cases
        score = calculate_incident_confidence(0.0, 0.0)
        self.assertEqual(score, 0.0)
        
        score = calculate_incident_confidence(100.0, 100.0)
        self.assertEqual(score, 100.0)

class AIAnalysisIntegrationTests(TestCase):
    def setUp(self):
        # Create test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='REPORTER'
        )

        # Create test image
        self.test_image = Image.new('RGB', (224, 224), color='red')
        img_byte_arr = io.BytesIO()
        self.test_image.save(img_byte_arr, format='PNG')
        self.test_image_bytes = img_byte_arr.getvalue()

        # Create test incident
        self.incident = FireIncident.objects.create(
            reporter=self.user,
            latitude=40.7128,
            longitude=-74.0060,
            description="URGENT! Large fire in building with heavy smoke!",
            status='PENDING'
        )

        # Create test media
        self.media = IncidentMedia.objects.create(
            incident=self.incident,
            media_type='IMAGE',
            file_url=SimpleUploadedFile(
                "test_fire.png",
                self.test_image_bytes,
                content_type="image/png"
            )
        )

    def test_full_incident_analysis(self):
        """Test complete incident analysis flow"""
        from ..views import FireIncidentViewSet
        
        viewset = FireIncidentViewSet()
        viewset._analyze_incident(self.incident)

        # Refresh incident from database
        self.incident.refresh_from_db()

        # Check that scores were calculated
        self.assertIsNotNone(self.incident.ai_confidence_score)
        self.assertIsNotNone(self.incident.sentiment_score)

        # Check status update based on scores
        self.assertIn(self.incident.status, ['VERIFIED', 'REJECTED', 'PENDING'])

        # If confidence is high, should be verified
        if self.incident.ai_confidence_score >= 80:
            self.assertEqual(self.incident.status, 'VERIFIED')
        # If confidence is very low, should be rejected
        elif self.incident.ai_confidence_score < 20:
            self.assertEqual(self.incident.status, 'REJECTED')

    def tearDown(self):
        # Clean up test files
        if hasattr(self, 'media') and self.media.file_url:
            if os.path.exists(self.media.file_url.path):
                os.remove(self.media.file_url.path) 