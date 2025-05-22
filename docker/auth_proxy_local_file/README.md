# Nginx Configuration for Auth Proxy

This example demonstrates how to set up an Nginx server as an authentication proxy for local files with manifests containing the secret token.


## Testing

Start the server:

```shell
docker-compose build
docker-compose up
```

Request a file without authentication:

```shell
curl http://localhost:8080/restricted_file.txt
```

A 403 Forbidden error should be returned.

Request a file with authentication:

```shell
curl http://localhost:8080/restricted_file.txt -H "Authorization: Bearer secret_word"
```

File contents should be returned.
