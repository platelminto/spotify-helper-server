from flask import url_for

from app import db
import os
import requests

redirect_uri = 'http://localhost:8888/callback'
get_token_url = 'https://accounts.spotify.com/api/token'
client_id = os.getenv('SPOTIFY_CLIENT_ID')
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
    id = db.Column(db.Integer, primary_key=True)
    refresh_token = db.Column(db.String(64))
    token = db.relationship('Token', uselist=False, back_populates="user")

    def to_dict(self):
        return {
            'id': self.id,
            'refresh_token': self.refresh_token,
            'access_token': self.token.access_token if self.token is not None else None,
            'expiry': self.token.expiry if self.token is not None else None
        }

    def from_dict(self, data):
        for field in ['id', 'refresh_token']:
            if field in data:
                setattr(self, field, data[field])

    def __repr__(self):
        return '<User {} with refresh token {}>'.format(self.id, self.refresh_token)

    @staticmethod
    def get_access_info(auth_code):
        payload = {'grant_type': 'authorization_code', 'code': auth_code,
                   'redirect_uri': redirect_uri, 'client_id': client_id,
                   'client_secret': client_secret}

        r = requests.post(get_token_url, data=payload)
        return r


class Token(PaginatedAPIMixin, db.Model):
    access_token = db.Column(db.String(64), primary_key=True)
    expiry = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", back_populates="token")

    def __repr__(self):
        return '<Access token for {} expires {}>'.format(self.owner_id, self.expiry)


class TempUser(PaginatedAPIMixin, db.Model):
    ip_address = db.Column(db.String(32), primary_key=True)

    def __repr__(self):
        return '<Temporary user with IP ()>'.format(self.ip_address)

    def to_dict(self):
        return {
            'ip_address': self.ip_address
        }

    def from_dict(self, data):
        if 'ip_address' in data:
            self.ip_address = data['ip_address']