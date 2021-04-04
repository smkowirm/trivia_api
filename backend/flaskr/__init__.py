import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  '''
  Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={r"/api/*": {"origins": "*"}})

  '''
  Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response


  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():
    categories = Category.query.all()
    formatted_categories = {category.id: category.type for category in categories}

    if len(formatted_categories)==0:
      abort(404)

    return jsonify({
      'success': True, 
      'categories': formatted_categories,
      'total_categories': len(formatted_categories)
    })

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
  @app.route('/questions', methods=['GET'])
  def get_questions():
    page = request.args.get('page', 1, type=int)#get the pagenumber
    #define start question for page 
    start = (page - 1) *10
    #define end question for page 
    end = start + 10
    #get all question for page 
    questions = Question.query.all()
    #get all question for page
    formatted_questions = [question.format() for question in questions]

    #in case no questions found 
    if len(formatted_questions[start:end])==0:
      abort(404)

    #get all categories
    categories = Category.query.all()
    #format all categories
    formatted_categories = {category.id: category.type for category in categories}

    return jsonify({
      'success': True, 
      'questions': formatted_questions[start:end],
      'total_questions': len(formatted_questions),  
      'categories': formatted_categories,
      'current_category': None
    })

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 
  
  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<question_id>', methods=['DELETE'])
  def delete_question(question_id):
    # get the question by id
    question = Question.query.filter_by(id=question_id).one_or_none()
    # abort 404 if no question found
    if question is None:
        abort(404)
    # delete the question
    question.delete()
    # return success response
    return jsonify({
        'success': True,
        'deleted': question_id
    })
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
    # get data for new question 
    body = request.get_json()
    question=body.get('question')
    answer=body.get('answer')
    category=body.get('category')
    difficulty=body.get('difficulty')
    
    #if one of needed information is missing abort with bad request 
    if question is None or answer is None or category is None or difficulty is None:
      abort(400)
    else:
      #define new question with given information 
      question=Question(question=question,answer=answer,category=category,difficulty=difficulty)
      try:
        #insert question in database 
        question.insert()
        #get all questions 
        questions = Question.query.all()
        #format all questions 
        formatted_questions = [question.format() for question in questions]
        return jsonify({
          'success': True, 
          'questions': formatted_questions,
          'total_questions': len(formatted_questions)
        })
      except:
        abort(422)
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
    body = request.get_json()
    #get search_term from body
    search_term = body.get('searchTerm', None)
    if search_term: 
      #get questions matching the search_term 
      selection = Question.query.filter(Question.question.ilike('%{}%'.format(search_term)))
      #in case no match is found return not found 
      if not selection.all():
        abort(404)
      #format selected questions
      formatted_questions = [question.format() for question in selection]
      return jsonify({
        'success': True, 
        'questions': formatted_questions,
        'total_questions': len(selection.all()),
        'current_category': None
      })
    else: 
      abort(400)

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<category_id>/questions', methods=['GET'])
  def get_questions_bycategory(category_id):
    # get questions by category_id
    questions = Question.query.filter_by(category=category_id)
    # abort 404 if no questions found
    if questions is None:
        abort(404)
    # format questions 
    formatted_questions = [question.format() for question in questions]
    # return success response
    return jsonify({
        'success': True,
        'total_questions': len(formatted_questions),
        'questions': formatted_questions, 
        'current_category': category_id 
    })

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
  def get_quiz_questions():
        body = request.get_json()
        if not body:
            abort(400)
        previous_q = body['previous_questions']
        category_id = body['quiz_category']['id']
        if previous_q is not None:
            questions = Question.query.filter(
                Question.id.notin_(previous_q),
                Question.category == category_id).all()
            if not questions:
              next_question = False
            else: 
              next_question = random.choice(questions).format()     
        else:
            questions = Question.query.filter(
                Question.category == category_id).all()
            if not questions:
              abort(404)  
            else: 
              next_question = random.choice(questions).format()
        return jsonify({
            'success': True,
            'question': next_question
        })
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
        "success": False, 
        "error": 404,
        "message": "Not found"
        }), 404

  @app.errorhandler(422)
  def Unprocessable_Entity(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": "Unprocessable Entity"
        }), 422
  
  @app.errorhandler(400)
  def Bad_Request(error):
    return jsonify({
        "success": False, 
        "error": 400,
        "message": "Bad Request"
        }), 400

  @app.errorhandler(405)
  def Method_Not_Allowed(error):
    return jsonify({
        "success": False, 
        "error": 405,
        "message": "Method Not Allowed"
        }), 405

  @app.errorhandler(500)
  def Internal_Server_error(error):
    return jsonify({
        "success": False, 
        "error": 500,
        "message": "Internal Server error"
        }), 500

  return app

    