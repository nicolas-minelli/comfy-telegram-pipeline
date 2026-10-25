# Security policy

## Project status

Comfy Telegram Pipeline is a portfolio/community preview based on a personal deployment. It has not undergone a complete clean-install validation, independent security audit, or certification for Internet-facing production use.

Security reports are reviewed as time permits. There is no guaranteed response/resolution time, bug bounty, or security-maintenance SLA. Review focuses on the current default branch and latest preview; there is no committed backport program for older releases.

## Report vulnerabilities privately

Do not publish exploit details, proof-of-concept payloads, credentials, signed approval links, private hostnames, or operational state in public issues or PRs.

1. Open the repository's **Security → Advisories** area and use **Report a vulnerability** when private vulnerability reporting is available.
2. Include affected version/commit, component, impact, prerequisites, and minimal reproduction using synthetic data. Describe any mitigation you have tested.
3. If the private report option is unavailable, open only a minimal public request for a private security contact, such as: “Please provide a private channel for a security report.” Do not include the vulnerable endpoint, exploit, attachment, or affected installation details. Wait for a private channel before sending them.

The policy file alone does not enable GitHub private vulnerability reporting. Maintainers must enable that repository setting separately where supported. No private-reporting feature is claimed to be enabled by this package.

## If a credential was exposed

Revoke or rotate it at the provider first. Deleting the visible post/file or changing the latest commit does not revoke a token or remove past copies. Preserve relevant evidence privately; review history and logs without reposting the secret. Coordinate any history rewrite separately instead of using a blind force-push.

Examples of sensitive material include Telegram bot tokens, the Comfy integration key, LTX Header Auth, n8n encryption keys/databases, SSH keys, signed form links, scheduler receipts, and private exports. Never send your entire runtime directory as a security report.

## Deployment boundaries

- Keep Comfy APIs, internal submission/recovery endpoints, editor, and approval forms off the public bot surface.
- Restrict the public proxy to the actual Telegram Trigger route/method and validate its origin protection.
- Treat Telegram ID allowlists as authorization, not proof that an Internet request came from Telegram.
- Restrict Code-node editing and runner filesystem/module permissions to trusted administrators.
- Keep keys and runtime state outside Git and back them up privately.
- Do not assume timeout means rejection; preserve uncertain-submission evidence to avoid duplicate GPU work.

Security of third-party components and model distribution remains subject to their own advisories and policies. Report an upstream issue to its appropriate maintainer when applicable, without disclosing private deployment information.
