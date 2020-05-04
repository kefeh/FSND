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
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''

  @app.after_request
  def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, PATCH, DELETE, OPTIONS')
    return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():
    categories = Category.query.all()
    result = {}
    for category in categories:
      result[category.id] = category.type

    return jsonify({'categories': result})
  

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
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


  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.get(question_id)
    question.delete()
    return jsonify({'message': "Delete Successful"})

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def add_question():
    data = request.json
    question = Question(question=data.get('question', ''), answer=data.get('answer'), category=data.get('category'), difficulty=data.get('difficulty'))
    question.insert()

    return jsonify({'message': 'success'})

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_question():
    search_term = request.json.get('searchTerm', '')
    result = question_get_return(1, search_term=search_term)

    return jsonify(result)

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route("/categories/<int:category_id>/questions", methods=['GET'])
  def get_question_per_category(category_id):
    result = question_get_return(1, category_id=category_id)

    return jsonify(result)

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def quizes():
    data = request.json
    previous_questions_list = data.get('previous_questions')
    quiz_category = data.get('quiz_category')
    question = Question.query.filter(Question.category==quiz_category.get('id')).filter(Question.id.notin_(previous_questions_list)).order_by(func.random()).limit(1).all()

    if question:
      question = dict(question[0].format())
    return jsonify({'question': question})

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  
  return app

    