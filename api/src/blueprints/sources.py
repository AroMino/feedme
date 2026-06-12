from flask import Blueprint, jsonify, request
from src.db import DBManager

sources_bp = Blueprint('sources', __name__)
db = DBManager()

@sources_bp.route('', methods=['GET'])
def get_sources():
    sources = db.get_rss_sources()
    return jsonify(sources)

@sources_bp.route('', methods=['POST'])
def add_source():
    data = request.json
    if not data or not data.get('url') or not data.get('name'):
        return jsonify({"error": "Missing name or url"}), 400
    
    try:
        source_id = db.add_rss_source(data['name'], data['url'])
        return jsonify({"id": source_id, "message": "Source added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sources_bp.route('/<int:source_id>', methods=['DELETE'])
def delete_source(source_id):
    try:
        db.delete_rss_source(source_id)
        return jsonify({"message": "Source deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sources_bp.route('/<int:source_id>', methods=['PUT'])
def update_source(source_id):
    data = request.json
    if not data or not data.get('url') or not data.get('name'):
        return jsonify({"error": "Missing name or url"}), 400
    
    try:
        db.update_rss_source(source_id, data['name'], data['url'])
        return jsonify({"message": "Source updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
