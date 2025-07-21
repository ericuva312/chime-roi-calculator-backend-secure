"""
Form validation system for ROI calculator submissions - FIXED VERSION
Implements comprehensive validation with intelligent defaults for missing fields
"""

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_positive_number(value, field_name, allow_zero=False):
    """Validate positive numeric values"""
    try:
        num_value = float(value)
        if allow_zero and num_value < 0:
            raise ValidationError(f"{field_name} must be zero or positive")
        elif not allow_zero and num_value <= 0:
            raise ValidationError(f"{field_name} must be positive")
        return num_value
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number")

def validate_positive_integer(value, field_name):
    """Validate positive integer values"""
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValidationError(f"{field_name} must be a positive integer")
        return int_value
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")

def validate_email(email):
    """Validate email address"""
    if not email:
        raise ValidationError("Email is required")
    
    email = email.strip().lower()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    if len(email) > 254:
        raise ValidationError("Email address too long")
    
    return email

def validate_alphabetic(value, field_name):
    """Validate alphabetic names"""
    if not value:
        raise ValidationError(f"{field_name} is required")
    
    value = value.strip()
    
    if len(value) < 2:
        raise ValidationError(f"{field_name} must be at least 2 characters")
    
    if len(value) > 50:
        raise ValidationError(f"{field_name} must be less than 50 characters")
    
    if not re.match(r"^[a-zA-Z\s\-']+$", value):
        raise ValidationError(f"{field_name} can only contain letters, spaces, hyphens, and apostrophes")
    
    return value

def validate_website(website):
    """Validate website URL (optional field)"""
    if not website:
        return None
    
    website = website.strip()
    if not website:
        return None
    
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website
    
    try:
        parsed = urlparse(website)
        if not parsed.netloc:
            raise ValidationError("Invalid website URL")
        
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, parsed.netloc):
            raise ValidationError("Invalid domain name")
        
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            url += f"?{parsed.query}"
        if parsed.fragment:
            url += f"#{parsed.fragment}"
        
        return url
    except Exception:
        raise ValidationError("Invalid website URL format")

def validate_phone(phone):
    """Validate phone number (optional field)"""
    if not phone:
        return None
    
    phone = phone.strip()
    if not phone:
        return None
    
    cleaned_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    
    if not cleaned_phone.isdigit():
        raise ValidationError("Phone number can only contain digits and formatting characters")
    
    if len(cleaned_phone) < 7 or len(cleaned_phone) > 15:
        raise ValidationError("Phone number must be between 7 and 15 digits")
    
    return phone

def validate_dropdown_choice(value, field_name, valid_choices):
    """Validate dropdown selections"""
    if not value:
        raise ValidationError(f"{field_name} is required")
    
    if value not in valid_choices:
        raise ValidationError(f"Invalid {field_name} selection")
    
    return value

def validate_roi_calculation(data):
    """
    Validate ROI calculation data with intelligent defaults for missing fields
    Returns: cleaned_data dict
    Raises: ValidationError with specific field errors
    """
    errors = {}
    cleaned_data = {}
    
    # Define valid choices
    VALID_INDUSTRIES = [
        'Fashion & Apparel', 'Electronics', 'Health & Wellness', 'Home & Garden',
        'Beauty & Cosmetics', 'Food & Beverage', 'Pet Products', 'Sports & Fitness',
        'Automotive', 'Books & Media', 'Toys & Games', 'Other'
    ]
    
    VALID_BUSINESS_STAGES = ['Startup', 'Growth', 'Established', 'Mature']
    
    VALID_CHALLENGES = [
        'Manual processes', 'Low conversion rates', 'High cart abandonment',
        'Poor customer retention', 'Inventory management', 'Marketing inefficiency',
        'Customer service issues', 'Data analysis challenges', 'Other'
    ]
    
    # Validate required monthly revenue
    try:
        cleaned_data['monthly_revenue'] = validate_positive_number(
            data.get('monthly_revenue'), 'Monthly revenue'
        )
    except ValidationError as e:
        errors['monthly_revenue'] = str(e)
    
    # Get monthly revenue for calculations
    monthly_revenue = cleaned_data.get('monthly_revenue', 0)
    
    # Average order value - optional with intelligent defaults
    if data.get('average_order_value'):
        try:
            cleaned_data['average_order_value'] = validate_positive_number(
                data.get('average_order_value'), 'Average order value'
            )
        except ValidationError as e:
            errors['average_order_value'] = str(e)
    else:
        # Calculate intelligent default based on industry and revenue
        industry = data.get('industry', 'Other')
        if industry == 'Electronics':
            cleaned_data['average_order_value'] = max(100, monthly_revenue * 0.002)
        elif industry in ['Fashion & Apparel', 'Beauty & Cosmetics']:
            cleaned_data['average_order_value'] = max(50, monthly_revenue * 0.001)
        else:
            cleaned_data['average_order_value'] = max(75, monthly_revenue * 0.0015)
    
    # Monthly orders - optional with calculated default
    if data.get('monthly_orders'):
        try:
            cleaned_data['monthly_orders'] = validate_positive_integer(
                data.get('monthly_orders'), 'Monthly orders'
            )
        except ValidationError as e:
            errors['monthly_orders'] = str(e)
    else:
        # Calculate from revenue and average order value
        aov = cleaned_data.get('average_order_value', 100)
        cleaned_data['monthly_orders'] = max(10, int(monthly_revenue / aov))
    
    # Manual hours per week - optional with business stage default
    if data.get('manual_hours_per_week'):
        try:
            cleaned_data['manual_hours_per_week'] = validate_positive_integer(
                data.get('manual_hours_per_week'), 'Manual hours per week'
            )
        except ValidationError as e:
            errors['manual_hours_per_week'] = str(e)
    else:
        # Default based on business stage and revenue
        business_stage = data.get('business_stage', 'Growth')
        if business_stage == 'Startup':
            cleaned_data['manual_hours_per_week'] = max(10, int(monthly_revenue / 5000))
        elif business_stage == 'Growth':
            cleaned_data['manual_hours_per_week'] = max(15, int(monthly_revenue / 4000))
        elif business_stage == 'Established':
            cleaned_data['manual_hours_per_week'] = max(20, int(monthly_revenue / 3000))
        else:  # Mature
            cleaned_data['manual_hours_per_week'] = max(25, int(monthly_revenue / 2500))
    
    # Validate dropdown fields
    try:
        cleaned_data['industry'] = validate_dropdown_choice(
            data.get('industry'), 'Industry', VALID_INDUSTRIES
        )
    except ValidationError as e:
        errors['industry'] = str(e)
    
    try:
        cleaned_data['business_stage'] = validate_dropdown_choice(
            data.get('business_stage'), 'Business stage', VALID_BUSINESS_STAGES
        )
    except ValidationError as e:
        errors['business_stage'] = str(e)
    
    # Validate challenges (optional)
    challenges = data.get('challenges', [])
    if challenges:
        if isinstance(challenges, str):
            challenges = [challenges]
        
        if isinstance(challenges, list):
            for challenge in challenges:
                if challenge not in VALID_CHALLENGES:
                    errors['challenges'] = f'Invalid challenge: {challenge}'
                    break
            cleaned_data['challenges'] = challenges
        else:
            errors['challenges'] = 'Challenges must be a list'
    else:
        cleaned_data['challenges'] = []
    
    # If there are any errors, raise ValidationError with all errors
    if errors:
        raise ValidationError(errors)
    
    return cleaned_data

def validate_roi_submission(data):
    """
    Validate complete ROI submission data (includes contact info)
    Returns: cleaned_data dict
    Raises: ValidationError with specific field errors
    """
    errors = {}
    cleaned_data = {}
    
    # First validate calculation data
    try:
        calc_data = validate_roi_calculation(data)
        cleaned_data.update(calc_data)
    except ValidationError as e:
        if isinstance(e.args[0], dict):
            errors.update(e.args[0])
        else:
            errors['calculation'] = str(e)
    
    # Add default values for required fields that might be missing
    if 'conversion_rate' not in cleaned_data:
        industry = cleaned_data.get('industry', 'Other')
        if industry == 'Electronics':
            cleaned_data['conversion_rate'] = 2.5
        elif industry == 'Fashion & Apparel':
            cleaned_data['conversion_rate'] = 2.8
        else:
            cleaned_data['conversion_rate'] = 2.0
    
    if 'cart_abandonment_rate' not in cleaned_data:
        cleaned_data['cart_abandonment_rate'] = 70.0
    
    # Validate contact information
    try:
        cleaned_data['first_name'] = validate_alphabetic(
            data.get('first_name'), 'First name'
        )
    except ValidationError as e:
        errors['first_name'] = str(e)
    
    try:
        cleaned_data['last_name'] = validate_alphabetic(
            data.get('last_name'), 'Last name'
        )
    except ValidationError as e:
        errors['last_name'] = str(e)
    
    try:
        cleaned_data['email'] = validate_email(data.get('email'))
    except ValidationError as e:
        errors['email'] = str(e)
    
    # Business name
    business_name = data.get('business_name') or data.get('company', '').strip()
    if not business_name:
        errors['business_name'] = 'Business name is required'
    else:
        cleaned_data['business_name'] = business_name
    
    # Optional fields
    try:
        cleaned_data['website'] = validate_website(data.get('website'))
    except ValidationError as e:
        errors['website'] = str(e)
    
    try:
        cleaned_data['phone'] = validate_phone(data.get('phone'))
    except ValidationError as e:
        errors['phone'] = str(e)
    
    # If there are any errors, raise ValidationError with all errors
    if errors:
        raise ValidationError(errors)
    
    return cleaned_data

