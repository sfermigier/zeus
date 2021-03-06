import zeus
import requests

from flask import current_app, redirect, request, session, url_for
from flask.views import MethodView
from oauth2client.client import OAuth2WebServerFlow

from zeus.config import db
from zeus.constants import GITHUB_AUTH_URI, GITHUB_TOKEN_URI
from zeus.models import Identity, User


def get_auth_flow(redirect_uri=None, scopes=('user:email', )):
    # XXX(dcramer): we have to generate this each request because oauth2client
    # doesn't want you to set redirect_uri as part of the request, which causes
    # a lot of runtime issues.
    return OAuth2WebServerFlow(
        client_id=current_app.config['GITHUB_CLIENT_ID'],
        client_secret=current_app.config['GITHUB_CLIENT_SECRET'],
        scope=','.join(scopes),
        redirect_uri=redirect_uri,
        user_agent='zeus/{0}'.format(
            zeus.VERSION,
        ),
        auth_uri=GITHUB_AUTH_URI,
        token_uri=GITHUB_TOKEN_URI,
    )


class GitHubAuthView(MethodView):
    def __init__(self, authorized_url, scopes=('user:email', )):
        self.authorized_url = authorized_url
        self.scopes = scopes
        super(GitHubAuthView, self).__init__()

    def get(self):
        redirect_uri = url_for(self.authorized_url, _external=True)
        flow = get_auth_flow(redirect_uri=redirect_uri, scopes=self.scopes)
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)


class GitHubCompleteView(MethodView):
    def __init__(self, complete_url):
        self.complete_url = complete_url
        super(GitHubCompleteView, self).__init__()

    def get(self):
        redirect_uri = request.url
        flow = get_auth_flow(redirect_uri=redirect_uri)
        response = flow.step2_exchange(request.args['code'])

        scopes = response.token_response['scope'].split(',')

        if 'user:email' not in scopes:
            raise NotImplementedError

        identity_config = {
            'access_token': response.access_token,
            'refresh_token': response.refresh_token,
            'scopes': scopes,
        }

        # fetch user details
        response = requests.get(
            'https://api.github.com/user', params={'access_token': identity_config['access_token']}
        )
        response.raise_for_status()
        user_data = response.json()

        with db.session.begin_nested():
            existing_identity = Identity.query.filter(
                Identity.external_id == str(user_data['id']),
                Identity.provider == 'github',
            ).first()
            if not existing_identity:
                user = User(
                    email=user_data['email'],
                )
                db.session.add(user)
                identity = Identity(
                    user=user,
                    external_id=str(user_data['id']),
                    provider='github',
                    config=identity_config,
                )
                db.session.add(identity)
            else:
                user = User.query.filter(
                    Identity.external_id == str(user_data['id']),
                    Identity.provider == 'github',
                    Identity.user_id == User.id,
                ).first()
                Identity.query.filter(
                    Identity.external_id == str(user_data['id']),
                    Identity.provider == 'github',
                ).update({
                    'config': identity_config,
                })

        session['uid'] = user.id.hex

        return redirect(url_for(self.complete_url))
