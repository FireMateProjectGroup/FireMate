from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from ..models import FireIncident, IncidentMedia
from ..ai_analysis import analyze_image, analyze_text_sentiment
import os
import requests
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class RealWorldTestCases(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test user
        User = get_user_model()
        cls.user = User.objects.create_user(
            username='realworldtester',
            password='testpass123',
            role='REPORTER'
        )
        
        # Test cases with real emergency descriptions
        cls.test_descriptions = [
            "EMERGENCY! Large fire in apartment building, flames visible from 3rd floor, heavy smoke!",
            "Seeing some smoke from neighbor's barbecue, might be nothing but wanted to report.",
            "HELP! Factory on fire, multiple explosions heard, black smoke everywhere!",
            "Small kitchen fire, contained in trash can, already extinguished.",
            "Massive forest fire spreading rapidly, multiple trees ablaze, urgent response needed!"
        ]
        
        # URLs to test images (replace with your actual test image URLs)
        cls.test_image_urls = [
            "https://example.com/test_images/large_building_fire.jpg",
            "https://example.com/test_images/bbq_smoke.jpg",
            "https://example.com/test_images/factory_fire.jpg",
            "https://example.com/test_images/small_kitchen_fire.jpg",
            "https://example.com/test_images/forest_fire.jpg"
        ]

    def setUp(self):
        self.incidents = []
        self.test_images = []

        # Download and prepare test images
        for i, url in enumerate(self.test_image_urls):
            try:
                # In a real test, you would download the image from the URL
                # For this example, we'll create a dummy image
                test_image = Image.new('RGB', (224, 224), color=('red' if i % 2 == 0 else 'gray'))
                img_byte_arr = io.BytesIO()
                test_image.save(img_byte_arr, format='PNG')
                self.test_images.append(img_byte_arr.getvalue())
            except Exception as e:
                logger.error(f"Error preparing test image {i}: {str(e)}")
                self.test_images.append(None)

    def test_real_world_scenarios(self):
        """Test AI analysis with real-world scenarios"""
        
        for i in range(len(self.test_descriptions)):
            # Create incident
            incident = FireIncident.objects.create(
                reporter=self.user,
                latitude=40.7128,
                longitude=-74.0060,
                description=self.test_descriptions[i],
                status='PENDING'
            )
            
            # Add test image if available
            if self.test_images[i]:
                media = IncidentMedia.objects.create(
                    incident=incident,
                    media_type='IMAGE',
                    file_url=SimpleUploadedFile(
                        f"test_fire_{i}.png",
                        self.test_images[i],
                        content_type="image/png"
                    )
                )
            
            # Analyze text
            sentiment_score, sentiment_status = analyze_text_sentiment(incident.description)
            self.assertEqual(sentiment_status, "Success")
            
            # For emergency descriptions, expect higher sentiment scores
            if "EMERGENCY" in incident.description or "HELP" in incident.description:
                self.assertGreater(sentiment_score, 50)
            
            # For non-emergency descriptions, expect lower sentiment scores
            if "might be nothing" in incident.description or "already extinguished" in incident.description:
                self.assertLess(sentiment_score, 50)
            
            # If we have an image, test image analysis
            if self.test_images[i]:
                image_score, image_status = analyze_image(media.file_url)
                self.assertEqual(image_status, "Success")
                
                # Store incident for cleanup
                self.incidents.append(incident)

    def test_edge_cases(self):
        """Test edge cases and potential system gaming"""
        
        # Test with very short description
        incident = FireIncident.objects.create(
            reporter=self.user,
            latitude=40.7128,
            longitude=-74.0060,
            description="fire",
            status='PENDING'
        )
        
        score, status = analyze_text_sentiment(incident.description)
        self.assertEqual(status, "Success")
        self.assertIsInstance(score, float)
        
        # Test with very long description
        long_description = "fire " * 1000
        incident = FireIncident.objects.create(
            reporter=self.user,
            latitude=40.7128,
            longitude=-74.0060,
            description=long_description,
            status='PENDING'
        )
        
        score, status = analyze_text_sentiment(incident.description)
        self.assertEqual(status, "Success")
        self.assertIsInstance(score, float)
        
        # Test with special characters
        incident = FireIncident.objects.create(
            reporter=self.user,
            latitude=40.7128,
            longitude=-74.0060,
            description="🔥 FIRE!!! #emergency @station",
            status='PENDING'
        )
        
        score, status = analyze_text_sentiment(incident.description)
        self.assertEqual(status, "Success")
        self.assertIsInstance(score, float)

    def tearDown(self):
        # Clean up test files
        for incident in self.incidents:
            for media in incident.media.all():
                if media.file_url and os.path.exists(media.file_url.path):
                    os.remove(media.file_url.path) 