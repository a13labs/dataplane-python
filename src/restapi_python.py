
"""
A Python client for the HAProxy RestAPI.
https://github.com/a13labs/dataplane-python
"""
import logging
import requests
from types import SimpleNamespace
import json
from simplejson.errors import JSONDecodeError

__version__ = "0.0.1"

logger = logging.getLogger(__name__)

# Default timeout
DEFAULT_TIMEOUT = 60


class RestAPIException(Exception):
    """Superclass for exceptions thrown by this module"""

    def __init__(self, response: requests.Response):
        self.__dict__ = response.json()


class BadRequestException(RestAPIException):
    """
    A REST method returns 400 (BAD REQUEST)
    """


class UnauthorizedException(RestAPIException):
    """
    A REST method returns 401 (UNAUTHORIZED)
    """


class ForbiddenException(RestAPIException):
    """
    A REST method returns 403 (FORBIDDEN)
    """


class NotFoundException(RestAPIException):
    """
    A REST method returns 404 (NOT FOUND)
    """


class MethodNotAllowedException(RestAPIException):
    """
    A REST method returns 405 (METHOD NOT ALLOWED)
    """


class ServerErrorException(RestAPIException):
    """
    A REST method returns 500 (INTERNAL SERVER ERROR)
    """


class ServiceUnavailableException(RestAPIException):
    """
    The server is currently unable to handle the request
    """


class RestAPI(object):
    """
    Represents a RestAPI REST server
    :param string path: protocol://hostname:port of the server.
    :param string username: Username used to authenticate against the server
    :param string password: Password used to authenticate against the server
    :param bool verify: Whether to verify certificates on SSL connections.
    :param string version: Version of the API to use, defaults to v1
    :param float timeout: The timeout value to use, in seconds. Default is 305.
    """

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        verify: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.session = requests.Session()
        self.session.verify = verify
        self.session.auth = (username, password)
        user_agent = "dataplane-python {} ({})".format(
            __version__, self.session.headers["User-Agent"]
        )
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": user_agent,
                "X-Requested-By": user_agent,
            }
        )
        self.verify = verify
        self.timeout = timeout
        self.base_url = url

    def __repr__(self):
        return "<RestAPI API url='{}' username='{}'>".format(
            self.base_url, self.session.auth[0]
        )

    def get(self, url, **kwargs):
        """
        Does a GET request to the specified URL.
        Returns the decoded JSON.
        """
        response = self.session.get(
            url, timeout=self.timeout, params=kwargs)

        return self._handle_response(response)

    def post(self, url, prefer_async=False, body=None, **kwargs):
        """
        Does a POST request to the specified URL.
        Returns the decoded JSON.
        """
        headers = {"Prefer": "respond-async"} if prefer_async else None

        if body is not None:
            if headers is None:
                headers = {"Content-Type": "application/json"}
            else:
                headers.update({"Content-Type": "application/json"})

        response = self.session.post(
            url, headers=headers, timeout=self.timeout, json=body, params=kwargs
        )

        return self._handle_response(response)

    def put(self, url, prefer_async=False, body=None, **kwargs):
        """
        Does a PUT request to the specified URL.
        Returns the decoded JSON.
        """
        headers = {"Prefer": "respond-async"} if prefer_async else None

        if body is not None:
            if headers is None:
                headers = {"Content-Type": "application/json"}
            else:
                headers.update({"Content-Type": "application/json"})

        response = self.session.put(
            url, headers=headers, timeout=self.timeout, data=body, params=kwargs
        )
        return self._handle_response(response)

    def delete(self, url, prefer_async=False, **kwargs):
        """
        Does a DELETE request to the specified URL.
        Returns the decoded JSON.
        """
        headers = {"Prefer": "respond-async"} if prefer_async else None

        response = self.session.delete(
            url, headers=headers, timeout=self.timeout, params=kwargs
        )
        return self._handle_response(response)

    def _handle_response(self, response):
        logger.debug(
            "Sent %s request to %s, with headers:\n%s\n\nand body:\n%s",
            response.request.method,
            response.request.url,
            "\n".join(
                ["{0}: {1}".format(k, v)
                 for k, v in response.request.headers.items()]
            ),
            response.request.body,
        )
        logger.debug(
            "Recieved response:\nHTTP %s\n%s\n\n%s",
            response.status_code,
            "\n".join(["{0}: {1}".format(k, v)
                       for k, v in response.headers.items()]),
            response.content.decode(),
        )

        if not response.ok:
            self._handle_error(response)

        try:
            body = response.json()
            if isinstance(body, dict):
                return RestAPIResponse(body)
            elif isinstance(body, list):
                result = []
                for item in body:
                    result.append(RestAPIResponse(item))
                return result
        except JSONDecodeError:
            pass

        return None

    @staticmethod
    def _handle_error(response):

        exception_type = RestAPIException

        if response.status_code == 400:
            exception_type = BadRequestException

        elif response.status_code == 401:
            raise UnauthorizedException(response)

        elif response.status_code == 403:
            exception_type = ForbiddenException

        elif response.status_code == 404:
            exception_type = NotFoundException

        elif response.status_code == 405:
            exception_type = MethodNotAllowedException

        elif response.status_code == 500:
            exception_type = ServerErrorException

        elif response.status_code == 503:
            exception_type = ServiceUnavailableException

        raise exception_type(response)

    def __call__(self, **kwargs):

        return self.get(self.base_url, **kwargs)

    def __getattr__(self, name):
        return RestAPIEndpoint(name=name, path=name, dataplane=self)


class RestAPIResponse(object):

    """
    Represents a RestAPI response
    :param requests.Response reponse: response from server
    """

    def __init__(self, body: dict):
        self.__dict__ = RestAPIResponse._dict_to_sn(body).__dict__

    @staticmethod
    def _dict_to_sn(d: dict):
        result = SimpleNamespace()
        for k, v in d.items():
            if isinstance(v, dict):
                setattr(result, k, RestAPIResponse._dict_to_sn(v))
                continue
            setattr(result, k, v)
        return result

    def __repr__(self):
        return "<RestAPI Response dict='{}'>".format(
            self.__dict__
        )


class RestAPIEndpoint(object):

    """
    Represents a RestAPI Endponint
    :param string name: name of the endpoint.
    :param string path: path
    :param RestAPI dataplane: dataplane Server object
    """

    def __init__(self, name: str, path: str, dataplane: RestAPI):
        self._name = name
        self._path = path
        self._api = dataplane
        pass

    def __getattr__(self, name):
        return RestAPIEndpoint(name, "{}/{}".format(self._path, name), self._api)

    def __call__(self, path=None, api_version: str = "v1", method: str = "GET", **kwargs):
        try:
            attr = object.__getattribute__(self, method.lower())
            return attr(path=path, api_version=api_version, **kwargs)
        except AttributeError:
            return None

    def get(self, api_version: str = "v1", path=None, **kwargs):
        """
        Does a GET request to the specified URL.
        Returns the decoded JSON.
        """
        url = "{}/{}/{}".format(self._api.base_url, api_version, self._path)

        if path is not None:
            url = "{}/{}".format(url, path)

        return self._api.get(url=url, **kwargs)

    def post(self, api_version: str = "v1", path=None, **kwargs):
        """
        Does a POST request to the specified URL.
        Returns the decoded JSON.
        """
        url = "{}/{}/{}".format(self._api.base_url, api_version, self._path)

        if path is not None:
            url = "{}/{}".format(url, path)

        return self._api.post(url=url, **kwargs)

    def put(self, api_version: str = "v1", path=None, **kwargs):
        """
        Does a PUT request to the specified URL.
        Returns the decoded JSON.
        """
        url = "{}/{}/{}".format(self._api.base_url, api_version, self._path)

        if path is not None:
            url = "{}/{}".format(url, path)

        return self._api.put(url=url, **kwargs)

    def delete(self, api_version: str = "v1", path=None, **kwargs):
        """
        Does a DELETE request to the specified URL.
        Returns the decoded JSON.
        """
        url = "{}/{}/{}".format(self._api.base_url, api_version, self._path)

        if path is not None:
            url = "{}/{}".format(url, path)

        return self._api.delete(url=url, **kwargs)
