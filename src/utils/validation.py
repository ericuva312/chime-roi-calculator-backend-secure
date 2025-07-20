"""
Form validation system for ROI calculator submissions
Implements comprehensive validation for all form fields
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

def validate_percentage(value, field_name):
    """Validate percentage values (0-100 with 2 decimals)"""
    try:
        pct_value = float(value)
        if pct_value < 0 or pct_value > 100:
            raise ValidationError(f"{field_name} must be between 0 and 100")
        
        # Check for max 2 decimal places
        decimal_value = Decimal(str(value))
        if decimal_value.as_tuple().exponent < -2:
            raise ValidationError(f"{field_name} can have maximum 2 decimal places")
        
        return pct_value
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError(f"{field_name} must be a valid percentage")

def validate_email(email):
    """Validate email address"""
    if not email:
        raise ValidationError("Email is required")
    
    email = email.strip().lower()
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    if len(email) > 254:  # RFC 5321 limit
        raise ValidationError("Email address too long")
    
    return email

def validate_alphabetic(value, field_name):
    """Validate alphabetic names (letters, spaces, hyphens, apostrophes)"""
    if not value:
        raise ValidationError(f"{field_name} is required")
    
    value = value.strip()
    
    if len(value) < 2:
        raise ValidationError(f"{field_name} must be at least 2 characters")
    
    if len(value) > 50:
        raise ValidationError(f"{field_name} must be less than 50 characters")
    
    # Allow letters, spaces, hyphens, and apostrophes
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
    
    # Add protocol if missing
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website
    
    try:
        parsed = urlparse(website)
        if not parsed.netloc:
            raise ValidationError("Invalid website URL")
        
        # Basic domain validation
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
    
    # Remove common formatting characters
    cleaned_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    
    # Check if it's all digits (after cleaning)
    if not cleaned_phone.isdigit():
        raise ValidationError("Phone number can only contain digits and formatting characters")
    
    # Check length (7-15 digits is reasonable for international numbers)
    if len(cleaned_phone) < 7 or len(cleaned_phone) > 15:
        raise ValidationError("Phone number must be between 7 and 15 digits")
    
    return phone  # Return original format

def validate_dropdown_choice(value, field_name, valid_choices):
    """Validate dropdown selections"""
    if not value:
        raise ValidationError(f"{field_name} is required")
    
    if value not in valid_choices:
        raise ValidationError(f"Invalid {field_name} selection")
    
    return value

def validate_roi_calculation(data):
    """
    Validate ROI calculation data (minimal validation for calculation only)
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
    
    # Validate required numeric fields for calculation
    try:
        cleaned_data['monthly_revenue'] = validate_positive_number(
            data.get('monthly_revenue'), 'Monthly revenue'
        )
    except ValidationError as e:
        errors['monthly_revenue'] = str(e)
    
    try:
        cleaned_data['average_order_value'] = validate_positive_number(
            data.get('average_order_value'), 'Average order value'
        )
    except ValidationError as e:
        errors['average_order_value'] = str(e)
    
    try:
        cleaned_data['monthly_orders'] = validate_positive_integer(
            data.get('monthly_orders'), 'Monthly orders'
        )
    except ValidationError as e:
        errors['monthly_orders'] = str(e)
    
    try:
        cleaned_data['manual_hours_per_week'] = validate_positive_integer(
            data.get('manual_hours_per_week'), 'Manual hours per week'
        )
    except ValidationError as e:
        errors['manual_hours_per_week'] = str(e)
    
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
    
    # Validate challenges (optional for calculation)
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
        # Calculate conversion rate from existing data if possible
        if 'monthly_revenue' in cleaned_data and 'average_order_value' in cleaned_data:
            monthly_orders = cleaned_data.get('monthly_orders', 0)
            if monthly_orders > 0:
                # Estimate conversion rate based on industry averages
                industry = cleaned_data.get('industry', 'Other')
                if industry == 'Electronics':
                    cleaned_data['conversion_rate'] = 2.5  # Industry average
                elif industry == 'Fashion & Apparel':
                    cleaned_data['conversion_rate'] = 2.8
                else:
                    cleaned_data['conversion_rate'] = 2.0  # General average
            else:
                cleaned_data['conversion_rate'] = 2.0
        else:
            cleaned_data['conversion_rate'] = 2.0
    
    if 'cart_abandonment_rate' not in cleaned_data:
        # Use industry average cart abandonment rate
        cleaned_data['cart_abandonment_rate'] = 70.0  # Industry average
    
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
    
    # Business name - use company field if business_name not provided
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

