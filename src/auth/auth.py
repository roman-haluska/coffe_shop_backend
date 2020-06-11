import json, requests
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen

AUTH0_DOMAIN = 'coffeshop.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'https://coffeshop/'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header
def get_token_auth_header():
    if 'Authorization' not in request.headers:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization is expected!'
        }, 401)
    auth_header = request.headers['Authorization']
    bearer_header = auth_header.split(' ')
    if (bearer_header[0].lower() != 'bearer'):
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must have atribute "Bearer"!'
        }, 401)
    elif (len(bearer_header) > 2):
        raise AuthError({
            'code': 'invalid_header',
            'description': 'For authorization please use bearer token!'
        }, 401)
    elif (len(bearer_header) == 1):
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found!'
        }, 401)
    return bearer_header[1]

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT!'
        }, 400)
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found!'
        }, 403)
    return True

def verify_decode_jwt(token):
    r = requests.get(url='http://coffeshop.eu.auth0.com/.well-known/jwks.json')
    print(r.json())
    jwks = r.json()
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''

def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                jwt = get_token_auth_header()
                payload = verify_decode_jwt(jwt)
                check_permissions(permission, payload)
            except Exception as e:
                abort(401)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator