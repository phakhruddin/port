FROM --platform=linux/amd64 mirror.gcr.io/library/python:3.12-slim AS verifier
ARG AWS_PROVIDER_VERSION=6.51.0
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/tests \
    TF_CLI_CONFIG_FILE=/etc/terraformrc.offline
# Tool set is kept identical to environment/Dockerfile on purpose: v1 of this
# task had a verifier image that installed boto3 but not awscli, even though
# the public contract explicitly permitted AWS CLI use and the agent
# environment provided it — a submission that used it legitimately failed
# every dependent test with "command not found" after relocation. The `for`
# loop below fails the image build itself, at task-authoring time, if this
# environment ever drifts from that guarantee again.
RUN apt-get update && apt-get install -y --no-install-recommends bash curl jq unzip \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir awscli boto3 jsonschema pytest requests pyyaml \
    && curl -fsSLo /tmp/terraform.zip https://releases.hashicorp.com/terraform/1.15.8/terraform_1.15.8_linux_amd64.zip \
    && unzip -q /tmp/terraform.zip -d /usr/local/bin \
    && rm /tmp/terraform.zip \
    && mkdir -p /opt/terraform-provider-mirror /tmp/provider-seed \
    && printf '%s\n' \
      'terraform {' \
      '  required_providers {' \
      '    aws = {' \
      '      source = "hashicorp/aws"' \
      "      version = \"=${AWS_PROVIDER_VERSION}\"" \
      '    }' \
      '  }' \
      '}' >/tmp/provider-seed/main.tf \
    && TF_CLI_CONFIG_FILE=/dev/null terraform -chdir=/tmp/provider-seed init -backend=false -input=false \
    && TF_CLI_CONFIG_FILE=/dev/null terraform -chdir=/tmp/provider-seed providers mirror /opt/terraform-provider-mirror \
    && rm -rf /tmp/provider-seed \
    && printf '%s\n' \
      'disable_checkpoint = true' \
      'provider_installation {' \
      '  filesystem_mirror {' \
      '    path = "/opt/terraform-provider-mirror"' \
      '    include = ["registry.terraform.io/hashicorp/aws"]' \
      '  }' \
      '}' >/etc/terraformrc.offline \
    && for tool in bash curl jq terraform aws; do command -v "$tool" >/dev/null; done
COPY . /tests
RUN groupadd --gid 10001 verifier \
    && useradd --uid 10001 --gid 10001 --create-home --shell /bin/bash verifier \
    && mkdir -p /logs/verifier /workspace/config /workspace/submission /workspace/evidence \
    && chown -R verifier:verifier /logs/verifier /workspace \
    && chmod 0555 /tests/test.sh
WORKDIR /tests
USER verifier
CMD ["sleep", "infinity"]
