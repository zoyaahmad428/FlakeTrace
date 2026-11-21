# W27 (reproducibility image, M3): pins the exact toolchain a fixture diagnosis needs --
# Maven 3.9.9, Temurin JDK 8, Python 3 -- so "it reproduces on my machine" is one build away from
# "it reproduces on any machine with Docker". Does not implement the full sandbox profile in
# docs/02-Requirements/non-functional.md (rootless, network-disabled, resource limits) -- that
# remains a later target; this image is for reproducibility, not isolation.
FROM maven:3.9.9-eclipse-temurin-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /flaketrace
COPY eval/requirements.txt eval/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r eval/requirements.txt

COPY . .

# Pinned for determinism, matching the real-case protocol's own environment (docs/05-Testing/real-case-protocol.md).
ENV JAVA_TOOL_OPTIONS="-Duser.timezone=UTC -Duser.language=en -Duser.country=US"

ENTRYPOINT ["python3", "-m", "runner"]
