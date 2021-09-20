import requests
from numbers import Number
from requests_oauthlib import OAuth1Session, OAuth1, OAuth2 as oa2
# from bs4 import BeautifulSoup
import urllib3
# from OAuth2 import OAuth2

zero_depth_bases = (str, bytes, Number, range, bytearray)

class Result:
    def __getitem__(self, item):
        return getattr(self, item)

def result_helper(data):
    if any([isinstance(data, x) for x in zero_depth_bases]):
        return data
    elif isinstance(data, list):
        return [result_helper(x) for x in data]
    elif isinstance(data, dict):
        try:
            obj = Result()
            for key, value in data.items():
                setattr(obj, key, result_helper(value))
        except Exception as err:
            print('error processing result', err, obj)
    else:
        return data
    return obj


class apPy:
    class endpoint:
        def __init__(self, parent, endpoint, args, params, include_query_markers, protocol='GET', header={}, oauth=False):
            assert isinstance(endpoint, str), 'endpoint must be string! : ' + str(endpoint)
            assert isinstance(args, dict), 'args must be in format {arg1: value...} : ' + str(args)
            assert isinstance(params, dict), 'params must be in format {arg1:type, ...} : ' + str(args)
            assert protocol.upper() in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], 'Invalid protocol: ' + protocol.upper()

            self.include_query_markers = include_query_markers
            self.parent = parent
            self.endpoint = endpoint
            self.args = args
            self.params = params
            self.protocol = protocol.upper()
            self.header = header
            self.oauth = oauth
            if self.oauth:
                self.create_oauth()

        def create_oauth(self):
            # assert isinstance(self.oauth, OAuth2), 'self.OAuth is not OAuth2 object!'
            if type(self.oauth) == 'OAuth.OAuth2':
                self.oauth = oa2(
                    client_id=self.oauth.client_key,
                    token=self.oauth.access_token,
                )
            else:
                self.oauth = OAuth1(
                    client_key=self.oauth.client_key,
                    client_secret=self.oauth.client_secret,
                    resource_owner_key=self.oauth.access_token,
                    resource_owner_secret=self.oauth.access_token_secret
                )


        def check_args(self, *args):
            assert len(args) == len(self.args), 'incorrect number of arguments'
            for a in args:
                assert isinstance(a, dict), 'all arguments must be in format {arg_name:arg...} : ' + str(a)

        def call(self, headers={}, debug=False, **kwargs):
            if debug: print('Debug mode enabled. Use self.raw_data to access raw data returned for debugging')
            headers = {**headers, **self.header}
            request_module = requests
            if self.oauth:
                request_module = self.oauth
            url = self.parent.base_url + self.endpoint + '/'
            if self.include_query_markers:
                url += '?'
                for name, value in self.args.items():
                    url += '&{}={}'.format(name, value)
                for name, value in kwargs.items():
                    url += '&{}={}'.format(name, value)
            else:
                assert len(kwargs) == 1, 'only 1 value may be passed when include_query_markers=False'
                url += list(kwargs.values())[0]

            def get(url):
                if not self.oauth:
                    response = request_module.get(url=url, headers=headers)
                else:
                    url = self.parent.base_url + self.endpoint
                    response = requests.get(url=url, auth=self.oauth, params=kwargs)
                try:
                    0
                    return response

                except Exception as err:
                    print('Error getting data (url:{}):'.format(url), err)

            def post(url, data):
                try:
                    response = request_module.post(url=url, data=data, headers=headers)
                    return response
                except Exception as err:
                    print('Error posting data:', err)

            def put(url, data):
                try:
                    response = request_module.put(url, data, headers=headers)
                    return response
                except Exception as err:
                    print('Error putting data:', err)

            def patch(url, data):
                try:
                    response = request_module.patch(url, data)
                    return response
                except Exception as err:
                    print('Error patching data:', err)

            def delete(url, data):
                try:
                    response = request_module.delete(url, *data)
                    return response
                except Exception as err:
                    print('Error deleting data:', err)


            if self.protocol == 'GET':
                response = get(url)
            elif self.protocol == 'POST':
                response = post(url, kwargs)
            elif self.protocol == 'PUT':
                response = put(url, kwargs)
            elif self.protocol == 'PATCH':
                response = patch(url, kwargs)
            elif self.protocol == 'DELETE':
                response = delete(url, kwargs)
            else:
                response = {}
            try:
                result_obj = result_helper(response.json())
                if not isinstance(result_obj, list):
                    result_obj.request_url = url
                else:
                    [setattr(x, 'request_url', url) for x in result_obj]
                if debug:
                    result_obj.raw_data = response.json()
                return result_obj
            except Exception as err:
                if self.protocol != 'DELETE': print('error saving result', err)
                return response


    def __init__(self, base_url='https://jsonplaceholder.typicode.com'):
        self.base_url = base_url
        self.endpoints = {}

    def add_endpoint(self, endpoint_name, endpoint, protocol='GET', args={}, header={}, include_query_markers=True, oauth=False, **kwargs):
        self.endpoints[endpoint_name] = self.endpoint(self, endpoint=endpoint, args=args,
                                                      params=kwargs, include_query_markers=include_query_markers,
                                                      protocol=protocol, header=header, oauth=oauth)
        setattr(self, endpoint_name, self.endpoints[endpoint_name].call)

    def call(self, endpoint_name, params={}, header={}):
        headers = {**self.header, **header}
        return self.endpoints[endpoint_name].call(params, headers)

def test_get():
    global api
    api.add_endpoint('get_users', '/api/users', 'GET')
    return api.get_users()

def test_post():
    global api
    api.add_endpoint('post_users', '/api/users', 'POST')
    return api.post_users(name='ZZ Top', movies=['I love u', 'I luv my beard'])

def test_put():
    global api
    api.add_endpoint('put_users', '/api/users/2', 'PUT')
    return api.put_users(name='Nicolas Cage', movies=['Everything bb', 'Nicolas Cage is bueno'])

def test_patch():
    global api
    api.add_endpoint('patch_users', '/api/users/2', 'PATCH')
    return api.patch_users(name='Kevin Spacey', movies=['Se7en', 'American Beauty'])

def test_delete():
    global api
    api.add_endpoint('delete_users', '/api/users/2', 'DELETE')
    return api.delete_users()



# if __name__ == '__main__':
#     api = apPy('https://reqres.in')
#     post = test_post()
#     get = test_get()
#     put = test_put()
#     patch = test_patch()
#     delete = test_delete()
