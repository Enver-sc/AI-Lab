import ipaddress, socket
from urllib.parse import urlparse

def validate_provider_url(url, allow_localhost=False, resolver=socket.getaddrinfo):
    try: parsed = urlparse(url)
    except ValueError as exc: raise ValueError("Ungültige Provider-URL.") from exc
    if parsed.scheme not in {"http","https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Nur vollständige HTTP(S)-URLs ohne eingebettete Zugangsdaten sind erlaubt.")
    host = parsed.hostname.lower()
    if host in {"localhost","localhost.localdomain"} and not allow_localhost: raise ValueError("Lokale Ziele sind für externe Provider gesperrt.")
    try: infos = resolver(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc: raise ValueError("Provider-Hostname kann nicht aufgelöst werden.") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not allow_localhost and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise ValueError("Private oder interne Netzwerkziele sind für externe Provider gesperrt.")
    return url.rstrip("/")

