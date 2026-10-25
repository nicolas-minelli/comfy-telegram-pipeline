"""Prepare a new private Telegram ingress; no services, network calls or credentials."""
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[1]


def checked_port(value, minimum=1):
    if isinstance(value, bool) or not re.fullmatch(r'[0-9]{1,5}', str(value)):
        raise ValueError('Invalid numeric port.')
    number = int(value)
    if not minimum <= number <= 65535:
        raise ValueError('Port is outside the allowed range.')
    return number


def prepare(repo, target, webhook_url, n8n_host_port=5678, gateway_host_port=5680,
            private_https_port=443, project_name='telegram-ingress-example'):
    repo, target = Path(repo).resolve(), Path(target).resolve()
    if target == repo or repo in target.parents or target in repo.parents:
        raise ValueError('Prepare ingress outside the repository and its ancestors.')
    if target.exists():
        raise ValueError('Destination already exists; no files were overwritten.')
    if not isinstance(webhook_url, str) or any(c.isspace() for c in webhook_url) or any(c in webhook_url for c in ['\\', '"', "'"]):
        raise ValueError('Use a plain HTTPS production URL without whitespace or quoting.')
    try:
        parsed = urlsplit(webhook_url)
        public_port = parsed.port or 443
    except ValueError as exc:
        raise ValueError('Invalid webhook URL or port.') from exc
    hostname = parsed.hostname or ''
    if (parsed.scheme != 'https' or parsed.username or parsed.password or parsed.query or parsed.fragment
            or not hostname.isascii() or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.ts\.net', hostname)
            or '..' in hostname):
        raise ValueError('Use this device\'s HTTPS .ts.net production URL without credentials, query or fragment.')
    if public_port not in [443, 8443]:
        raise ValueError('Telegram and Funnel require a shared supported public port: 443 or 8443.')
    if not re.fullmatch(r'/webhook/[A-Za-z0-9_-]{1,128}/webhook', parsed.path):
        raise ValueError('Expected the exact native Telegram Trigger production path; prefix/test/internal routes are refused.')
    n8n_port = checked_port(n8n_host_port, 1024)
    gateway_port = checked_port(gateway_host_port, 1024)
    private_port = checked_port(private_https_port)
    if n8n_port == gateway_port or private_port == public_port:
        raise ValueError('Use different n8n/gateway host ports and different private/public HTTPS ports.')
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,50}', project_name):
        raise ValueError('Use a short lowercase Compose project name without spaces or options.')
    source = repo / 'examples/telegram-ingress'
    nginx = (source / 'nginx.conf.template').read_text(encoding='utf-8')
    if set(re.findall(r'__[A-Z0-9_]+__', nginx)) != {'__TELEGRAM_WEBHOOK_PATH__', '__N8N_UPSTREAM_URL__'}:
        raise ValueError('Nginx template contract changed; review before generating.')
    nginx = nginx.replace('__TELEGRAM_WEBHOOK_PATH__', parsed.path).replace(
        '__N8N_UPSTREAM_URL__', 'http://host.docker.internal:' + str(n8n_port))
    if re.search(r'__[A-Z0-9_]+__', nginx):
        raise ValueError('Unresolved template marker.')
    private_base = 'https://' + hostname + (':' + str(private_port) if private_port != 443 else '') + '/'
    public_base = 'https://' + hostname + (':' + str(public_port) if public_port != 443 else '') + '/'
    settings = dict(schema_version=1, project_name=project_name, hostname=hostname,
                    public_https_port=public_port, private_https_port=private_port,
                    n8n_host_port=n8n_port, gateway_host_port=gateway_port,
                    private_base_url=private_base, public_base_url=public_base,
                    webhook_path=parsed.path)
    compose = {'services': {'telegram-gateway': {
        'image': 'nginx:stable-alpine', 'restart': 'unless-stopped',
        'entrypoint': ['nginx', '-g', 'daemon off;'],
        'ports': ['127.0.0.1:' + str(gateway_port) + ':8080'],
        'volumes': [{'type': 'bind', 'source': './nginx.conf',
                     'target': '/etc/nginx/nginx.conf', 'read_only': True}]}}}
    env = '\n'.join(['# Reference values for this topology; apply in your own n8n deployment.',
                     '# This file is not loaded into n8n by the gateway Compose file.',
                     'N8N_EDITOR_BASE_URL=' + private_base, 'N8N_WEBHOOK_URL=' + public_base,
                     'N8N_HOST=' + hostname, 'N8N_PROTOCOL=https', 'N8N_PORT=5678',
                     'N8N_PROXY_HOPS=1', ''])
    runbook = (source / 'Manage-Ingress.ps1.template').read_text(encoding='utf-8')
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.ingress-prepare-', dir=target.parent))
    try:
        (staging / 'nginx.conf').write_text(nginx, encoding='utf-8')
        (staging / 'compose.local.yaml').write_text(json.dumps(compose, indent=2) + '\n', encoding='utf-8')
        (staging / 'ingress.local.json').write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
        (staging / 'n8n-url-settings.env').write_text(env, encoding='utf-8')
        (staging / 'Manage-Ingress.ps1').write_text(runbook, encoding='utf-8')
        (staging / 'BEFORE-START.txt').write_text(
            'Private configuration: keep outside Git. No token was requested or generated.\n'
            'Review nginx.conf and ingress.local.json before starting.\n'
            'Validate: .\\Manage-Ingress.ps1 -Action Validate\n'
            'Start NEW gateway: .\\Manage-Ingress.ps1 -Action StartGateway\n'
            'Configure routes on an UNCONFIGURED Tailscale host: .\\Manage-Ingress.ps1 -Action ConfigureTailscale\n'
            'Read-only status: .\\Manage-Ingress.ps1 -Action Status\n'
            'ConfigureTailscale refuses any existing Serve/Funnel state; it never resets it.\n'
            'If a later command fails, earlier successful changes remain; inspect before retrying.\n'
            'n8n URL settings are a reference, not an automatic edit/restart of n8n.\n'
            'Follow docs/REMOTE-ACCESS.md and its security section.\n', encoding='utf-8')
        if target.exists():
            raise ValueError('Destination appeared during preparation; refusing to overwrite.')
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', required=True)
    parser.add_argument('--telegram-webhook-url', required=True)
    parser.add_argument('--n8n-host-port', type=int, default=5678)
    parser.add_argument('--gateway-host-port', type=int, default=5680)
    parser.add_argument('--private-https-port', type=int, default=443)
    parser.add_argument('--project-name', default='telegram-ingress-example')
    args = parser.parse_args()
    try:
        prepare(REPO, Path(args.output_root), args.telegram_webhook_url, args.n8n_host_port,
                args.gateway_host_port, args.private_https_port, args.project_name)
    except (ValueError, OSError) as exc:
        parser.exit(1, 'Ingress preparation failed: ' + str(exc) + '\n')
    print('Prepared private ingress files. No container, proxy route or public endpoint was started.')


if __name__ == '__main__':
    main()
