FROM haproxy:2.1

# Arguments
ARG DATAPLANE_VERSION="1.2.4"

# Configure Image
RUN set -x \ 
    && apt-get update && apt-get install -y --no-install-recommends \
		ca-certificates \
		wget procps webfs \
    && wget -O /usr/local/bin/dataplaneapi https://github.com/haproxytech/dataplaneapi/releases/download/v${DATAPLANE_VERSION}/dataplaneapi \
    && chmod +x /usr/local/bin/dataplaneapi \
    && mkdir /etc/hapee-1.9 \
	&& apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

# Copy files    
COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
