import threading
from flask import Blueprint, jsonify, request
from src.db import DBManager
from src.scorer import Scorer

users_bp = Blueprint('users', __name__)
db = DBManager()

def run_rescoring(user_id):
    try:
        # We create a new Scorer instance per thread to avoid connection pool issues if any
        s = Scorer()
        s.score_all_for_user(user_id)
    except Exception as e:
        print(f"❌ Background re-scoring error for user {user_id}: {e}")

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    user = db.get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify(user)

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Add stats
    stats = db.get_user_stats(user_id)
    user['stats'] = stats
    return jsonify(user)

@users_bp.route('/<int:user_id>/read/<string:article_id>', methods=['POST'])
def record_read(user_id, article_id):
    db.record_article_read(user_id, article_id)
    return jsonify({"status": "success"})

@users_bp.route('/<int:user_id>/interests', methods=['GET'])
def get_interests(user_id):
    interests = db.get_user_interests(user_id)
    return jsonify(interests)

@users_bp.route('/<int:user_id>/interests', methods=['POST'])
def add_interest(user_id):
    data = request.json
    interest_name = data.get('interest_name')
    if not interest_name:
        return jsonify({"error": "Interest name required"}), 400
    
    db.add_user_interest(user_id, interest_name)
    return jsonify({"status": "success", "interest_name": interest_name})

@users_bp.route('/<int:user_id>/interests/<string:interest_name>', methods=['DELETE'])
def remove_interest(user_id, interest_name):
    db.remove_user_interest(user_id, interest_name)
    return jsonify({"status": "success"})
