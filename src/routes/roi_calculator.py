"""
ROI Calculator API Routes
Handles form submission, validation, scoring, and processing
"""

from flask import Blueprint, request, jsonify
import json
from uuid import uuid4
from datetime import datetime
from sqlalchemy import text

from src.models.roi_submission import ROISubmission
from src.models.user import db
from src.utils.validation import validate_roi_submission, validate_roi_calculation, ValidationError
from src.utils.lead_scoring import calculate_lead_score
from src.services.email_service import send_confirmation_email, send_internal_notification
from src.services.hubspot_service_fixed_final import HubSpotServiceFixed

roi_bp = Blueprint('roi_calculator', __name__)

@roi_bp.route('/calculate', methods=['POST'])
def calculate_roi():
    """
    Calculate real-time ROI projections without storing data
    Used for live calculations as user types
    """
    try:
        data = request.get_json()
        
        # Use proper validation for calculation
        try:
            validated_data = validate_roi_calculation(data)
        except ValidationError as e:
            if isinstance(e.args[0], dict):
                return jsonify({'error': 'Validation failed', 'field_errors': e.args[0]}), 400
            else:
                return jsonify({'error': str(e)}), 400
        
        monthly_revenue = validated_data['monthly_revenue']
        
        # Calculate projections
        projections = {
            'conservative': {
                'monthly_revenue': monthly_revenue * 1.10,
                'monthly_increase': monthly_revenue * 0.10,
                'annual_benefit': monthly_revenue * 0.10 * 12,
                'roi_percentage': 150,
                'break_even_months': 6,
                'conversion_improvement': '5-10%',
                'cost_reduction': '15-20%'
            },
            'expected': {
                'monthly_revenue': monthly_revenue * 1.30,
                'monthly_increase': monthly_revenue * 0.30,
                'annual_benefit': monthly_revenue * 0.30 * 12,
                'roi_percentage': 400,
                'break_even_months': 5,
                'conversion_improvement': '15-25%',
                'cost_reduction': '25-35%'
            },
            'optimistic': {
                'monthly_revenue': monthly_revenue * 1.50,
                'monthly_increase': monthly_revenue * 0.50,
                'annual_benefit': monthly_revenue * 0.50 * 12,
                'roi_percentage': 700,
                'break_even_months': 4,
                'conversion_improvement': '30-50%',
                'cost_reduction': '40-60%'
            }
        }
        
        return jsonify({
            'status': 'success',
            'projections': projections
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@roi_bp.route('/submit', methods=['POST'])
def submit_roi_calculation():
    """
    Process complete ROI calculator submission
    Validates, scores, stores, and triggers automation
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Validate submission data
        try:
            cleaned_data = validate_roi_submission(data)
        except ValidationError as e:
            if isinstance(e.args[0], dict):
                return jsonify({'error': 'Validation failed', 'field_errors': e.args[0]}), 400
            else:
                return jsonify({'error': str(e)}), 400
        
        # Calculate lead score
        lead_score, tier, score_breakdown = calculate_lead_score(cleaned_data)
        
        # Create submission record
        submission = ROISubmission(
            submission_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            ip_address=client_ip,
            monthly_revenue=cleaned_data['monthly_revenue'],
            average_order_value=cleaned_data['average_order_value'],
            monthly_orders=cleaned_data['monthly_orders'],
            industry=cleaned_data['industry'],
            conversion_rate=cleaned_data['conversion_rate'],
            cart_abandonment_rate=cleaned_data['cart_abandonment_rate'],
            monthly_ad_spend=cleaned_data.get('monthly_ad_spend'),
            manual_hours_per_week=cleaned_data['manual_hours_per_week'],
            business_stage=cleaned_data['business_stage'],
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            email=cleaned_data['email'],
            business_name=cleaned_data['business_name'],
            website=cleaned_data.get('website'),
            phone=cleaned_data.get('phone'),
            lead_score=lead_score,
            tier=tier
        )
        
        # Set challenges
        submission.set_challenges_list(cleaned_data.get('challenges', cleaned_data.get('biggest_challenges', [])))
        
        # Save to database
        db.session.add(submission)
        db.session.commit()
        
        # Calculate projections for response
        projections = submission.calculate_projections()
        
        # Trigger async processes (email and HubSpot sync)
        try:
            # Send confirmation email
            email_sent = send_confirmation_email(submission, projections)
            if email_sent:
                submission.email_sent = True
            
            # Send internal notification
            send_internal_notification(submission, score_breakdown)
            
            # Sync to HubSpot
            hubspot_service = HubSpotServiceFixed()
            
            # Create/update contact
            contact_result = hubspot_service.upsert_contact(
                cleaned_data, 
                lead_score, 
                tier
            )
            
            hubspot_success = False
            if contact_result['success']:
                submission.hubspot_contact_id = contact_result['contact_id']
                
                # Create deal
                deal_result = hubspot_service.create_deal(
                    cleaned_data,
                    contact_result['contact_id'],
                    lead_score
                )
                
                if deal_result['success']:
                    submission.hubspot_deal_id = deal_result['deal_id']
                    hubspot_success = True
            
            if hubspot_success:
                submission.hubspot_synced = True
            
            # Update submission with sync status
            db.session.commit()
            
        except Exception as async_error:
            # Log error but don't fail the submission
            print(f"Async processing error: {async_error}")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'submission_id': submission.submission_id,
            'lead_score': lead_score,
            'tier': tier,
            'projections': projections,
            'message': f'Thank you, {submission.first_name}! Your custom growth blueprint is on the way.'
        })
        
    except Exception as e:
        # Rollback database transaction
        db.session.rollback()
        return jsonify({'error': f'Submission processing failed: {str(e)}'}), 500

@roi_bp.route('/status/<submission_id>', methods=['GET'])
def get_submission_status(submission_id):
    """
    Get status of a submission (for debugging/monitoring)
    """
    try:
        # Add debugging information
        print(f"🔍 Looking for submission: {submission_id}")
        
        # Query the submission
        submission = ROISubmission.query.filter_by(submission_id=submission_id).first()
        
        if not submission:
            # Add more debugging
            total_submissions = ROISubmission.query.count()
            print(f"🔍 Submission not found. Total submissions in DB: {total_submissions}")
            
            # List recent submissions for debugging
            recent_submissions = ROISubmission.query.order_by(ROISubmission.created_at.desc()).limit(5).all()
            recent_ids = [s.submission_id for s in recent_submissions]
            print(f"🔍 Recent submission IDs: {recent_ids}")
            
            return jsonify({
                'error': 'Submission not found',
                'debug_info': {
                    'requested_id': submission_id,
                    'total_submissions': total_submissions,
                    'recent_submissions': recent_ids
                }
            }), 404
        
        return jsonify({
            'submission_id': submission.submission_id,
            'status': {
                'email_sent': submission.email_sent,
                'hubspot_synced': submission.hubspot_synced,
                'hubspot_contact_id': submission.hubspot_contact_id,
                'hubspot_deal_id': submission.hubspot_deal_id
            },
            'lead_info': {
                'score': submission.lead_score,
                'tier': submission.tier,
                'business_name': submission.business_name
            },
            'created_at': submission.created_at.isoformat()
        })
        
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@roi_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

