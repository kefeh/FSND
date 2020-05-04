import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  

  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  @app.after_request
  def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, PATCH, DELETE, OPTIONS')
    return response


  @app.route('/categories', methods=['GET'])
  def get_categories():
    categories = Category.query.all()
    result = {}
    for category in categories:
      result[category.id] = category.type

    return jsonify({'categories': result})
  

  def question_get_return(page, category_id=None, search_term=None):
    """
    Generic question search and formatter, that always return the first page of the results if no page number is specified
    """
    num_quest = 10
    if category_id:
      # here we are handling the case where we need questions on a particular category
      questions = Question.query.filter(Question.category==category_id).paginate(max_per_page=num_quest, page=page)
      category = Category.query.get(category_id)
      category_type = category.type
    elif search_term:
      # Here we are handling the search for a question not case sensitive search if the term is a substring of the question
      questions = Question.query.filter(func.lower(Question.question).contains(search_term.lower())).paginate(max_per_page=num_quest, page=page)
      category_type = ' '
    else:
      questions = Question.query.paginate(max_per_page=num_quest, page=page)
      category_type = ' '

    questions = [dict(question.format()) for question in questions.items]
    categories = Category.query.all()
    category_result = {}
    for category in categories:
      category_result[category.id] = category.type 

    result = {"questions": questions, "total_questions": len(questions), "current_category": category_type, 'categories': category_result}

    return result


  @app.route('/questions', methods=['GET'])
  def get_questions():
    page = request.args.get('page', 1, type=int)

    result = question_get_return(page)

    if len(result) == 0:
      abort(400)

    return jsonify(result)


  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.get(question_id)
    if not question:
      abort(405)
    try:
      question.delete()
    except Exception:
      abort(500)
    return jsonify({'message': "Delete Successful"})

 
  @app.route('/questions', methods=['POST'])
  def add_question():
    data = request.json
    if (data.get('question') == '') or (data.get('answer') or data.get('category') or data.get('difficulty')):
      abort(422)
    try:
      question = Question(question=data.get('question', ''), answer=data.get('answer'), category=data.get('category'), difficulty=data.get('difficulty'))
      question.insert()
    except Exception:
      abort(422)

    return jsonify({'message': 'success'})


  @app.route('/questions/search', methods=['POST'])
  def search_question():
    try:
      search_term = request.json.get('searchTerm', '')
      result = question_get_return(1, search_term=search_term)
    except Exception:
      abort(422)

    return jsonify(result)


  @app.route("/categories/<int:category_id>/questions", methods=['GET'])
  def get_question_per_category(category_id):
    result = question_get_return(1, category_id=category_id)
    if not result:
      abort(405)

    return jsonify(result)


  @app.route('/quizzes', methods=['POST'])
  def quizes():
    data = request.json
    previous_questions_list = data.get('previous_questions')
    quiz_category = data.get('quiz_category')
    if not previous_questions_list or not quiz_category:
      abort(422)

    question = Question.query.filter(Question.category==quiz_category.get('id')).filter(Question.id.notin_(previous_questions_list)).order_by(func.random()).limit(1).all()

    if question:
      question = dict(question[0].format())
    return jsonify({'question': question})


  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'error': 404,
      'message': 'Not Found'
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'error': 422,
      'message': 'Unprocessable'
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'error': 400,
      'message': 'Bad Request'
    }), 400

  @app.errorhandler(500)
  def sever_error(error):
    return jsonify({
      'error': 500,
      'message': 'Sever Error'
    }), 500
  
  return app

    