#auth.py
from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Hash the user's password
def hash_password(password: str) -> str:
    return generate_password_hash(password, method='pbkdf2:sha256')

# Verify password on login
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, plain_password)


def create_tokens(user_id: int, role: str, employee_code: int, email: str):
    additional_claims = {
        "role": role,
        "employee_code": employee_code,
        "email": email
    }
    access_token = create_access_token(identity=str(user_id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user_id), additional_claims={"role": role})
    return access_token, refresh_token

# Get current user info from token
def get_current_user():
    """Helper to get current user data from JWT token"""
    try:
        claims = get_jwt()
        user_id = get_jwt_identity()
        return {
            "user_id": user_id,
            "role": claims.get("role", "employee"),
            "employee_code": claims.get("employee_code"),
            "email": claims.get("email")
        }
    except:
        return None


# Role-based decorator
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role", "employee")

            role_hierarchy = {
                'employee': 1,
                'manager': 2,
                'hr_admin': 3
            }

            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)

            if user_level < required_level:
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return wrapper

    return decorator


# Optional: Employee-specific access (user can only access their own data)
def employee_access_required(f):
    @wraps(f)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        user_role = claims.get("role", "employee")
        user_employee_code = claims.get("employee_code")

        # Get employee_code from request (URL param or JSON body)
        requested_employee_code = request.view_args.get('employee_code') or request.json.get('employee_code')

        # hr_admin and manager can access any employee data
        if user_role in ['hr_admin', 'manager']:
            return f(*args, **kwargs)

        # employee can only access their own data
        if user_role == 'employee' and str(user_employee_code) == str(requested_employee_code):
            return f(*args, **kwargs)

        return jsonify({"error": "Access denied"}), 403

    return wrapper


# Validate password strength (optional)
def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    return True, "Password is valid"