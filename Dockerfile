ARG NODE_IMAGE=docker.1ms.run/library/node:22-slim
ARG PYTHON_IMAGE=docker.1ms.run/library/python:3.13-slim
ARG NPM_REGISTRY=https://registry.npmmirror.com
ARG PYPI_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ARG DEBIAN_MIRROR=http://mirrors.aliyun.com/debian
ARG DEBIAN_SECURITY_MIRROR=http://mirrors.aliyun.com/debian-security

FROM ${NODE_IMAGE} AS frontend-builder

ARG NPM_REGISTRY
WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm config set registry ${NPM_REGISTRY} && npm install

COPY frontend ./
RUN npm run build

FROM ${PYTHON_IMAGE}

ARG PYPI_INDEX_URL
ARG DEBIAN_MIRROR
ARG DEBIAN_SECURITY_MIRROR
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_INDEX_URL=${PYPI_INDEX_URL}

RUN set -eux; \
    . /etc/os-release; \
    printf 'deb %s %s main\ndeb %s %s-updates main\ndeb %s %s-security main\n' \
      "${DEBIAN_MIRROR}" "${VERSION_CODENAME}" \
      "${DEBIAN_MIRROR}" "${VERSION_CODENAME}" \
      "${DEBIAN_SECURITY_MIRROR}" "${VERSION_CODENAME}" \
      > /etc/apt/sources.list; \
    rm -f /etc/apt/sources.list.d/*; \
    apt-get update; \
    apt-get install -y --no-install-recommends nginx; \
    rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default; \
    rm -rf /var/lib/apt/lists/*; \
    pip install --no-cache-dir -i ${PYPI_INDEX_URL} uv

COPY pyproject.toml README.md ./
RUN uv pip install --system -e .

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY --from=frontend-builder /frontend/dist ./frontend/dist
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
