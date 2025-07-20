"""
Fixed HubSpot CRM Integration Service - Using Only Standard Properties
"""
import os
import requests
import logging
import time
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class HubSpotServiceFixed:
    def __init__(self):
        self.api_key = os.getenv('HUBSPOT_API_KEY')
        if not self.api_key:
            logger.warning("HUBSPOT_API_KEY not found in environment variables")
            self.enabled = False
        else:
            self.enabled = True
            
        self.base_url = 'https://api.hubapi.com'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.max_retries = 3
        self.retry_delay = 2
    
    def upsert_contact(self, form_data, lead_score, tier):
        """Create or update HubSpot contact with only standard properties"""
        if not self.enabled:
            logger.warning("HubSpot service disabled - missing API key")
            return {
                'success': False,
                'error': 'HubSpot service not configured',
                'contact_id': None
            }
        
        try:
            email = form_data['email']
            
            # Map business stage to valid HubSpot values
            business_stage_mapping = {
                'Startup': 'startup',
                'Growth': 'growing',
                'Established': 'established',
                'Enterprise': 'enterprise'
            }
            
            # Map challenges to single valid value (since it's a multi-select, we'll use notes)
            challenges = form_data.get('biggest_challenges', [])
            if isinstance(challenges, list):
                challenges_text = ', '.join(challenges)
            else:
                challenges_text = str(challenges)
            
            # Use only standard HubSpot properties
            properties = {
                'email': email,
                'firstname': form_data['first_name'],
                'lastname': form_data['last_name'],
                'company': form_data['business_name'],
                'website': form_data.get('website', ''),
                'phone': form_data.get('phone', ''),
                'industry': form_data['industry'],
                'lifecyclestage': 'lead',
                
                # Use standard fields creatively for additional data
                'jobtitle': f"{tier} Priority Lead (Score: {lead_score})",
                'state': business_stage_mapping.get(form_data['business_stage'], 'growing'),
                'city': f"Monthly Revenue: ${form_data['monthly_revenue']:,}",
                'zip': str(form_data['monthly_orders']),
                
                # Use description for challenges and metrics
                'hs_content_membership_notes': f"Challenges: {challenges_text}. AOV: ${form_data['average_order_value']}, Conv: {form_data['conversion_rate']}%, Cart Abandon: {form_data['cart_abandonment_rate']}%"
            }
            
            # Try to find existing contact first
            search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
            search_payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }]
                }],
                "properties": ["id", "email", "firstname", "lastname"]
            }
            
            search_response = self._make_request('POST', search_url, search_payload)
            
            if search_response and search_response.get('results'):
                # Update existing contact
                contact_id = search_response['results'][0]['id']
                update_url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
                update_payload = {"properties": properties}
                
                response = self._make_request('PATCH', update_url, update_payload)
                
                if response:
                    logger.info(f"Updated HubSpot contact: {contact_id}")
                    return {
                        'success': True,
                        'contact_id': contact_id,
                        'action': 'updated'
                    }
            else:
                # Create new contact
                create_url = f"{self.base_url}/crm/v3/objects/contacts"
                create_payload = {"properties": properties}
                
                response = self._make_request('POST', create_url, create_payload)
                
                if response:
                    contact_id = response['id']
                    logger.info(f"Created HubSpot contact: {contact_id}")
                    return {
                        'success': True,
                        'contact_id': contact_id,
                        'action': 'created'
                    }
            
            return {'success': False, 'error': 'Failed to create/update contact'}
            
        except Exception as e:
            logger.error(f"HubSpot contact upsert error: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_deal(self, form_data, contact_id, lead_score):
        """Create HubSpot deal with standard properties"""
        try:
            # Calculate deal amount based on monthly revenue
            monthly_revenue = float(form_data['monthly_revenue'])
            deal_amount = monthly_revenue * 12 * 0.15  # 15% of annual revenue as potential deal value
            
            # Determine deal stage based on tier
            tier = self._get_tier_from_score(lead_score)
            stage_mapping = {
                'Hot': 'qualifiedtobuy',
                'Warm': 'presentationscheduled', 
                'Cold': 'appointmentscheduled'
            }
            
            properties = {
                'dealname': f"ROI Calculator Lead - {form_data['business_name']}",
                'amount': str(int(deal_amount)),
                'dealstage': stage_mapping.get(tier, 'qualifiedtobuy'),
                'pipeline': 'default',
                'closedate': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'dealtype': 'newbusiness',
                
                # Use description for additional context
                'description': f"Lead Score: {lead_score}, Tier: {tier}, Industry: {form_data['industry']}, Monthly Revenue: ${monthly_revenue:,}"
            }
            
            # Create deal
            url = f"{self.base_url}/crm/v3/objects/deals"
            payload = {"properties": properties}
            
            response = self._make_request('POST', url, payload)
            
            if response:
                deal_id = response['id']
                
                # Associate deal with contact
                self._associate_deal_with_contact(deal_id, contact_id)
                
                # Create follow-up task
                self._create_follow_up_task(contact_id, deal_id, tier, form_data)
                
                logger.info(f"Created HubSpot deal: {deal_id}")
                return {
                    'success': True,
                    'deal_id': deal_id,
                    'deal_amount': deal_amount
                }
            
            return {'success': False, 'error': 'Failed to create deal'}
            
        except Exception as e:
            logger.error(f"HubSpot deal creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _associate_deal_with_contact(self, deal_id, contact_id):
        """Associate deal with contact"""
        try:
            url = f"{self.base_url}/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/3"
            
            response = self._make_request('PUT', url, {})
            
            if response:
                logger.info(f"Associated deal {deal_id} with contact {contact_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Deal association error: {e}")
            return False
    
    def _create_follow_up_task(self, contact_id, deal_id, tier, form_data):
        """Create follow-up task based on lead tier"""
        try:
            # Task timing based on tier
            timing_mapping = {
                'Hot': 1,    # 1 hour
                'Warm': 24,  # 24 hours
                'Cold': 72   # 72 hours
            }
            
            hours_delay = timing_mapping.get(tier, 24)
            due_date = datetime.now() + timedelta(hours=hours_delay)
            
            # Task content based on tier
            task_templates = {
                'Hot': f"🔥 HIGH PRIORITY: Call {form_data['first_name']} {form_data['last_name']} from {form_data['business_name']} ASAP. Monthly Revenue: ${form_data['monthly_revenue']}. They're ready to buy!",
                'Warm': f"📞 Follow up with {form_data['first_name']} {form_data['last_name']} from {form_data['business_name']}. Monthly Revenue: ${form_data['monthly_revenue']}. Good potential.",
                'Cold': f"📧 Send nurture email to {form_data['first_name']} {form_data['last_name']} from {form_data['business_name']}. Long-term opportunity."
            }
            
            properties = {
                'hs_task_subject': f"ROI Calculator Follow-up - {tier} Priority",
                'hs_task_body': task_templates.get(tier, task_templates['Warm']),
                'hs_task_status': 'NOT_STARTED',
                'hs_task_priority': 'HIGH' if tier == 'Hot' else 'MEDIUM' if tier == 'Warm' else 'LOW',
                'hs_task_type': 'CALL' if tier in ['Hot', 'Warm'] else 'EMAIL',
                'hs_timestamp': int(due_date.timestamp() * 1000)  # HubSpot expects milliseconds
            }
            
            url = f"{self.base_url}/crm/v3/objects/tasks"
            payload = {"properties": properties}
            
            response = self._make_request('POST', url, payload)
            
            if response:
                task_id = response['id']
                
                # Associate task with contact and deal
                self._associate_task(task_id, contact_id, 'contacts')
                self._associate_task(task_id, deal_id, 'deals')
                
                logger.info(f"Created follow-up task: {task_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Task creation error: {e}")
            return False
    
    def _associate_task(self, task_id, object_id, object_type):
        """Associate task with contact or deal"""
        try:
            association_mapping = {
                'contacts': '204',
                'deals': '216'
            }
            
            association_type = association_mapping.get(object_type)
            if not association_type:
                return False
            
            url = f"{self.base_url}/crm/v3/objects/tasks/{task_id}/associations/{object_type}/{object_id}/{association_type}"
            
            response = self._make_request('PUT', url, {})
            
            if response:
                logger.info(f"Associated task {task_id} with {object_type} {object_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Task association error: {e}")
            return False
    
    def _make_request(self, method, url, payload=None):
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=self.headers)
                elif method == 'POST':
                    response = requests.post(url, headers=self.headers, json=payload)
                elif method == 'PATCH':
                    response = requests.patch(url, headers=self.headers, json=payload)
                elif method == 'PUT':
                    response = requests.put(url, headers=self.headers, json=payload)
                else:
                    return None
                
                if response.status_code in [200, 201, 204]:
                    return response.json() if response.content else {}
                elif response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get('Retry-After', 10))
                    logger.warning(f"Rate limited, waiting {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HubSpot API error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def _get_tier_from_score(self, score):
        """Get tier from lead score"""
        if score >= 100:
            return 'Hot'
        elif score >= 60:
            return 'Warm'
        else:
            return 'Cold'
    
    def get_contact_by_email(self, email):
        """Get contact by email address"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/search"
            payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }]
                }],
                "properties": ["id", "email", "firstname", "lastname", "notes_last_contacted"]
            }
            
            response = self._make_request('POST', url, payload)
            
            if response and response.get('results'):
                return response['results'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Contact lookup error: {e}")
            return None

