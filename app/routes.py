import time

from app import app, db
from flask import jsonify, url_for, request
from app.models import User, TempUser, Token
from app.errors import bad_request


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/users/temp', methods=['GET'])
def get_temp_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = TempUser.to_collection_dict(TempUser.query, page, per_page, 'get_temp_users')
    return jsonify(data)


@app.route('/users/complete', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'get_users')
    return jsonify(data)


@app.route('/tokens', methods=['GET'])
def get_tokens():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Token.to_collection_dict(Token.query, page, per_page, 'get_tokens')
    return jsonify(data)


@app.route('/users/temp', methods=['POST'])
def create_temp_user():
    data = request.get_json() or {}
    if 'ip_address' not in data:
        return bad_request('Must include machine IP')
    if TempUser.query.filter_by(ip_address=data['ip_address']).first():
        return bad_request("Current IP already registering")
    temp_user = TempUser(ip_address=data['ip_address'])
    db.session.add(temp_user)
    db.session.commit()
    return jsonify(temp_user.to_dict())


@app.route('/users/complete', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    ip_address_query = TempUser.query.filter_by(ip_address=data['ip_address'])
    if 'auth_code' not in data or 'ip_address' not in data:
        return bad_request('Must include authorization code and IP')
    if ip_address_query.count() == 0:
        return bad_request('Given IP address is not currently authenticating')
    TempUser.query.filter_by(ip_address=data['ip_address']).delete()
    db.session.commit()
    response = User.get_access_info(data['auth_code'])
    # If there's an error, return the Spotify error directly
    if response.status_code >= 400:
        return response.text, response.status_code, response.headers.items()
    if response.status_code == 200:
        auth_info = response.json()
        user = User(refresh_token=auth_info['refresh_token'])
        db.session.add(user)
        db.session.commit()
        print(user.id)
        token = Token(owner_id=user.id,
                      access_token=auth_info['access_token'],
                      expiry=int(time.time())+int(auth_info['expires_in']))
        db.session.add(token)
        db.session.commit()
        return jsonify(user.to_dict())