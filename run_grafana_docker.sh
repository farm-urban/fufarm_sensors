#!/bin/bash
#sudo ufw allow in on docker0
#docker exec -it `docker ps | grep grafana | awk '{print $1}'` /bin/bash

docker run -d \
--network host \
--volume "$PWD/grafana-data:/var/lib/grafana" \
--user $(id -u):$(id -g)  \
-e GF_LOG_MODE="console file" \
-e GF_LOG_LEVEL="debug" \
-e GF_SERVER_ROUTER_LOGGING=true \
-e GF_SECURITY_ALLOW_EMBEDDING=true \
-e GF_AUTH_ANONYMOUS_ENABLED=true \
-e GF_AUTH_ANONYMOUS_ORG_NAME=AnonymousOrg \
-e GF_SERVER_DOMAIN=grafana.farmurban.co.uk \
-e GF_INSTALL_PLUGINS=grafana-clock-panel \
-e GF_PANELS_DISABLE_SANITIZE_HTML=true \
grafana/grafana


#-e GF_SERVER_ROOT_URL=http://78.31.105.128:3000 \
#-e GF_SERVER_SERVE_FROM_SUB_PATH=true \
