"""
Comprehensive Test Suite for ROI Calculator
"""
import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main_secure import create_secure_app
from src.models.roi_submission import ROISubmission, db
from src.utils.lead_scoring import calculate_lead_score, assign_tier
from src.utils.validation import validate_roi_submission
from src.services.email_service_compliant import EmailServiceCompliant
from src.services.hubspot_service_enhanced import HubSpotServiceEnhanced

class ROICalculatorTestCase(unittest.TestCase):
    """Base test case for ROI Calculator"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_secure_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

class TestROICalculation(ROICalculatorTestCase):
    """Test ROI calculation functionality"""
    
    def test_basic_roi_calculation(self):
        """Test basic ROI calculation endpoint"""
        data = {
            'monthly_revenue': 50000
        }
        
        response = self.client.post('/api/roi-calculator/calculate',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        
        self.assertTrue(result['success'])
        self.assertIn('projections', result)
        self.assertIn('conservative', result['projections'])
        self.assertIn('expected', result['projections'])
        self.assertIn('optimistic', result['projections'])
        
        # Verify calculation accuracy
        conservative = result['projections']['conservative']
        self.assertEqual(conservative['monthly_revenue'], 55000)  # 50000 * 1.10
        self.assertEqual(conservative['monthly_increase'], 5000)   # 50000 * 0.10
        self.assertEqual(conservative['annual_benefit'], 60000)    # 5000 * 12
    
    def test_invalid_revenue_calculation(self):
        """Test calculation with invalid revenue"""
        data = {
            'monthly_revenue': -1000
        }
        
        response = self.client.post('/api/roi-calculator/calculate',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertIn('error', result)
    
    def test_missing_revenue_calculation(self):
        """Test calculation without revenue"""
        data = {}
        
        response = self.client.post('/api/roi-calculator/calculate',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertIn('error', result)

class TestLeadScoring(ROICalculatorTestCase):
    """Test lead scoring algorithm"""
    
    def test_high_score_lead(self):
        """Test high-scoring lead"""
        data = {
            'monthly_revenue': 100000,
            'industry': 'E-commerce',
            'business_stage': 'Growth',
            'conversion_rate': 2.5,
            'cart_abandonment_rate': 70,
            'manual_hours_per_week': 20,
            'monthly_ad_spend': 10000
        }
        
        score = calculate_lead_score(data)
        tier = assign_tier(score)
        
        self.assertGreaterEqual(score, 100)
        self.assertEqual(tier, 'Hot')
    
    def test_medium_score_lead(self):
        """Test medium-scoring lead"""
        data = {
            'monthly_revenue': 25000,
            'industry': 'Fashion',
            'business_stage': 'Established',
            'conversion_rate': 1.5,
            'cart_abandonment_rate': 65,
            'manual_hours_per_week': 10,
            'monthly_ad_spend': 2000
        }
        
        score = calculate_lead_score(data)
        tier = assign_tier(score)
        
        self.assertGreaterEqual(score, 60)
        self.assertLess(score, 100)
        self.assertEqual(tier, 'Warm')
    
    def test_low_score_lead(self):
        """Test low-scoring lead"""
        data = {
            'monthly_revenue': 5000,
            'industry': 'Other',
            'business_stage': 'Startup',
            'conversion_rate': 0.5,
            'cart_abandonment_rate': 50,
            'manual_hours_per_week': 5,
            'monthly_ad_spend': 100
        }
        
        score = calculate_lead_score(data)
        tier = assign_tier(score)
        
        self.assertLess(score, 60)
        self.assertEqual(tier, 'Cold')

class TestFormValidation(ROICalculatorTestCase):
    """Test form validation"""
    
    def test_valid_form_data(self):
        """Test validation with valid form data"""
        data = {
            'monthly_revenue': 50000,
            'average_order_value': 75,
            'monthly_orders': 667,
            'industry': 'E-commerce',
            'conversion_rate': 2.0,
            'cart_abandonment_rate': 65,
            'manual_hours_per_week': 15,
            'business_stage': 'Growth',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'business_name': 'Test Business'
        }
        
        result = validate_roi_submission(data)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_invalid_email_validation(self):
        """Test validation with invalid email"""
        data = {
            'monthly_revenue': 50000,
            'average_order_value': 75,
            'monthly_orders': 667,
            'industry': 'E-commerce',
            'conversion_rate': 2.0,
            'cart_abandonment_rate': 65,
            'manual_hours_per_week': 15,
            'business_stage': 'Growth',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'business_name': 'Test Business'
        }
        
        result = validate_roi_submission(data)
        self.assertFalse(result['valid'])
        self.assertIn('email', result['errors'])
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        data = {
            'monthly_revenue': 50000,
            # Missing other required fields
        }
        
        result = validate_roi_submission(data)
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)

class TestFormSubmission(ROICalculatorTestCase):
    """Test form submission workflow"""
    
    @patch('src.services.email_service_compliant.EmailServiceCompliant.send_confirmation_email')
    @patch('src.services.email_service_compliant.EmailServiceCompliant.send_internal_notification')
    @patch('src.services.hubspot_service_enhanced.HubSpotServiceEnhanced.upsert_contact')
    @patch('src.services.hubspot_service_enhanced.HubSpotServiceEnhanced.create_deal')
    def test_successful_submission(self, mock_create_deal, mock_upsert_contact, 
                                 mock_internal_email, mock_confirmation_email):
        """Test successful form submission"""
        # Mock successful responses
        mock_confirmation_email.return_value = {'success': True}
        mock_internal_email.return_value = {'success': True}
        mock_upsert_contact.return_value = {'success': True, 'contact_id': '12345'}
        mock_create_deal.return_value = {'success': True, 'deal_id': '67890'}
        
        data = {
            'monthly_revenue': 50000,
            'average_order_value': 75,
            'monthly_orders': 667,
            'industry': 'E-commerce',
            'conversion_rate': 2.0,
            'cart_abandonment_rate': 65,
            'manual_hours_per_week': 15,
            'business_stage': 'Growth',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'business_name': 'Test Business',
            'website': 'https://testbusiness.com',
            'phone': '+1234567890'
        }
        
        response = self.client.post('/api/roi-calculator/submit',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        
        self.assertTrue(result['success'])
        self.assertIn('submission_id', result)
        self.assertIn('lead_score', result)
        self.assertIn('tier', result)
        
        # Verify database record was created
        with self.app.app_context():
            submission = ROISubmission.query.filter_by(
                submission_id=result['submission_id']
            ).first()
            self.assertIsNotNone(submission)
            self.assertEqual(submission.monthly_revenue, 50000)
    
    def test_submission_with_invalid_data(self):
        """Test submission with invalid data"""
        data = {
            'monthly_revenue': 'invalid',
            'email': 'invalid-email'
        }
        
        response = self.client.post('/api/roi-calculator/submit',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertIn('error', result)

class TestEmailService(ROICalculatorTestCase):
    """Test email service functionality"""
    
    @patch('sendgrid.SendGridAPIClient.send')
    def test_confirmation_email_creation(self, mock_send):
        """Test confirmation email creation"""
        mock_send.return_value = MagicMock(status_code=202)
        
        # Create test submission
        with self.app.app_context():
            submission = ROISubmission(
                monthly_revenue=50000,
                average_order_value=75,
                monthly_orders=667,
                industry='E-commerce',
                conversion_rate=2.0,
                cart_abandonment_rate=65,
                manual_hours_per_week=15,
                business_stage='Growth',
                first_name='John',
                last_name='Doe',
                email='john@example.com',
                business_name='Test Business',
                lead_score=85,
                tier='Warm'
            )
            db.session.add(submission)
            db.session.commit()
            
            form_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'business_name': 'Test Business',
                'industry': 'E-commerce',
                'monthly_revenue': 50000
            }
            
            email_service = EmailServiceCompliant()
            result = email_service.send_confirmation_email(submission, form_data)
            
            self.assertTrue(result['success'])
            mock_send.assert_called_once()

class TestHubSpotService(ROICalculatorTestCase):
    """Test HubSpot service functionality"""
    
    @patch('requests.post')
    def test_contact_creation(self, mock_post):
        """Test HubSpot contact creation"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': '12345'}
        mock_post.return_value = mock_response
        
        hubspot_service = HubSpotServiceEnhanced()
        
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'business_name': 'Test Business',
            'industry': 'E-commerce',
            'monthly_revenue': 50000,
            'average_order_value': 75,
            'monthly_orders': 667,
            'conversion_rate': 2.0,
            'cart_abandonment_rate': 65,
            'manual_hours_per_week': 15,
            'business_stage': 'Growth'
        }
        
        result = hubspot_service.upsert_contact(form_data, 85, 'Warm')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['contact_id'], '12345')

class TestHealthEndpoint(ROICalculatorTestCase):
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        
        self.assertEqual(result['status'], 'healthy')
        self.assertIn('metrics', result)
        self.assertIn('security', result)

class TestRateLimiting(ROICalculatorTestCase):
    """Test rate limiting functionality"""
    
    def test_calculation_rate_limit(self):
        """Test rate limiting on calculation endpoint"""
        data = {'monthly_revenue': 50000}
        
        # Make requests up to the limit
        for i in range(20):
            response = self.client.post('/api/roi-calculator/calculate',
                                      data=json.dumps(data),
                                      content_type='application/json')
            self.assertEqual(response.status_code, 200)
        
        # Next request should be rate limited
        response = self.client.post('/api/roi-calculator/calculate',
                                  data=json.dumps(data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 429)

if __name__ == '__main__':
    # Set environment variables for testing
    os.environ['SENDGRID_API_KEY'] = 'test-key'
    os.environ['HUBSPOT_API_KEY'] = 'test-key'
    
    unittest.main()

