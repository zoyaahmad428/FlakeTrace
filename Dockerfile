# W27 (reproducibility image, M3): pins the exact toolchain a fixture diagnosis needs --
# Maven 3.9.9, Temurin JDK 8, Python 3 -- so "it reproduces on my machine" is one build away from
# "it reproduces on any machine with Docker". Does not implement the full sandbox profile in
# docs/02-Requirements/non-functional.md (rootless, network-disabled, resource limits) -- that
# remains a later target; this image is for reproducibility, not isolation.
#
# Pinned by digest, not just the tag (M2's review, PR #153): a moved tag would silently change
# the JDK 8 patch level under us, exactly the kind of drift docs/evidence-m3.md already found
# between this host's Temurin 1.8.0_512 and this image's own 1.8.0_452.
FROM maven:3.9.9-eclipse-temurin-8@sha256:e20e4fc05fb5480c884a1f750c362ed0e91aca15cec5736e12796713710ec9b3

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /flaketrace
COPY eval/requirements.txt eval/requirements.txt
# --retries (M1's first W27 build hit a transient "from versions: none" on rpds-py; the
# unchanged retry worked, so this is PyPI/network flakiness, not a real incompatibility --
# eval/requirements.txt now pins every one of jsonschema's dependencies for the real fix).
RUN pip3 install --no-cache-dir --break-system-packages --retries 5 -r eval/requirements.txt

COPY . .

# Pinned for determinism, matching the real-case protocol's own environment (docs/05-Testing/real-case-protocol.md).
ENV JAVA_TOOL_OPTIONS="-Duser.timezone=UTC -Duser.language=en -Duser.country=US"

ENTRYPOINT ["python3", "-m", "runner"]
