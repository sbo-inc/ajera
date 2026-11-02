# syntax=docker/dockerfile:1
#
# Runtime for `ajera[odbc]`: Python, unixODBC, and the Progress DataDirect
# Hybrid Data Pipeline (HDP) ODBC driver that Deltek ships for Ajera.
#
# Progress builds the driver for x86_64 Linux and Windows only, so this image
# must be built for linux/amd64 and runs emulated on an arm64 machine.
#
# The driver is not vendored. `make odbc-driver` downloads Deltek's public
# zip and verifies its checksum, and the build receives it through the
# `hdp-dist` named context. `make odbc-image` runs:
#
#   docker build --platform linux/amd64 --build-context hdp-dist=.odbc/download \
#     -f docker/odbc/Dockerfile -t ajera-odbc .

ARG PYTHON_VERSION=3.13
ARG DEBIAN_RELEASE=bookworm

# =============================================================================
# STAGE: hdp - run the vendor installer
# =============================================================================
#
# InstallAnywhere needs a JVM at install time only. The driver itself loads no
# Java, so none of this stage reaches the runtime image.

FROM debian:${DEBIAN_RELEASE}-slim AS hdp

# Fail early and plainly rather than inside the vendor installer.
RUN [ "$(uname -m)" = x86_64 ] \
 || { echo "The HDP driver is x86_64 only; build with --platform linux/amd64" >&2; exit 1; }

RUN apt-get update \
 && apt-get install -y --no-install-recommends default-jre-headless unzip \
 && rm -rf /var/lib/apt/lists/*

COPY --from=hdp-dist HDPLinuxDriver.zip /tmp/HDPLinuxDriver.zip

# The installer refuses to run unless the four redist files sit beside it, and
# both install-type properties must be set explicitly.
RUN cd /tmp \
 && unzip -q HDPLinuxDriver.zip \
 && cd HDPLinuxDriver/*/ \
 && chmod +x PROGRESS_DATADIRECT_HDP_ODBC_4.6.2_LINUX_64.bin \
 && ./PROGRESS_DATADIRECT_HDP_ODBC_4.6.2_LINUX_64.bin -i silent \
      -DUSER_INSTALL_DIR=/opt/progress/hdp \
      -DINSTALL_TYPE_STD=true \
      -DINSTALL_TYPE_OEM=false \
 && test -f /opt/progress/hdp/lib/ddhybrid01.so

# =============================================================================
# STAGE: runtime
# =============================================================================

FROM python:${PYTHON_VERSION}-slim-${DEBIAN_RELEASE}

# unixodbc-dev provides the unversioned libodbcinst.so the driver dlopens.
RUN apt-get update \
 && apt-get install -y --no-install-recommends unixodbc unixodbc-dev \
 && rm -rf /var/lib/apt/lists/*

COPY --from=hdp /opt/progress/hdp /opt/progress/hdp

# What the vendor's odbc.sh exports. The driver bundles its own curl, OpenSSL,
# and ICU under distinct names (libddcurl28.so, libddopenssl30.so,
# libddicu.so) and resolves them from LD_LIBRARY_PATH. It also reads the
# [ODBC] section of ODBCINI (install dir, code page) even for a DSN-less
# connection, and fails with "File not found '.odbc.ini'" without it.
#
# The driver also refuses to connect unless it can resolve a time zone, and a
# slim image has neither TZ nor /etc/sysconfig/clock.
ENV LD_LIBRARY_PATH=/opt/progress/hdp/lib \
    ODBCINI=/opt/progress/hdp/odbc.ini \
    ODBCINST=/opt/progress/hdp/odbcinst.ini \
    TZ=UTC

# Register the driver with unixODBC under the name the client asks for.
RUN printf '%s\n' \
      '[DataDirect HDP 4.6]' \
      'Description=Progress DataDirect Hybrid Data Pipeline ODBC 4.6' \
      'Driver=/opt/progress/hdp/lib/ddhybrid01.so' \
      'Setup=/opt/progress/hdp/lib/ddhybrid01.so' \
      'APILevel=0' \
      'ConnectFunctions=YY' \
      'DriverODBCVer=3.52' \
      'FileUsage=0' \
      'SQLLevel=0' \
    >> /etc/odbcinst.ini

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /usr/local/bin/

# The project environment lives outside /src, so bind-mounting a checkout
# (whose .venv belongs to the host platform) never shadows it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH=/opt/venv/bin:$PATH

WORKDIR /src

# Dependencies only; the project itself is installed from the mounted checkout
# at run time so source edits never need a rebuild.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --extra odbc --no-install-project

CMD ["bash"]
