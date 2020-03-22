# HAProxy Dataplane API Python 

Python library to configura HA Proxy using Dataplane API.

A Dockerfile is provided for HAProxy with Dataplane enabled.

# Usage

```
import haproxy_python

API = haproxy_python.RestAPI("http://localhost:5555", "admin", "admin","v2")

try:
    transaction = API.services.haproxy.transactions(method="POST", version=1)

    backend = {
        "name": "test_backend",
        "mode": "http",
        "balance": {
            "algorithm": "roundrobin"
        },
        "httpchk": {
            "method": "HEAD", "uri": "/", "version": "HTTP/1.1"
        }
    }

    server = {
        "name": "server1", 
        "address": "127.0.0.1", 
        "port": 9090, "check": 
        "enabled", 
        "maxconn": 30, 
        "weight": 100
    }

    frontend = {
        "name": "test_frontend", 
        "mode": "http", 
        "default_backend": "test_backend", 
        "maxconn": 2000
    }

    bind = {"name": "http", "address": "*", "port": 80}

    API.services.haproxy.configuration.backends(method="POST", body=backend, transaction_id=transaction.id)
    API.services.haproxy.configuration.servers(method="POST", body=server, backend="test_backend",transaction_id=transaction.id)
    API.services.haproxy.configuration.frontends(method="POST", body=frontend, transaction_id=transaction.id)
    API.services.haproxy.configuration.binds(method="POST", body=bind, frontend="test_frontend",transaction_id=transaction.id)
    API.services.haproxy.transactions(path=transaction.id,method="PUT")
except haproxy_python.RestAPIException as e:
    self.fail(e.message)

```