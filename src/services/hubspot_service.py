"""
HubSpot CRM Integration Service - Fixed Version
Only uses standard HubSpot properties and valid option values
"""

import os
import requests
import json
from datetime import datetime, timedelta
from src.utils.lead_scoring import get_hubspot_lifecycle_stage, get_follow_up_timeline

# HubSpot API configuration
HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
if not HUBSPOT_API_KEY:
    print("⚠️ HubSpot API key not found - HubSpot integration will be disabled")
    HUBSPOT_ENABLED = False
else:
    print("✅ HubSpot API key loaded securely from environment")
    HUBSPOT_ENABLED = True

HUBSPOT_BASE_URL = 'https://api.hubapi.com'

def get_headers():
    """Get HubSpot API headers"""
    return {
        'Authorization': f'Bearer {HUBSPOT_API_KEY}',
        'Content-Type': 'application/json'
    }

def sync_to_hubspot(submission, score_breakdown):
    """
    Complete HubSpot sync: upsert contact, create deal, enroll in workflows
    Returns: True if successful, False otherwise
    """
    try:
        # Check if HubSpot integration is enabled
        if not HUBSPOT_ENABLED:
            print("⚠️ HubSpot integration skipped - API key not configured")
            return False
        
        # Step 1: Upsert contact
        contact_id = upsert_contact(submission)
        if not contact_id:
            print("❌ Failed to upsert contact")
            return False
        
        # Update submission with contact ID
        submission.hubspot_contact_id = contact_id
        
        # Step 2: Create deal
        deal_id = create_deal(submission, contact_id)
        if not deal_id:
            print("❌ Failed to create deal")
            return False
        
        # Update submission with deal ID
        submission.hubspot_deal_id = deal_id
        
        # Step 3: Create follow-up task
        create_follow_up_task(submission, contact_id)
        
        print(f"✅ HubSpot sync complete for {submission.business_name}")
        return True
        
    except Exception as e:
        print(f"❌ HubSpot sync error: {e}")
        return False

def upsert_contact(submission):
    """
    Create or update HubSpot contact using only standard properties
    Returns: contact_id if successful, None otherwise
    """
    try:
        # Map business stage to valid HubSpot values
        business_stage_mapping = {
            'Startup': 'startup',
            'Growth': 'growing', 
            'Established': 'established',
            'Mature': 'enterprise'
        }
        
        # Map tier to valid lead status
        lead_status_mapping = {
            'Hot': 'NEW',
            'Warm': 'OPEN', 
            'Cold': 'ATTEMPTED_TO_CONTACT'
        }
        
        # Prepare contact properties using only standard HubSpot fields
        properties = {
            'email': submission.email,
            'firstname': submission.first_name,
            'lastname': submission.last_name,
            'company': submission.business_name,
            'phone': submission.phone or '',
            'website': submission.website or '',
            'industry': submission.industry,
            'lifecyclestage': get_hubspot_lifecycle_stage(submission.tier),
            'hs_lead_status': lead_status_mapping.get(submission.tier, 'NEW')
        }
        
        # Add business stage if it maps to a valid value
        mapped_stage = business_stage_mapping.get(submission.business_stage)
        if mapped_stage:
            properties['business_stage'] = mapped_stage
        
        # First, try to find existing contact by email
        search_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search"
        search_data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": submission.email
                }]
            }],
            "properties": ["id", "email", "firstname", "lastname"]
        }
        
        search_response = requests.post(search_url, headers=get_headers(), json=search_data)
        
        if search_response.status_code == 200:
            search_results = search_response.json()
            
            if search_results.get('total', 0) > 0:
                # Contact exists, update it
                contact_id = search_results['results'][0]['id']
                update_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/{contact_id}"
                
                update_response = requests.patch(
                    update_url, 
                    headers=get_headers(), 
                    json={"properties": properties}
                )
                
                if update_response.status_code == 200:
                    print(f"✅ Updated existing contact: {submission.email}")
                    return contact_id
                else:
                    print(f"❌ Failed to update contact: {update_response.text}")
                    return None
            else:
                # Contact doesn't exist, create new one
                create_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts"
                
                create_response = requests.post(
                    create_url, 
                    headers=get_headers(), 
                    json={"properties": properties}
                )
                
                if create_response.status_code == 201:
                    contact_data = create_response.json()
                    contact_id = contact_data['id']
                    print(f"✅ Created new contact: {submission.email}")
                    return contact_id
                else:
                    print(f"❌ Failed to create contact: {create_response.text}")
                    return None
        else:
            print(f"❌ Contact search failed: {search_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Contact upsert error: {e}")
        return None

def create_deal(submission, contact_id):
    """
    Create HubSpot deal and associate with contact using only standard properties
    Returns: deal_id if successful, None otherwise
    """
    try:
        # Calculate deal amount (Year-1 projected revenue delta × 0.3)
        projections = submission.calculate_projections()
        deal_amount = projections['expected']['annual_benefit'] * 0.3
        
        # Set close date (90 days from now)
        close_date = datetime.now() + timedelta(days=90)
        close_date_ms = int(close_date.timestamp() * 1000)
        
        # Prepare deal properties using only standard fields
        properties = {
            'dealname': f"{submission.business_name} – ROI Calculator Lead",
            'amount': str(int(deal_amount)),
            'closedate': str(close_date_ms),
            'dealstage': 'qualifiedtobuy',  # Standard stage that should exist
            'pipeline': 'default',  # Use default pipeline
            'deal_currency_code': 'USD',
            'hs_deal_stage_probability': '0.4',  # 40% probability as decimal
            'description': f"""ROI Calculator Lead Details:
            
Lead Score: {submission.lead_score}/150
Tier: {submission.tier}
Monthly Revenue: ${submission.monthly_revenue:,.0f}
Industry: {submission.industry}
Business Stage: {submission.business_stage}

Projected Benefits:
- Annual Benefit: ${projections['expected']['annual_benefit']:,.0f}
- ROI: {projections['expected']['roi_percentage']}%
- Break-even: {projections['expected']['break_even_months']} months

Challenges: {', '.join(submission.get_challenges_list())}
"""
        }
        
        # Create deal
        create_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals"
        
        create_response = requests.post(
            create_url, 
            headers=get_headers(), 
            json={"properties": properties}
        )
        
        if create_response.status_code == 201:
            deal_data = create_response.json()
            deal_id = deal_data['id']
            
            # Associate deal with contact
            associate_deal_with_contact(deal_id, contact_id)
            
            print(f"✅ Created deal: {submission.business_name}")
            return deal_id
        else:
            print(f"❌ Failed to create deal: {create_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Deal creation error: {e}")
        return None

def associate_deal_with_contact(deal_id, contact_id):
    """Associate deal with contact"""
    try:
        association_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/3"
        
        response = requests.put(association_url, headers=get_headers())
        
        if response.status_code in [200, 201]:
            print(f"✅ Associated deal {deal_id} with contact {contact_id}")
        else:
            print(f"❌ Failed to associate deal with contact: {response.text}")
            
    except Exception as e:
        print(f"❌ Deal association error: {e}")

def create_follow_up_task(submission, contact_id):
    """
    Create follow-up task based on lead tier
    """
    try:
        # Get follow-up timeline
        follow_up_hours = get_follow_up_timeline(submission.tier)
        due_date = datetime.now() + timedelta(hours=follow_up_hours)
        due_date_ms = int(due_date.timestamp() * 1000)
        
        # Task properties
        properties = {
            'hs_task_subject': f"Follow up with {submission.first_name} {submission.last_name} ({submission.tier} lead)",
            'hs_task_body': f"""
ROI Calculator Lead Follow-up

Contact: {submission.first_name} {submission.last_name}
Business: {submission.business_name}
Email: {submission.email}
Phone: {submission.phone or 'Not provided'}
Industry: {submission.industry}
Lead Score: {submission.lead_score}/150
Tier: {submission.tier}

Key Metrics:
- Monthly Revenue: ${submission.monthly_revenue:,.0f}
- Monthly Orders: {submission.monthly_orders:,}
- Conversion Rate: {submission.conversion_rate}%

Biggest Challenges: {', '.join(submission.get_challenges_list())}

Next Steps:
1. Review ROI projections sent via email
2. Schedule strategy call if interested
3. Qualify for implementation readiness
            """,
            'hs_task_status': 'NOT_STARTED',
            'hs_task_priority': 'HIGH' if submission.tier == 'Hot' else 'MEDIUM' if submission.tier == 'Warm' else 'LOW',
            'hs_timestamp': str(due_date_ms)
        }
        
        # Create task
        create_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/tasks"
        
        create_response = requests.post(
            create_url, 
            headers=get_headers(), 
            json={"properties": properties}
        )
        
        if create_response.status_code == 201:
            task_data = create_response.json()
            task_id = task_data['id']
            
            # Associate task with contact
            associate_task_with_contact(task_id, contact_id)
            
            print(f"✅ Created follow-up task for {submission.business_name}")
        else:
            print(f"❌ Failed to create task: {create_response.text}")
            
    except Exception as e:
        print(f"❌ Task creation error: {e}")

def associate_task_with_contact(task_id, contact_id):
    """Associate task with contact"""
    try:
        association_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/tasks/{task_id}/associations/contacts/{contact_id}/204"
        
        response = requests.put(association_url, headers=get_headers())
        
        if response.status_code in [200, 201]:
            print(f"✅ Associated task {task_id} with contact {contact_id}")
        else:
            print(f"❌ Failed to associate task with contact: {response.text}")
            
    except Exception as e:
        print(f"❌ Task association error: {e}")

def test_hubspot_connection():
    """Test HubSpot API connection and permissions"""
    try:
        # Check if HubSpot is configured
        if not HUBSPOT_API_KEY:
            print("⚠️  HubSpot API key not configured")
            return False
        
        # Test basic API access
        test_url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts?limit=1"
        response = requests.get(test_url, headers=get_headers())
        
        if response.status_code == 200:
            print("✅ HubSpot API connection successful")
            return True
        else:
            print(f"❌ HubSpot API connection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ HubSpot connection test error: {e}")
        return False

