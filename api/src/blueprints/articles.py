from flask import Blueprint, jsonify, request
from src.db import DBManager
articles_bp = Blueprint('articles', __name__)
db = DBManager()
@articles_bp.route('/for-you', methods=['GET'])
def get_for_you():
    user_id = request.args.get('user_id', default=1, type=int)
    limit = request.args.get('limit', default=20, type=int)
    
    articles = db.get_for_you_articles(user_id, limit)
    
    # Enrich with topics
    for art in articles:
        art['topics'] = [t['name'] for t in db.get_article_topics(art['id'])]
        
    return jsonify(articles)
@articles_bp.route('/trending', methods=['GET'])
def get_trending():
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=20, type=int)
    
    articles = db.get_trending_articles(limit, user_id)
    
    # Enrich with topics
    for art in articles:
        art['topics'] = [t['name'] for t in db.get_article_topics(art['id'])]
        
    return jsonify(articles)
@articles_bp.route('/<article_id>', methods=['GET'])
def get_article(article_id):
    user_id = request.args.get('user_id', type=int)
    article = db.get_article_by_id(article_id, user_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
        
    article['topics'] = [t['name'] for t in db.get_article_topics(article_id)]
    return jsonify(article)
