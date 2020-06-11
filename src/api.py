import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from functools import wraps

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__,instance_relative_config=True)
setup_db(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
#db_drop_and_create_all()

# Set up CORS. Allow '*' for origins.
cors = CORS(app, resources={r"/*": {"origins": "*"}},
            supports_credentials=True)

# CORS Headers
# after_request decorator to set Access-Control-Allow
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers',
                            'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                            'GET, POST, PUT, PATCH, DELETE, OPTIONS')
    return response

# Create an public endpoint to handle GET requests for all available drinks
@app.route('/drinks', methods=['GET'])
def get_drinks_short():
    error = False
    try:
        drinks = Drink.query.all()
        formatted_drinks = [drink.short() for
                                    drink in drinks]
    except Exception as e:
        error = True
    finally:
        if error:
            abort(500)
        ##elif objectresult is None:
           ## abort(404)
        else:
            return jsonify({
                'success': True,
                'drinks': formatted_drinks
            })

# Create an public endpoint to handle GET requests for all available drinks
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_long(payload):
    error = False
    try:
        drinks = Drink.query.all()
        formatted_drinks = [drink.long() for
                                    drink in drinks]
    except Exception as e:
        error = True
    finally:
        if error:
            abort(500)
        elif len(formatted_drinks) == 0:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'drinks': formatted_drinks
            })


 # Create an endpoint to handle POST requests for create drink
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    error = False
    fieldErr = False
    try:
        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        id = body.get('id', None)
        # if search term is epmty
        if ((title is None) or (title == "") or (recipe is None)):
            fieldErr = True
        else:
            # add drink to db
            added_drink = Drink(title=title, recipe=json.dumps(recipe))
            added_drink.insert()
            formatted_drink = added_drink.long()

    except Exception as e:
        error = True
    finally:
        if error:
            abort(500)
        elif fieldErr:
            abort(400)
        elif formatted_drink is None:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'drinks': formatted_drink
            })

 # Create an endpoint to handle PATCH requests for update drink
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    error = False
    fieldErr = False
    notFound = False
    formatted_drink = []
    try:
        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        # if search term is epmty
        if ((title is None) or (title == "") or (recipe is None)):
            fieldErr = True
        else:
            # add drink to db
            load_drink = Drink.query.filter(Drink.id == id).one_or_none()
            if load_drink is None:
                notFound = True
            else:
                load_drink.title = title
                load_drink.recipe = json.dumps(recipe)
                load_drink.update()
                formatted_drink = load_drink.long()
    except Exception as e:
        error = True
    finally:
        if error:
            abort(500)
        elif fieldErr:
            abort(400)
        elif (formatted_drink is None) or notFound:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'drinks': formatted_drink
            })

# Create an endpoint to handle DELETE requests for delete drink
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    error = False
    drinkErr = False
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            drinkErr = True
        else:
            drink.delete()
    except Exception as e:
        error = True
    finally:
        if error:
            abort(500)
        elif drinkErr:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'delete': id
            })

## Error Handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Not found"
        }), 404

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable"
        }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad request"
        }), 400

@app.errorhandler(405)
def not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "Method not allowed"
        }), 405

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal server error"
        }), 500

## error handler for AuthError
@app.errorhandler(401)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": error.description
        }), 401

@app.errorhandler(403)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Forbidden"
        }), 403
