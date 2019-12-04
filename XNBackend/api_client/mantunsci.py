from typing import NamedTuple, Optional, Iterable, Tuple
from requests.auth import AuthBase
from requests import Session, Response, PreparedRequest
from datetime import datetime, timedelta
from contextlib import contextmanager
from urllib.parse import urljoin, parse_qs
from collections import OrderedDict
from hashlib import md5

AUTH_VERIFY_URL = './oauth/authverify2.as'
AUTH_TOKEN_URL = './oauth/token.as'
AUTH_REFRESH_URL = './oauth/refresh.as'


class MantunsciAuthError(Exception):
    def __init__(self, msg: str, req: object):
        self.msg = msg
        self.req = req

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.msg)


class MantunsciAuthTokenBase(NamedTuple):
    access_token: str
    refresh_token: str
    obtained_time: datetime
    refreshed_time: datetime
    expire_at: datetime


class MantunsciAuthToken(MantunsciAuthTokenBase):
    def is_expired(self, buffer_seconds: int = 30) -> bool:
        utcnow = datetime.utcnow() + timedelta(seconds=buffer_seconds)
        return self.expire_at <= utcnow

    @classmethod
    def from_response_data(
        cls,
        data: dict,
        obtained_time: Optional[datetime] = None
    ) -> 'MantunsciAuthToken':
        utcnow = datetime.utcnow()
        return cls(
            access_token=data['accessToken'],
            refresh_token=data['refreshToken'],
            obtained_time=obtained_time if obtained_time else utcnow,
            refreshed_time=utcnow,
            expire_at=utcnow + timedelta(seconds=data['expiresIn'])
        )


class MantunsciAuthBase(AuthBase):
    def __init__(
        self: 'MantunsciAuthBase',
        auth_url: str,
        username: str,
        password: str,
        app_key: str,
        app_secret: str,
        redirect_uri: str,
    ):
        self.base_url = auth_url
        self.username = username
        self.password = password
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri

    def save_token(self, token: MantunsciAuthToken, refreshing: bool):
        raise NotImplementedError

    def load_token(self) -> Optional[MantunsciAuthToken]:
        raise NotImplementedError

    @contextmanager
    def request_refresh_token(self):
        raise NotImplementedError

    def raise_for_invalid_resp(self, resp: Response):
        if resp.status_code != 200:
            raise MantunsciAuthError(
                str(resp.status_code),
                resp.request
            )
        elif not resp.json() or \
            not resp.json().get('success') or \
                not resp.json().get('code'):
            raise MantunsciAuthError(
                'unexpected body: ' + resp.text,
                resp.request
            )

    def obtain_code(self) -> str:
        with Session() as s:
            resp = s.post(
                cookies=None,
                allow_redirects=False,
                url=urljoin(self.base_url, AUTH_VERIFY_URL),
                data={
                    'response_type': 'code',
                    'client_id': self.app_key,
                    'redirect_uri': self.redirect_uri,
                    'uname': self.username,
                    'passwd': self.password
                }
            )
            self.raise_for_invalid_resp(resp)
            return resp.json()['code']

    def auth_params(self, param, refresh: bool) -> dict:
        params: OrderedDict = OrderedDict()
        params['client_id'] = self.app_key
        params['grant_type'] = 'refresh_token' \
            if refresh else 'authorization_code'
        params['redirect_uri'] = self.redirect_uri
        if refresh:
            params['refresh_token'] = param
        else:
            params['code'] = param
        content = ''.join(params.values()) + self.app_secret
        client_secret = md5(content.encode('utf-8'))
        params['client_secret'] = client_secret.hexdigest()
        return params

    def obtain_token(self, code: str) -> MantunsciAuthToken:
        data = self.auth_params(code, False)
        with Session() as s:
            resp = s.post(
                cookies=None,
                allow_redirects=False,
                url=urljoin(self.base_url, AUTH_TOKEN_URL),
                data=data
            )

            self.raise_for_invalid_resp(resp)
            token = resp.json()['data']
            return MantunsciAuthToken.from_response_data(token)

    def refresh_token(self) -> MantunsciAuthToken:
        last_token = self.load_token()
        assert last_token is not None
        data = self.auth_params(last_token.refresh_token, refresh=True)
        with Session() as s:
            resp = s.post(
                cookies=None,
                allow_redirects=False,
                url=urljoin(self.base_url, AUTH_REFRESH_URL),
                data=data
            )

            self.raise_for_invalid_resp(resp)
            token = resp.json()['data']
            return MantunsciAuthToken.from_response_data(
                token,
                last_token.obtained_time
            )

    def use_token(self):
        token = self.load_token()
        if token and token.is_expired():
            with self.request_refresh_token() as permitted:
                if permitted:
                    try:
                        token = self.refresh_token()
                        self.save_token(token, refreshing=True)
                    except MantunsciAuthError:
                        # TODO add logging here
                        token = None
                else:
                    # TODO add logging here
                    pass

        if not token:
            code = self.obtain_code()
            token = self.obtain_token(code)
            self.save_token(token, refreshing=False)

        return token

    def sign(self, data: Iterable[Tuple[str, str]]) -> str:
        sorted_data = sorted(
            data, key=lambda t: t[0]
        )
        content = ''.join(t[1] for t in sorted_data) + self.app_secret
        return md5(content.encode('utf-8')).hexdigest()

    def __call__(self, req: PreparedRequest) -> PreparedRequest:
        token = self.use_token()
        data = parse_qs(str(req.body))
        data.setdefault('client_id', [self.app_key, ])
        data.setdefault('access_token', [token.access_token, ])
        data.setdefault(
            'timestamp', [datetime.now().strftime('%Y%m%d%H%M%S'), ]
        )
        sign = self.sign((k, v[0]) for k, v in data.items())
        data['sign'] = [sign, ]
        req.prepare_body(
            data, None, None
        )
        return req


class MantunsciAuthInMemory(MantunsciAuthBase):
    def save_token(self, token: MantunsciAuthToken, refreshing: bool):
        self.token = token

    def load_token(self):
        if not hasattr(self, 'token'):
            self.token = None
        return self.token

    @contextmanager
    def request_refresh_token(self):
        yield True
