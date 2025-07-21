"""
Email Service for ROI Calculator - REAL WORKING VERSION
Handles customer confirmation emails and internal notifications via SendGrid
"""

import os
import requests
import json
from datetime import datetime

# SendGrid configuration from environment
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_BASE_URL = 'https://api.sendgrid.com/v3'
FROM_EMAIL = 'hello@chimehq.co'
FROM_NAME = 'Chime Revenue Growth Calculator'

def get_headers():
    """Get SendGrid API headers"""
    return {
        'Authorization': f'Bearer {SENDGRID_API_KEY}',
        'Content-Type': 'application/json'
    }

def generate_customer_email_html(submission_data, projections):
    """Generate HTML email content for customer"""
    first_name = submission_data.get('first_name', 'there')
    business_name = submission_data.get('business_name', 'your business')
    industry = submission_data.get('industry', 'your industry')
    
    # Get expected scenario projections
    expected = projections.get('expected', {})
    monthly_benefit = expected.get('monthly_benefit', 0)
    annual_benefit = expected.get('annual_benefit', 0)
    payback_period = expected.get('payback_period', 0)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Your Revenue Growth Analysis</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #2E7D32; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .highlight {{ background: #E8F5E8; padding: 15px; border-left: 4px solid #2E7D32; margin: 20px 0; }}
            .projections {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .cta {{ text-align: center; margin: 30px 0; }}
            .cta a {{ background: #2E7D32; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Your {industry} Growth Analysis</h1>
                <p>Personalized Revenue Projections for {business_name}</p>
            </div>
            
            <div class="content">
                <h2>Hi {first_name},</h2>
                
                <p>Thank you for using our Revenue Growth Calculator! Based on your business metrics, we've identified significant growth opportunities for {business_name}.</p>
                
                <div class="highlight">
                    <h3>🎯 Your Growth Potential (Expected Scenario)</h3>
                    <ul>
                        <li><strong>Additional Monthly Revenue:</strong> ${monthly_benefit:,.0f}</li>
                        <li><strong>Additional Annual Revenue:</strong> ${annual_benefit:,.0f}</li>
                        <li><strong>Payback Period:</strong> {payback_period} months</li>
                    </ul>
                </div>
                
                <div class="projections">
                    <h3>📊 Complete Projections</h3>
                    <p><strong>Conservative Scenario (90% confidence):</strong></p>
                    <ul>
                        <li>Monthly Benefit: ${projections.get('conservative', {}).get('monthly_benefit', 0):,.0f}</li>
                        <li>Annual Benefit: ${projections.get('conservative', {}).get('annual_benefit', 0):,.0f}</li>
                    </ul>
                    
                    <p><strong>Expected Scenario (70% confidence):</strong></p>
                    <ul>
                        <li>Monthly Benefit: ${expected.get('monthly_benefit', 0):,.0f}</li>
                        <li>Annual Benefit: ${expected.get('annual_benefit', 0):,.0f}</li>
                    </ul>
                    
                    <p><strong>Optimistic Scenario (40% confidence):</strong></p>
                    <ul>
                        <li>Monthly Benefit: ${projections.get('optimistic', {}).get('monthly_benefit', 0):,.0f}</li>
                        <li>Annual Benefit: ${projections.get('optimistic', {}).get('annual_benefit', 0):,.0f}</li>
                    </ul>
                </div>
                
                <p>These projections are based on your current monthly revenue of ${submission_data.get('monthly_revenue', 0):,.0f} and industry benchmarks for {industry} businesses.</p>
                
                <div class="cta">
                    <a href="https://chimehq.co/implementation">Get Your Implementation Plan</a>
                </div>
                
                <p>Questions? Reply to this email or visit <a href="https://chimehq.co">chimehq.co</a></p>
                
                <p>Best regards,<br>
                The Chime Team<br>
                <a href="mailto:hello@chimehq.co">hello@chimehq.co</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def generate_internal_notification_html(submission_data, projections):
    """Generate HTML email content for internal notification"""
    lead_score = submission_data.get('lead_score', 0)
    tier = submission_data.get('tier', 'Unknown')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>New ROI Calculator Lead</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1976D2; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .lead-info {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .high-value {{ background: #E8F5E8; border-left: 4px solid #2E7D32; }}
            .medium-value {{ background: #FFF3E0; border-left: 4px solid #F57C00; }}
            .low-value {{ background: #FFEBEE; border-left: 4px solid #D32F2F; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 New ROI Calculator Lead</h1>
                <p>Lead Score: {lead_score} | Tier: {tier}</p>
            </div>
            
            <div class="content">
                <div class="lead-info {'high-value' if lead_score >= 80 else 'medium-value' if lead_score >= 50 else 'low-value'}">
                    <h3>Contact Information</h3>
                    <ul>
                        <li><strong>Name:</strong> {submission_data.get('first_name', '')} {submission_data.get('last_name', '')}</li>
                        <li><strong>Email:</strong> {submission_data.get('email', '')}</li>
                        <li><strong>Phone:</strong> {submission_data.get('phone', 'Not provided')}</li>
                        <li><strong>Company:</strong> {submission_data.get('business_name', '')}</li>
                        <li><strong>Website:</strong> {submission_data.get('website', 'Not provided')}</li>
                    </ul>
                    
                    <h3>Business Details</h3>
                    <ul>
                        <li><strong>Monthly Revenue:</strong> ${submission_data.get('monthly_revenue', 0):,.0f}</li>
                        <li><strong>Industry:</strong> {submission_data.get('industry', '')}</li>
                        <li><strong>Business Stage:</strong> {submission_data.get('business_stage', '')}</li>
                        <li><strong>Lead Score:</strong> {lead_score}</li>
                        <li><strong>Tier:</strong> {tier}</li>
                    </ul>
                    
                    <h3>Revenue Projections</h3>
                    <ul>
                        <li><strong>Expected Monthly Benefit:</strong> ${projections.get('expected', {}).get('monthly_benefit', 0):,.0f}</li>
                        <li><strong>Expected Annual Benefit:</strong> ${projections.get('expected', {}).get('annual_benefit', 0):,.0f}</li>
                        <li><strong>Payback Period:</strong> {projections.get('expected', {}).get('payback_period', 0)} months</li>
                    </ul>
                </div>
                
                <p><strong>Submission Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <p>This lead was generated from the ROI Calculator on chimehq.co</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def send_customer_email(submission_data, projections):
    """Send confirmation email to customer"""
    try:
        if not SENDGRID_API_KEY:
            print("⚠️ SendGrid API key not configured")
            return {'success': False, 'error': 'API key not configured'}
            
        email_data = {
            "personalizations": [
                {
                    "to": [
                        {
                            "email": submission_data['email'],
                            "name": f"{submission_data.get('first_name', '')} {submission_data.get('last_name', '')}"
                        }
                    ],
                    "subject": f"Your {submission_data.get('industry', 'Business')} Growth Analysis - Revenue Projections Inside"
                }
            ],
            "from": {
                "email": FROM_EMAIL,
                "name": FROM_NAME
            },
            "content": [
                {
                    "type": "text/html",
                    "value": generate_customer_email_html(submission_data, projections)
                }
            ],
            "tracking_settings": {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True}
            }
        }
        
        print(f"📧 Sending customer email to {submission_data['email']}")
        
        response = requests.post(
            f'{SENDGRID_BASE_URL}/mail/send',
            headers=get_headers(),
            json=email_data,
            timeout=15
        )
        
        if response.status_code == 202:
            message_id = response.headers.get('X-Message-Id')
            print(f"✅ Customer email sent successfully. Message ID: {message_id}")
            return {'success': True, 'message_id': message_id}
        else:
            print(f"❌ Customer email failed: {response.status_code} - {response.text}")
            return {'success': False, 'error': response.text}
            
    except Exception as e:
        print(f"❌ Customer email error: {e}")
        return {'success': False, 'error': str(e)}

def send_internal_notification(submission_data, projections):
    """Send internal notification email to hello@chimehq.co"""
    try:
        if not SENDGRID_API_KEY:
            print("⚠️ SendGrid API key not configured")
            return {'success': False, 'error': 'API key not configured'}
            
        email_data = {
            "personalizations": [
                {
                    "to": [
                        {
                            "email": "hello@chimehq.co",
                            "name": "Chime Team"
                        }
                    ],
                    "subject": f"🎯 New ROI Calculator Lead: {submission_data.get('business_name', 'Unknown')} (Score: {submission_data.get('lead_score', 0)})"
                }
            ],
            "from": {
                "email": FROM_EMAIL,
                "name": FROM_NAME
            },
            "content": [
                {
                    "type": "text/html",
                    "value": generate_internal_notification_html(submission_data, projections)
                }
            ]
        }
        
        print(f"📧 Sending internal notification to hello@chimehq.co")
        
        response = requests.post(
            f'{SENDGRID_BASE_URL}/mail/send',
            headers=get_headers(),
            json=email_data,
            timeout=15
        )
        
        if response.status_code == 202:
            message_id = response.headers.get('X-Message-Id')
            print(f"✅ Internal notification sent successfully. Message ID: {message_id}")
            return {'success': True, 'message_id': message_id}
        else:
            print(f"❌ Internal notification failed: {response.status_code} - {response.text}")
            return {'success': False, 'error': response.text}
            
    except Exception as e:
        print(f"❌ Internal notification error: {e}")
        return {'success': False, 'error': str(e)}

def send_all_emails(submission_data, projections):
    """Send both customer and internal emails"""
    try:
        print(f"📧 Sending emails for {submission_data.get('email', 'unknown')}")
        
        # Send customer email
        customer_result = send_customer_email(submission_data, projections)
        
        # Send internal notification
        internal_result = send_internal_notification(submission_data, projections)
        
        return {
            'customer_email': customer_result,
            'internal_email': internal_result,
            'success': customer_result.get('success', False) and internal_result.get('success', False)
        }
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return {'success': False, 'error': str(e)}

def test_sendgrid_connection():
    """Test SendGrid API connection"""
    try:
        if not SENDGRID_API_KEY:
            return False
            
        response = requests.get(
            f'{SENDGRID_BASE_URL}/user/account',
            headers=get_headers(),
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False

