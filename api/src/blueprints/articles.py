from flask import Blueprint, jsonify, request
from src.db import DBManager
articles_bp = Blueprint('articles', __name__)
db = DBManager()
@articles_bp.route('/for-you', methods=['GET'])
def get_for_you():
    user_id = request.args.get('user_id', default=1, type=int)
    limit = request.args.get('limit', default=50, type=int)
    
    articles = db.get_for_you_articles(user_id, limit)
    
    # Enrich with topics
    for art in articles:
        art['topics'] = [t['name'] for t in db.get_article_topics(art['id'])]
        
    return jsonify(articles)
@articles_bp.route('/trending', methods=['GET'])
def get_trending():
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=50, type=int)
    
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
        
    all_topics = db.get_article_topics(article_id)
    article['topics'] = [t['name'] for t in all_topics if not t.get('is_global', False)]
    article['suggested_topics'] = [t['name'] for t in all_topics if t.get('is_global', False)]
    
    return jsonify(article)

def stringify_value(val):
    if isinstance(val, dict):
        return "\n\n".join([str(v) for v in val.values()])
    if isinstance(val, list):
        return "\n\n".join([str(v) for v in val])
    return str(val) if val is not None else ""

@articles_bp.route('/<article_id>/analyze', methods=['POST'])
def analyze_article(article_id):
    # 1. Get article from DB
    article = db.get_article_by_id(article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
        
    # 2. If already analyzed, return it
    if article.get('ai_analysis'):
        return jsonify({
            "ai_explanation": article['ai_explanation'],
            "ai_analysis": article['ai_analysis'],
            "ai_commentary": article['ai_commentary']
        })
        
    # 3. Else, trigger LLM
    from src.processor import ArticleProcessor
    from src.utils.llm import RateLimitError
    processor = ArticleProcessor()
    
    try:
        # We need the full content for better analysis
        analysis = processor.analyze_deep(article['content'])
        
        if analysis:
            # Clean analysis for frontend (ensure all values are strings)
            clean_analysis = {k: stringify_value(v) for k, v in analysis.items()}
            
            # 4. Save to DB
            db.update_article_analysis(article_id, clean_analysis)
            return jsonify(clean_analysis)
        else:
            return jsonify({"error": "Failed to analyze article"}), 500
    except RateLimitError as e:
        return jsonify({"error": str(e)}), 429
    except Exception as e:
        return jsonify({"error": f"Internal error: {e}"}), 500
