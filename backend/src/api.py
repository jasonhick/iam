import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES

@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.all()
        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in drinks]
        }), 200
    except:
        abort(500)



@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.all()
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        }), 200
    except:
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    try:
        # Get drink data from request body
        body = request.get_json()
        
        # Create new drink
        new_drink = Drink(
            title=body.get('title'),
            recipe=json.dumps(body.get('recipe'))
        )
        
        # Insert drink into database
        new_drink.insert()
        
        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        }), 200
        
    except Exception as e:
        abort(422)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    try:
        # Get drink by id
        drink = Drink.query.get(id)
        
        # Check if drink exists
        if drink is None:
            abort(404)
            
        # Get drink data from request body
        body = request.get_json()
        
        # Update drink fields if they exist in request
        if 'title' in body:
            drink.title = body['title']
        if 'recipe' in body:
            drink.recipe = json.dumps(body['recipe'])
            
        # Update drink in database
        drink.update()
        
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
        
    except Exception as e:
        abort(422)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    try:
        # Get drink by id
        drink = Drink.query.get(id)
        
        # Check if drink exists
        if drink is None:
            abort(404)
            
        # Delete the drink
        drink.delete()
        
        return jsonify({
            'success': True,
            'delete': id
        }), 200
        
    except Exception as e:
        abort(422)


# Error Handling
# Error status code to message mapping
ERROR_MESSAGES = {
    400: "bad request",
    401: "unauthorized", 
    403: "forbidden",
    404: "resource not found",
    405: "method not allowed",
    422: "unprocessable",
    500: "internal server error"
}

# Generic error handler for common HTTP errors
def error_handler(error_code):
    @app.errorhandler(error_code)
    def handler(error):
        return jsonify({
            "success": False,
            "error": error_code,
            "message": ERROR_MESSAGES[error_code]
        }), error_code

# Register error handlers for all defined error codes
for error_code in ERROR_MESSAGES:
    error_handler(error_code)


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
