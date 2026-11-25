# Security

Please don't open a public issue for a security problem. Use a [private security advisory](https://github.com/ankit373/weight-edit-qwen/security/advisories/new) instead.

The scripts load model weights and run them on your machine. Load the base models only from the pinned revisions in the README, and check the sha256 values before you apply a diff. The diffs are safetensors files, which hold tensors only and no code.
