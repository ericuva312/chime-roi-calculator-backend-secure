"""
HubSpot CRM Integration Service - REAL WORKING VERSION
Properly creates contacts and deals in HubSpot with correct property mapping
"""

import os
import requests
import json
from datetime import datetime, timedelta

# HubSpot API configuration from environment
HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
HUBSPOT_BASE_URL = 'https://api.hubapi.com'

def get_headers():
    """Get HubSpot API headers"""
    return {
        'Authorization': f'Bearer {HUBSPOT_API_KEY}',
        'Content-Type': 'application/json'
    }

def map_business_stage(frontend_value):
    """Map frontend business stage values to HubSpot values"""
    mapping = {
        'Startup': 'startup',
        'Growth': 'growing', 
        'Established': 'established',
        'Mature': 'enterprise'
    }
    return mapping.get(frontend_value, 'growing')

def create_hubspot_contact(submission_data):
    """Create a new contact in HubSpot"""
    try:
        if not HUBSPOT_API_KEY:
            print("⚠️ HubSpot API key not configured")
            return None
            
        # Map business stage to HubSpot format
        business_stage = map_business_stage(submission_data.get('business_stage', 'Growth'))
        
        contact_properties = {
            'email': submission_data['email'],
            'firstname': submission_data['first_name'],
            'lastname': submission_data['last_name'],
            'company': submission_data['business_name'],
            'phone': submission_data.get('phone', ''),
            'website': submission_data.get('website', ''),
            'monthly_revenue': str(submission_data['monthly_revenue']),
            'industry': submission_data['industry'],
            'business_stage': business_stage,
            'lead_score': str(submission_data.get('lead_score', 100)),
            'lifecyclestage': 'lead',
            'hs_lead_status': 'NEW'
        }
        
        # Remove empty values
        contact_properties = {k: v for k, v in contact_properties.items() if v}
        
        contact_data = {
            'properties': contact_properties
        }
        
        print(f"🔄 Creating HubSpot contact for {submission_data['email']}")
        
        response = requests.post(
            f'{HUBSPOT_BASE_URL}/crm/v3/objects/contacts',
            headers=get_headers(),
            json=contact_data,
            timeout=15
        )
        
        if response.status_code == 201:
            contact = response.json()
            contact_id = contact.get('id')
            print(f"✅ HubSpot contact created: {contact_id}")
            return contact_id
        else:
            print(f"❌ HubSpot contact creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ HubSpot contact creation error: {e}")
        return None

def create_hubspot_deal(submission_data, contact_id):
    """Create a new deal in HubSpot"""
    try:
        if not HUBSPOT_API_KEY:
            print("⚠️ HubSpot API key not configured")
            return None
            
        # Calculate deal value from projections
        expected_annual_benefit = submission_data.get('expected_annual_benefit', 0)
        if not expected_annual_benefit:
            # Calculate from monthly revenue (30% increase)
            monthly_revenue = submission_data.get('monthly_revenue', 0)
            expected_annual_benefit = monthly_revenue * 0.30 * 12
        
        deal_properties = {
            'dealname': f"ROI Calculator Lead - {submission_data['business_name']}",
            'dealstage': 'appointmentscheduled',
            'amount': str(int(expected_annual_benefit)),
            'pipeline': 'default',
            'closedate': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        }
        
        # Create deal with contact association
        deal_data = {
            'properties': deal_properties,
            'associations': [
                {
                    'to': {'id': contact_id},
                    'types': [{'associationCategory': 'HUBSPOT_DEFINED', 'associationTypeId': 3}]
                }
            ]
        }
        
        print(f"🔄 Creating HubSpot deal for contact {contact_id}")
        
        response = requests.post(
            f'{HUBSPOT_BASE_URL}/crm/v3/objects/deals',
            headers=get_headers(),
            json=deal_data,
            timeout=15
        )
        
        if response.status_code == 201:
            deal = response.json()
            deal_id = deal.get('id')
            print(f"✅ HubSpot deal created: {deal_id}")
            return deal_id
        else:
            print(f"❌ HubSpot deal creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ HubSpot deal creation error: {e}")
        return None

def sync_to_hubspot(submission_data):
    """
    Main function to sync submission to HubSpot
    Returns: dict with contact_id and deal_id if successful
    """
    try:
        print(f"🔄 Starting HubSpot sync for {submission_data.get('email', 'unknown')}")
        
        # Create contact
        contact_id = create_hubspot_contact(submission_data)
        if not contact_id:
            return {'success': False, 'error': 'Failed to create contact'}
        
        # Create deal
        deal_id = create_hubspot_deal(submission_data, contact_id)
        if not deal_id:
            return {
                'success': True,
                'contact_id': contact_id,
                'deal_id': None,
                'warning': 'Contact created but deal creation failed'
            }
        
        print(f"✅ HubSpot sync completed successfully")
        return {
            'success': True,
            'contact_id': contact_id,
            'deal_id': deal_id
        }
        
    except Exception as e:
        print(f"❌ HubSpot sync failed: {e}")
        return {'success': False, 'error': str(e)}

class HubSpotServiceReal:
    """Real HubSpot service class"""
    
    @staticmethod
    def sync_submission(submission_data):
        """Sync submission to HubSpot"""
        return sync_to_hubspot(submission_data)
    
    @staticmethod
    def test_connection():
        """Test HubSpot API connection"""
        try:
            if not HUBSPOT_API_KEY:
                return False
                
            response = requests.get(
                f'{HUBSPOT_BASE_URL}/account-info/v3/details',
                headers=get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

