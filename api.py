import requests


class QuorumAPI(object):
    """
    An overall wrapper for Quorum's API that enables chainable
    filters and abstracts away the actual HTTP requests to the API.

    Typical usage:
    1. initialize a QuorumAPI object, passing in the username and API key
    2. set the endpoint of this particular QuorumAPI object (optionally can be specified at initialization)
    3. create a set of filters and set the settings on a given API object
    4. run GET to return relevant results

    Example:
    quorum_api = QuorumAPI(username="gwc", api_key="691e43c415d88cd16286edb1f78abb2e348688da")
    quorum_api.set_endpoint("person")
    quorum_api = quorum_api.set_endpoint("person") \
                    .count(True) \
                    .limit(100) \
                    .offset(20) \
                    .filter(role_type = RoleType.senator, current=True) \

    results = quorum_api.GET()
    next_results = quorum_api.NEXT()

    """

    # API constants
    SUPPORTED_ENDPOINTS = ["person", "bill", "vote", "district", "state"]
    BASE_URL = "https://www.quorum.us"

    # internal globals with defaults
    limit = 20
    offset = 0
    count = True
    filters = {
                "decode_enums": True
              }

    def __init__(self, username, api_key, endpoint=None):

        self.username = username
        self.api_key = api_key

        if endpoint:
            self.set_endpoint(endpoint)

    def set_endpoint(self, endpoint):

        if endpoint in self.SUPPORTED_ENDPOINTS:
            self.endpoint = endpoint
        else:
            raise Exception('Unsupported Endpoint')

        return self

    def count(self, return_count=True):
        if return_count in [True, False]:
            self.count = return_count
        else:
            raise Exception('Must be a boolean value.')

        return self

    def limit(self, value=20):
        if isinstance(value, int):
            self.limit = value
        else:
            raise Exception('Must be a numeric value.')

        return self

    def offset(self, value=0):
        if isinstance(value, int):
            self.offset = value
        else:
            raise Exception('Must be a numeric value.')

        return self

    def filter(self, **kwargs):
        for key, value in kwargs.iteritems():
            self.filters[key] = value

        return self

    def process_request(self, request):
        self.next_url = request["meta"]["next"]
        self.previous_url = request["meta"]["previous"]

    def NEXT(self):
        if hasattr(self, "next_url") and self.next_url:
            self.offset += self.limit
            next_request = requests.get(self.BASE_URL + self.next_url).json()
            self.process_request(next_request)

            return next_request
        else:
            raise Exception("End of results.")

    def PREVIOUS(self):
        if hasattr(self, "previous_url") and self.previous_url:
            self.offset -= self.limit
            next_request = requests.get(self.BASE_URL + self.previous_url).json()
            self.process_request(next_request)

            return next_request
        else:
            raise Exception("Beginning of results.")

    def GET(self):
        """
        The final step in calling the API -- actually
        go out and make the request. Returns a dictionary
        of results.
        """

        # set all the global vals as filters
        for attr in ["count", "limit", "offset", "username", "api_key"]:
            self.filters[attr] = getattr(self, attr)

        # convert all the boolean values (True and False) to strings
        for key, value in self.filters.iteritems():
            if value in [True, False]:
                if value:
                    self.filters[key] = "true"
                else:
                    self.filters[key] = "false"

        initial_request = requests.get(self.BASE_URL + "/api/%s/" % self.endpoint,
                                       params = self.filters) \
                                  .json()

        self.process_request(initial_request)

        return initial_request
