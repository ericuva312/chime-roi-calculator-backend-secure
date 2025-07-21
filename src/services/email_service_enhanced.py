"""
Enhanced Email Service for ROI Calculator
Handles customer confirmation emails and internal notifications via SendGrid
Uses premium HTML template with personalized business insights
"""

import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime
import json

# Load API key from environment
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
if not SENDGRID_API_KEY:
    print("⚠️ SendGrid API key not found - Email integration will be disabled")
    SENDGRID_ENABLED = False
else:
    # API key is already in full SG.xxx.xxx format
    print("✅ SendGrid API key loaded securely from environment")
    SENDGRID_ENABLED = True

FROM_EMAIL = 'hello@chimehq.co'
FROM_NAME = 'Chime Growth Team'

# Premium HTML Email Template
PREMIUM_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Personalized Business Insights from Chime</title>
  <style>
    /* --- Base Styles --- */
    body {
      margin: 0;
      padding: 0;
      background-color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    }
    .container {
      max-width: 600px;
      margin: 0 auto;
      background-color: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
    }
    .content {
      padding: 30px;
    }
    h1, h2, h3, p {
      margin: 0;
    }
    a {
      color: #2563eb;
      text-decoration: none;
    }

    /* --- Header --- */
    .header {
      background: linear-gradient(135deg, #1e40af 0%, #3730a3 100%);
      color: white;
      padding: 40px;
      text-align: center;
    }
    .header h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 10px;
    }
    .header p {
      font-size: 18px;
      opacity: 0.9;
    }

    /* --- Introduction --- */
    .intro {
      text-align: center;
      padding: 30px 0;
      border-bottom: 1px solid #e2e8f0;
    }
    .intro h2 {
      font-size: 22px;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 15px;
    }
    .intro p {
      font-size: 16px;
      color: #475569;
      line-height: 1.6;
    }

    /* --- Scenarios Table --- */
    .scenarios-table {
      width: 100%;
      border-collapse: collapse;
      margin: 30px 0;
    }
    .scenarios-table th, .scenarios-table td {
      padding: 15px;
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
    }
    .scenarios-table th {
      background-color: #f1f5f9;
      font-size: 14px;
      font-weight: 600;
      color: #475569;
      text-transform: uppercase;
    }
    .scenarios-table td {
      font-size: 16px;
      color: #1e293b;
    }
    .scenarios-table .scenario-name {
      font-weight: 600;
    }
    .scenarios-table .revenue-increase {
      color: #16a34a;
      font-weight: 700;
    }

    /* --- Next Steps --- */
    .next-steps {
      background-color: #f8fafc;
      padding: 25px;
      border-radius: 8px;
      margin-bottom: 30px;
    }
    .next-steps h3 {
      font-size: 18px;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 15px;
    }
    .next-steps ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .next-steps li {
      font-size: 16px;
      color: #475569;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
    }
    .next-steps li::before {
      content: "\\2713";
      color: #2563eb;
      font-weight: bold;
      margin-right: 10px;
    }

    /* --- CTA Button --- */
    .cta-button {
      display: inline-block;
      width: fit-content;
      margin: 0 auto;
      background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%);
      color: white !important;
      padding: 22px 45px;
      border-radius: 20px;
      font-size: 22px;
      font-weight: 800;
      text-align: center;
      text-decoration: none;
      letter-spacing: 0.5px;
      box-shadow: 0 12px 30px rgba(37, 99, 235, 0.4), 0 6px 15px rgba(0, 0, 0, 0.15);
      transition: all 0.3s ease;
      border: 3px solid rgba(255, 255, 255, 0.2);
      position: relative;
      overflow: hidden;
      text-transform: uppercase;
    }
    .cta-button:hover {
      transform: translateY(-4px);
      box-shadow: 0 18px 40px rgba(37, 99, 235, 0.6), 0 10px 25px rgba(0, 0, 0, 0.25);
      background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 50%, #1e3a8a 100%);
      border-color: rgba(255, 255, 255, 0.3);
    }
    .cta-button:before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
      transition: left 0.6s;
    }
    .cta-button:hover:before {
      left: 100%;
    }
    /* --- Footer --- */
    .footer {
      text-align: center;
      padding: 30px;
      font-size: 14px;
      color: #94a3b8;
    }

    /* --- Mobile Responsive --- */
    @media (max-width: 600px) {
      .container {
        margin: 10px;
        border-radius: 8px;
      }
      .header {
        padding: 30px 20px;
      }
      .header h1 {
        font-size: 24px;
      }
      .content {
        padding: 20px;
      }
      .scenarios-table th, .scenarios-table td {
        padding: 10px 8px;
        font-size: 14px;
      }
      .cta-button {
        padding: 18px 30px;
        font-size: 18px;
        border-radius: 16px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Your Personalized Business Insights</h1>
      <p>Thank you for your interest in Chime, {{first_name}}!</p>
    </div>
    <div class="content">
      <div class="intro">
        <h2>🚀 Unlock Your Business's True Potential Today</h2>
        <p>Thank you for exploring how Chime's AI-powered automation platform can accelerate your growth. <strong>Chime has helped 2,847+ businesses achieve an average of 35% revenue growth</strong> in their first year.</p>
        <p>Below is your personalized analysis based on your {{industry}} business metrics:</p>
      </div>

      <table class="scenarios-table">
        <thead>
          <tr>
            <th>Scenario</th>
            <th>Revenue Increase</th>
            <th>Time Saved</th>
            <th>Payback Period</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="scenario-name">Low</td>
            <td class="revenue-increase">{{conservative_revenue_increase}}%</td>
            <td>{{conservative_time_saved}} hours/week</td>
            <td>{{conservative_payback}} months</td>
          </tr>
          <tr>
            <td class="scenario-name">Expected</td>
            <td class="revenue-increase">{{expected_revenue_increase}}%</td>
            <td>{{expected_time_saved}} hours/week</td>
            <td>{{expected_payback}} months</td>
          </tr>
          <tr>
            <td class="scenario-name">High</td>
            <td class="revenue-increase">{{optimistic_revenue_increase}}%</td>
            <td>{{optimistic_time_saved}} hours/week</td>
            <td>{{optimistic_payback}} months</td>
          </tr>
        </tbody>
      </table>

      <div class="next-steps">
        <h3>What's next?</h3>
        <ul>
          <li>Review your Revenue Growth Plan.</li>
          <li>One of our growth experts will review your data and reach out shortly to discuss tailored strategies.</li>
          <li>Meanwhile, dive into our success stories to see how businesses like yours have soared with Chime.</li>
        </ul>
      </div>

      <div style="text-align: center; margin-bottom: 30px; padding: 20px; background-color: #f8fafc; border-radius: 8px;">
        <p style="font-size: 16px; color: #475569; margin: 0; line-height: 1.6;">
          Ready to supercharge your business? Schedule a no-obligation strategy call with us today and take the first step toward transformational growth.
        </p>
      </div>

      <div style="text-align: center;">
        <a href="https://www.chimehq.co/#/contact?utm_source=roi_calculator&utm_medium=email&utm_campaign=confirmation" class="cta-button">
          📞 Schedule a Strategy Call
        </a>
      </div>
      
      <div style="text-align: center; margin-top: 15px; color: #6b7280; font-size: 14px;">
        Free 30-minute consultation • No commitment required
      </div>
    </div>
    <div class="footer">
      <p><strong>Questions?</strong> Reply to this email—we personally read every message.</p>
      <p>&copy; 2025 Chime. All rights reserved.</p>
      <p>hello@chimehq.co</p>
    </div>
  </div>
</body>
</html>"""

def send_confirmation_email(submission, projections):
    """
    Send customer confirmation email with ROI projections using premium template
    """
    try:
        # Check if SendGrid integration is enabled
        if not SENDGRID_ENABLED:
            print("⚠️ Email sending skipped - SendGrid API key not configured")
            return False
        
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        
        # Email subject with personalization
        subject = f"Thank you for contacting Chime – See your personalized business insights!"
        
        # Generate email content using premium template
        html_content = generate_premium_email_html(submission, projections)
        plain_content = generate_premium_email_plain(submission, projections)
        
        # Create email
        from_email = Email(FROM_EMAIL, FROM_NAME)
        to_email = To(submission.email)
        
        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_content
        )
        
        # Send email
        response = sg.send(mail)
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Premium confirmation email sent to {submission.email}")
            return True
        else:
            print(f"❌ Email send failed: {response.status_code} - {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ Email service error: {e}")
        return False

def generate_premium_email_html(submission, projections):
    """Generate premium HTML email using template with dynamic data"""
    
    # Extract scenario data
    conservative = projections.get('conservative', {})
    expected = projections.get('expected', {})
    optimistic = projections.get('optimistic', {})
    
    # Populate template with dynamic data
    html_content = PREMIUM_EMAIL_TEMPLATE.replace('{{first_name}}', submission.first_name)
    html_content = html_content.replace('{{industry}}', submission.industry)
    html_content = html_content.replace('{{business_name}}', submission.business_name)
    
    # Conservative scenario
    html_content = html_content.replace('{{conservative_revenue_increase}}', str(conservative.get('revenueIncrease', 15)))
    html_content = html_content.replace('{{conservative_time_saved}}', str(conservative.get('timeSaved', 14)))
    html_content = html_content.replace('{{conservative_payback}}', str(conservative.get('paybackMonths', 1.8)))
    
    # Expected scenario
    html_content = html_content.replace('{{expected_revenue_increase}}', str(expected.get('revenueIncrease', 20)))
    html_content = html_content.replace('{{expected_time_saved}}', str(expected.get('timeSaved', 20)))
    html_content = html_content.replace('{{expected_payback}}', str(expected.get('paybackMonths', 1.2)))
    
    # Optimistic scenario
    html_content = html_content.replace('{{optimistic_revenue_increase}}', str(optimistic.get('revenueIncrease', 30)))
    html_content = html_content.replace('{{optimistic_time_saved}}', str(optimistic.get('timeSaved', 28)))
    html_content = html_content.replace('{{optimistic_payback}}', str(optimistic.get('paybackMonths', 0.8)))
    
    return html_content

def generate_premium_email_plain(submission, projections):
    """Generate premium plain text email"""
    
    # Extract scenario data
    conservative = projections.get('conservative', {})
    expected = projections.get('expected', {})
    optimistic = projections.get('optimistic', {})
    
    plain_content = f"""
Hi {submission.first_name},

Thank you for your interest in Chime!

🚀 READY TO TRANSFORM YOUR BUSINESS?

We appreciate you taking the time to explore your growth potential with Chime's AI-powered automation platform. Chime has helped 2,847+ businesses achieve an average of 35% revenue growth in their first year.

Below is your personalized analysis based on your {submission.industry} business metrics:

YOUR BUSINESS SCENARIOS:

Low Scenario:
- Revenue Increase: {conservative.get('revenueIncrease', 15)}%
- Time Saved: {conservative.get('timeSaved', 14)} hours/week
- Payback Period: {conservative.get('paybackMonths', 1.8)} months

Expected Scenario:
- Revenue Increase: {expected.get('revenueIncrease', 20)}%
- Time Saved: {expected.get('timeSaved', 20)} hours/week
- Payback Period: {expected.get('paybackMonths', 1.2)} months

High Scenario:
- Revenue Increase: {optimistic.get('revenueIncrease', 30)}%
- Time Saved: {optimistic.get('timeSaved', 28)} hours/week
- Payback Period: {optimistic.get('paybackMonths', 0.8)} months

WHAT HAPPENS NEXT?

✓ Your detailed growth analysis report will arrive in your inbox within 5 minutes
✓ A member of our team will review your information and reach out shortly
✓ In the meantime, explore our case studies to see how we've helped businesses like {submission.business_name}
✓ Ready to take the next step? Schedule a no-obligation strategy call with us

📅 SCHEDULE YOUR STRATEGY CALL
https://www.chimehq.co/#/contact?utm_source=roi_calculator&utm_medium=email&utm_campaign=confirmation

Free 30-minute consultation • No commitment required

Questions? Reply to this email—we personally read every message.

Best regards,
Chime Growth Team
hello@chimehq.co

© 2025 Chime. All rights reserved.
    """
    
    return plain_content

def send_internal_notification(submission, score_breakdown):
    """
    Send internal notification email to team
    """
    try:
        # Check if SendGrid integration is enabled
        if not SENDGRID_ENABLED:
            print("⚠️ Internal notification skipped - SendGrid API key not configured")
            return False
        
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        
        # Subject with lead tier and score
        subject = f"New ROI Lead · {submission.business_name} · {submission.tier}/{submission.lead_score}"
        
        # Generate internal email content
        html_content = generate_internal_notification_html(submission, score_breakdown)
        plain_content = generate_internal_notification_plain(submission, score_breakdown)
        
        # Create email
        from_email = Email(FROM_EMAIL, FROM_NAME)
        to_email = To(FROM_EMAIL)  # Send to hello@chimehq.co
        
        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_content
        )
        
        # Send email
        response = sg.send(mail)
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Internal notification sent for {submission.business_name}")
            return True
        else:
            print(f"❌ Internal notification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Internal notification error: {e}")
        return False

def generate_internal_notification_html(submission, score_breakdown):
    """Generate HTML content for internal notification email"""
    
    challenges = submission.get_challenges_list()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>New ROI Calculator Lead</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .header {{ background-color: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
            .section {{ margin-bottom: 20px; }}
            .section-title {{ font-weight: bold; color: #1f2937; margin-bottom: 10px; }}
            .tier-{submission.tier.lower()} {{ background-color: {'#dc2626' if submission.tier == 'Hot' else '#f59e0b' if submission.tier == 'Warm' else '#6b7280'}; color: white; padding: 5px 10px; border-radius: 4px; display: inline-block; }}
            .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            .metric {{ background-color: white; padding: 10px; border-radius: 4px; }}
            .score-breakdown {{ background-color: white; padding: 15px; border-radius: 4px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>New ROI Calculator Lead</h2>
                <div>Score: {submission.lead_score}/150 | Tier: <span class="tier-{submission.tier.lower()}">{submission.tier}</span></div>
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="section-title">Lead Snapshot</div>
                    <div class="metrics">
                        <div class="metric"><strong>Name:</strong> {submission.first_name} {submission.last_name}</div>
                        <div class="metric"><strong>Email:</strong> {submission.email}</div>
                        <div class="metric"><strong>Business:</strong> {submission.business_name}</div>
                        <div class="metric"><strong>Industry:</strong> {submission.industry}</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Key Metrics</div>
                    <div class="metrics">
                        <div class="metric"><strong>Monthly Revenue:</strong> ${submission.monthly_revenue:,.0f}</div>
                        <div class="metric"><strong>Business Stage:</strong> {submission.business_stage}</div>
                        <div class="metric"><strong>Conversion Rate:</strong> {submission.conversion_rate}%</div>
                        <div class="metric"><strong>Cart Abandonment:</strong> {submission.cart_abandonment_rate}%</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Lead Score Breakdown</div>
                    <div class="score-breakdown">
                        <table>
                            <tr><th>Category</th><th>Score</th><th>Details</th></tr>
                            <tr><td>Demographic</td><td>{score_breakdown['demographic']}/60</td><td>Revenue tier, business stage</td></tr>
                            <tr><td>Behavioral</td><td>{score_breakdown['behavioral']}/52</td><td>Form completion, engagement</td></tr>
                            <tr><td>Fit</td><td>{score_breakdown['fit']}/38</td><td>Industry match, challenge alignment</td></tr>
                            <tr><td><strong>Total</strong></td><td><strong>{submission.lead_score}/150</strong></td><td><strong>Tier: {submission.tier}</strong></td></tr>
                        </table>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Next Steps</div>
                    <ul>
                        <li>Follow up within: {1 if submission.tier == 'Hot' else 24 if submission.tier == 'Warm' else 72} hours</li>
                        <li>Premium email sent to customer with personalized insights</li>
                        <li>HubSpot Contact: <a href="https://app.hubspot.com/contacts/your-hub-id/contact/{submission.hubspot_contact_id or 'pending'}">View Contact</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_internal_notification_plain(submission, score_breakdown):
    """Generate plain text content for internal notification email"""
    
    plain = f"""
NEW ROI CALCULATOR LEAD
Score: {submission.lead_score}/150 | Tier: {submission.tier}

LEAD SNAPSHOT:
Name: {submission.first_name} {submission.last_name}
Email: {submission.email}
Business: {submission.business_name}
Industry: {submission.industry}

KEY METRICS:
Monthly Revenue: ${submission.monthly_revenue:,.0f}
Business Stage: {submission.business_stage}
Conversion Rate: {submission.conversion_rate}%
Cart Abandonment: {submission.cart_abandonment_rate}%

LEAD SCORE BREAKDOWN:
Demographic: {score_breakdown['demographic']}/60 (Revenue tier, business stage)
Behavioral: {score_breakdown['behavioral']}/52 (Form completion, engagement)
Fit: {score_breakdown['fit']}/38 (Industry match, challenge alignment)
Total: {submission.lead_score}/150 (Tier: {submission.tier})

NEXT STEPS:
- Follow up within: {1 if submission.tier == 'Hot' else 24 if submission.tier == 'Warm' else 72} hours
- Premium email sent to customer with personalized insights
- HubSpot Contact: https://app.hubspot.com/contacts/your-hub-id/contact/{submission.hubspot_contact_id or 'pending'}
    """
    
    return plain

