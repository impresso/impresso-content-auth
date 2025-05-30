# Nginx Configuration for Auth Proxy

This example demonstrates how to set up an Nginx server as an authentication proxy for local files with manifests containing the secret token.

## Prerequisites

Create the `.env` file in the `docker/auth_proxy` directory with the following content:

```shell
cat << EOF > .env
STATIC_FILES_PATH=/app/static_files
STATIC_SECRET=secret
EOF
```

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

## Remote file authentication with user bitmap in a jwt in a cookie and resource bitmap in a Solr document

Add the following to the `.env` file:

```shell
JWT_SECRET=<your_jwt_secret>

SOLR_BASE_URL=<your_solr_base_url eg http://localhost:8983/solr>
SOLR_USERNAME=<your_solr_username>
SOLR_PASSWORD=<your_solr_password>
SOLR_CONTENT_ITEM_COLLECTION=impresso_dev # or the collection you want to use
```

If Solr is behind a reverse proxy, you also need to set the `SOLR_PROXY_URL` to the reverse proxy URL.

```shell
SOLR_PROXY_URL=socks5://host.docker.internal:1080
```

### Sending a request with a JWT in a cookie:

```shell
curl http://localhost:8080/impresso-images/LLE-2007-02-03-a-p0030/info.json \
  -b "impresso_jwt=REPLACE_ME_WITH_JWT" \
  -v
```

If the JWT is valid, the `bitmap` in the JWT will be compared with the resource bitmap in the Solr document. If they match, the request will be processed and a 200 OK response will be returned with the file contents.
