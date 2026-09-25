<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

No throughput claim has been established for the initial iteration. The SFTP
acceptance tests measure a small synthetic upload and require its reply within
one second on localhost. That is a regression check, not a capacity guarantee.
Run `poetry run pytest tests/test_mockbank.py` to reproduce it.
