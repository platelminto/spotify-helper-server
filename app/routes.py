import uuid

from flask import request, redirect, url_for

from app import app, db
from app.errors import bad_request
from app.models import User, RegisteringUser


@app.route('/')
@app.route('/index')
def index():
    return ""


# Called by Spotify auth service
@app.route('/users/registering', methods=['GET'])
def create_registering_user():
    data = request.args.to_dict() or {}
    if 'error' in data:
        return bad_request('Error: ' + data['error'])
    try:
        user_uuid = uuid.UUID(data['state']).hex # Check for UUID validity
    except (ValueError, KeyError):
        return bad_request('Must include correct UUID in the state')
    RegisteringUser.query.filter_by(uuid=user_uuid).delete()
    db.session.commit()
    registering_user = RegisteringUser(uuid=user_uuid, auth_code=data['code'])
    db.session.add(registering_user)
    db.session.commit()
    return redirect(url_for('static', filename='close.html'))


@app.route('/users/complete', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if 'uuid' not in data:
        return bad_request('Must include UUID')
    registering_user_query = RegisteringUser.query.filter_by(uuid=uuid.UUID(data['uuid']).hex)
    if registering_user_query.count() == 0:
        return bad_request('Given UUID is not currently registering')

    registered_user = registering_user_query.first()
    response = User.get_access_info(registered_user.auth_code)
    registering_user_query.delete()
    User.query.filter_by(uuid=uuid.UUID(data['uuid']).hex).delete() # If we are re-registering, remove previous
    db.session.commit()
    if response.status_code < 400:
        db.session.add(User(uuid=registered_user.uuid))
        db.session.commit()
    return response.json(), response.status_code


@app.route('/users/refresh', methods=['POST'])
def refresh_tokens():
    data = request.get_json() or {}
    if 'uuid' not in data:
        return bad_request('Must include UUID')
    if User.query.filter_by(uuid=uuid.UUID(data['uuid']).hex).count() == 0:
        return bad_request('Given UUID isn\'t registered')

    response = User.get_refresh_info(data)
    return response.json(), response.status_code
