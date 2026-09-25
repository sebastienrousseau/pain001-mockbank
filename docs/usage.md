<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Synthetic bank guide

This service is for pipeline tests, not real payments or settlement.
Create an SSH host key with `ssh-keygen -t ed25519 -N '' -f mock_host_key`.
Set `MOCKBANK_PASSWORD` to a test-only secret in your shell, then start:

```sh
poetry run pain001-mockbank --host-key mock_host_key --username synthetic \
  --rules examples/rules.yaml
```

Default SFTP address: `127.0.0.1:2222`. Clients must trust the generated
public host key explicitly. Send `.xml` files to `/inbox`; replies appear
at `/outbox/<uploaded-name>.pain002.xml`. Direct uploads are processed at
close. Staged `.tmp` uploads are processed after their final `.xml` rename.
Open uploads cannot be renamed. Existing files are never overwritten.

Rules accept `total_amount` comparisons (`>`, `>=`, `<`, `<=`, `==`) against
decimal literals, or `any_iban_country == "XX"`. First match wins. Reactions
are `reject` (RJCT) or `pending` (PDNG); no match returns ACCP. Totals use
instructed amounts, not the untrusted declared control sum. Mixed currencies
are refused. This is structural parsing, not XSD or bank-rulebook validation.

`reason_code` is serialized by core. `reason` documents the policy; the core
builder currently has no free-text reason field, so this text is not inserted
into XML. No post-processing rewrites core-generated XML.

Limits: 8 MiB per upload, 100 inbox files, 100 outbox files, 100 in-memory
history entries, 64 KiB YAML and 64 rules. Operators remove old mailbox files
through SFTP to reclaim quota. Malformed XML fails the SFTP operation and is
retained in the inbox for synthetic-test debugging. No real data is allowed.
Links, directory creation and metadata-based truncation are disabled.

Install the `rest` extra and pass `--rest-port 8080` for
`GET /replies?limit=10`. Results are newest first, with filename and XML.
This endpoint has no authentication: bind locally and never expose it publicly.
History is in memory; files persist if the mailbox directory is persisted.

## Container

Registry publication is not enabled pending explicit approval. The intended
destination is `ghcr.io/sebastienrousseau/pain001-mockbank`, with Linux amd64
and arm64 images. For now build and run the locally verified image:

```sh
mkdir -p mailbox
docker build -t pain001-mockbank:local-test .
docker run --rm --user "$(id -u):$(id -g)" \
  -p 127.0.0.1:2222:2222 -e MOCKBANK_PASSWORD \
  --mount "type=bind,src=$(pwd)/mock_host_key,dst=/run/host_key,readonly" \
  --mount "type=bind,src=$(pwd)/mailbox,dst=/data" \
  pain001-mockbank:local-test \
  --host 0.0.0.0 --root /data --host-key /run/host_key --username synthetic
```

Generate keys outside the image. The image runs as an unprivileged user;
the example uses your UID so the mounted private key remains readable without
making it world-readable. No shell, SCP or port-forwarding service is enabled.
