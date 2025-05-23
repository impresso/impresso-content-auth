# Nginx Configuration for Auth Proxy

This example demonstrates how to set up an Nginx server as an authentication proxy for local files with manifests containing the secret token.


## Testing

Start the server:

```shell
docker-compose build
docker-compose up
```

## Local File Authentication with manifest

Request a file without authentication:

```shell
curl http://localhost:8080/restricted_file.txt
```

A 403 Forbidden error should be returned.

Request a file with authentication:

```shell
curl http://localhost:8080/restricted_file.txt -H "Authorization: Bearer secret_word"
```

Manifest of the file will be read, the secret will be compared with the bearer token and file contents should be returned.

## Remote File Authentication with static secret

Request a file without authentication:

```shell
curl http://localhost:8080/freemusicarchive/storage-freemusicarchive-org/music/no_curator/Phish_Funk/Best_Bytes_Volume_3/Phish_Funk_-_07_-_Lava_Lamp_Blastculture_328AM_remix.mp3
```

A 403 Forbidden error should be returned.
Request a file with authentication:

```shell
curl http://localhost:8080/freemusicarchive/storage-freemusicarchive-org/music/no_curator/Phish_Funk/Best_Bytes_Volume_3/Phish_Funk_-_07_-_Lava_Lamp_Blastculture_328AM_remix.mp3 -H "Authorization: Bearer secret"
```

The bearer token will be compared with the static token configured in the docker-compose. A 200 OK response should be returned with the file contents.
