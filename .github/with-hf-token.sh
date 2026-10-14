#!/usr/bin/env bash
# Run one command with a short-lived Hugging Face token in HUGGING_FACE_TOKEN
# and HF_TOKEN, so CI stores no long-lived Hugging Face secret.
#
# The job's GitHub OIDC token is exchanged through Hugging Face Trusted
# Publishers (https://huggingface.co/docs/hub/trusted-publishers) for a token
# scoped by HF_OIDC_RESOURCE:
#   - a Hub username (policyengine-auto): that account's CI/CD identity. The
#     token is read-only: it reads the gated repos the account can read, and
#     cannot write or read private repos.
#   - a repo (policyengine/<name>, datasets/policyengine/<name>): a publisher
#     on that repo. The token can write to that one repo.
# Hugging Face matches the job's repository, workflow file and (where set)
# branch against the identity or publisher configured for the resource.
#
# The token lasts 60 minutes from the exchange and is not refreshed, so wrap
# each step that talks to Hugging Face separately rather than exporting one
# token for a long job. The job needs `permissions: id-token: write`.
#
# Pull requests from forks get no OIDC token. With HF_OIDC_OPTIONAL=1 the
# command then runs without a token (tests that need the data skip or fail as
# they would with no credentials); otherwise the step fails.
#
# Never redirect this script's stdout: its ::add-mask:: line must reach the
# runner, or the token is neither masked nor kept out of the file. Redirect
# inside the command instead: with-hf-token.sh bash -c 'pytest ... > out.txt'
#
# Usage: HF_OIDC_RESOURCE=policyengine-auto .github/with-hf-token.sh make test
set -euo pipefail
: "${HF_OIDC_RESOURCE:?HF_OIDC_RESOURCE must name a Hugging Face user or repo}"
if [ "$#" -eq 0 ]; then
  echo "::error::with-hf-token.sh needs a command to run" >&2
  exit 2
fi
if [ -z "${ACTIONS_ID_TOKEN_REQUEST_URL:-}" ] && [ "${HF_OIDC_OPTIONAL:-}" = 1 ]; then
  echo "::notice::No OIDC token in this run (fork pull request?): running without Hugging Face credentials"
  exec env -u HF_OIDC_RESOURCE -u HF_OIDC_OPTIONAL "$@"
fi
# huggingface_hub 1.19.0 added the exchange; projects may lock an older
# version, so the CLI runs in its own throwaway environment.
if command -v uvx >/dev/null 2>&1; then
  token=$(uvx --from "huggingface_hub==2.2.0" hf auth token)
else
  token=$(pipx run --spec "huggingface_hub==2.2.0" hf auth token)
fi
if [ -z "$token" ]; then
  echo "::error::The Hugging Face token exchange for ${HF_OIDC_RESOURCE} returned no token" >&2
  exit 1
fi
echo "::add-mask::${token}"
# Unset HF_OIDC_RESOURCE for the command: huggingface_hub >= 1.19 would
# otherwise run its own exchange in place of the token passed here.
exec env -u HF_OIDC_RESOURCE -u HF_OIDC_OPTIONAL \
  HUGGING_FACE_TOKEN="$token" HF_TOKEN="$token" "$@"
