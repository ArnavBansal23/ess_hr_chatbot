#auth_routes.py
from flask import Blueprint, request, jsonify

from auth import (
    hash_password,
    verify_password,
    validate_password,
    create_tokens
)
import logging
import mysql.connector
import re

# from flask_server_a import limiter


def create_auth_blueprint(db):
    auth_bp = Blueprint('auth', __name__)
    logger = logging.getLogger(__name__)

    @auth_bp.route('/signup', methods=['POST'])
    # @limiter.limit("5 per minute")
    def signup():
        if db is None:
            logger.error("DB not initialized")
            return jsonify({"error": "Database not connected"}), 500
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "Request body must be JSON"}), 400

            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            employee_code = data.get("employee_code")

            if not all([email, password, employee_code]):
                return jsonify({"error": "Email, password, and employee_code are required"}), 400

            # Validate email format
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(email_pattern, email):
                return jsonify({"error": "Invalid email format"}), 400

            try:
                employee_code = int(employee_code)
            except (ValueError, TypeError):
                return jsonify({"error": "Employee code must be a valid number"}), 400

            # Validate password strength
            is_valid, msg = validate_password(password)
            if not is_valid:
                return jsonify({"error": msg}), 400

            # Database operations
            conn = None
            cursor = None

            try:
                conn = db._engine.raw_connection()
                cursor = conn.cursor(dictionary=True)

                # Check if employee  int the company records
                cursor.execute("""
                        SELECT email, employee_code, role FROM employees
                        WHERE email = %s AND employee_code = %s
                    """, (email, employee_code))

                employee = cursor.fetchone()
                if not employee:
                    return jsonify(
                        {"error": "No matching employee found. Contact HR if you believe this is a mistake."}), 403

                role = employee["role"]

                # Check if the user already has a account

                cursor.execute("""
                                SELECT id, email, employee_code, is_active 
                                FROM users 
                                WHERE email = %s OR employee_code = %s
                            """, (email, employee_code))

                existing_user = cursor.fetchone()

                if existing_user:
                    if existing_user["email"] == email:
                        return jsonify({"error": "An account with this email already exists"}), 409
                    else:
                        return jsonify({"error": "An account with this employee code already exists"}), 409

                # Create new user account
                hashed_pw = hash_password(password)
                cursor.execute("""
                                INSERT INTO users (email, password_hash, employee_code, role, is_active)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (email, hashed_pw, employee_code, role, True))
                conn.commit()
                user_id = cursor.lastrowid

                access_token, refresh_token = create_tokens(
                    user_id=user_id,
                    role=role,
                    employee_code=employee_code,
                    email=email
                )

                logger.info(f"User signed up successfully: {email} (role={role})")

                return jsonify({
                    "message": "Account created successfully",
                    "user": {
                        "id": user_id,
                        "email": email,
                        "employee_code": employee_code,
                        "role": role
                    },
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }), 201

            except mysql.connector.Error as db_err:
                logger.error(f"MySQL error during signup: {db_err}")
                return jsonify({"error": "Database error"}), 500

            finally:
                if cursor: cursor.close()
                if conn: conn.close()

        except Exception as e:
            logger.exception(f"Signup failed: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @auth_bp.route('/login', methods=['POST'])
    # @limiter.limit("5 per minute")
    def login():
        if db is None:
            logger.error("DB not initialized")
            return jsonify({"error": "Database not connected"}), 500
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body must be JSON"}), 400

            email = data.get("email", "").strip().lower()
            password = data.get("password", "")

            if not all([email, password]):
                return jsonify({"error": "Email and password are required"}), 400

            # Validate email format
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(email_pattern, email):
                return jsonify({"error": "Invalid email format"}), 400

            # Database operations
            conn = None
            cursor = None

            try:
                conn = db._engine.raw_connection()
                cursor = conn.cursor(dictionary=True)

                cursor.execute("""
                                SELECT id, email, password_hash, role, employee_code, is_active
                                FROM users
                                WHERE email = %s
                            """, (email,))
                user = cursor.fetchone()

                if not user or not user["is_active"]:
                    return jsonify({"error": "Invalid credentials or account is inactive"}), 401

                if not verify_password(password, user["password_hash"]):
                    return jsonify({"error": "Invalid email or password"}), 401

                access_token, refresh_token = create_tokens(
                    user_id=user["id"],
                    email=user["email"],
                    role=user["role"],
                    employee_code=user["employee_code"]
                )

                logger.info(f"User logged in: {email}")

                return jsonify({
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "role": user["role"],
                        "employee_code": user["employee_code"]
                    }
                }), 200

            except mysql.connector.Error as db_err:
                logger.error(f"MySQL error during login: {db_err}")
                return jsonify({"error": "Database error"}), 500

            finally:
                if cursor: cursor.close()
                if conn: conn.close()

        except Exception as e:
            logger.exception(f"Login failed: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    return auth_bp