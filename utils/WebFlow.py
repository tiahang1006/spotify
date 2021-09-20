import urllib.parse as urlparse

class WebFlow:
    def __init__(self, base_url=''):
        self.base_url = base_url

    def generate_auth_url(self, endpoint='/authorize', **kwargs):
        url = self.base_url + endpoint + "?"
        for k in kwargs.keys():
            url += "&" + k + "=" + kwargs[k]
        return url

    def authorization_flow(self, endpoint='/authorize', token_key='code', attrs_to_save=[], **kwargs):
        url = self.generate_auth_url(endpoint, **kwargs)
        redirect_url = urlparse.urlparse(
            input(url + '\nGo to the above URL and then paste the URL you were redirected to:\n').strip().replace("#", "?"))
        try:
            self.auth_token = urlparse.parse_qs(redirect_url.query)[token_key][0]
            for a in attrs_to_save:
                s = urlparse.parse_qs(redirect_url.query)[a]
                setattr(self, a, s)
        except Exception as err:
            print('error parsing token:', err, redirect_url)
            self.auth_token = redirect_url
        return self.auth_token

    def refreshAccessTokens(self, auth_code='', redirect_uri=''):
        0

