import base64

from flask import url_for

from app import db
import os
import requests

redirect_uri = 'https://platelminto.eu.pythonanywhere.com/users/registering'
get_token_url = 'https://accounts.spotify.com/api/token'
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class User(PaginatedAPIMixin, db.Model):
    uuid = db.Column(db.String(32), primary_key=True)

    def to_dict(self):
        return {
            'uuid': self.uuid,
        }

    def from_dict(self, data):
        if 'uuid' in data:
            self.uuid = data['uuid']

    def __repr__(self):
        return '<User {}>'.format(self.uuid)

    @staticmethod
    def get_access_info(auth_code):
        payload = {'grant_type': 'authorization_code', 'code': auth_code,
                   'redirect_uri': redirect_uri, 'client_id': client_id,
                   'client_secret': client_secret}

        r = requests.post(get_token_url, data=payload)
        return r

    @staticmethod
    def get_refresh_info(payload):
        headers = {'Authorization': 'Basic ' + base64.b64encode(
            (client_id + ':' + client_secret).encode('ascii')).decode('ascii')}
        r = requests.post('https://accounts.spotify.com/api/token', data=payload, headers=headers)
        return r


class RegisteringUser(PaginatedAPIMixin, db.Model):
    uuid = db.Column(db.String(32), primary_key=True)
    auth_code = db.Column(db.String(512))

    def __repr__(self):
        return '<Registering user {} with code {}>'.format(self.uuid, self.auth_code)

    def to_dict(self):
        return {
            'uuid': self.uuid,
            'auth_code': self.auth_code
        }

    def from_dict(self, data):
        for field in ['uuid', 'auth_code']:
            if field in data:
                setattr(self, field, data[field])
