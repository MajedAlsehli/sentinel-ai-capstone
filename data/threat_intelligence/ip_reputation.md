# IP Reputation Analysis

IP investigations correlate reputation history, abuse reports, ASN and organization ownership, geolocation, and infrastructure relationships. Cloud hosting, VPN exit nodes, shared proxies, carrier-grade NAT, and compromised infrastructure can create noisy signals, so geolocation alone must never determine a malicious verdict.

Reputation evidence should include the provider, observation time, abuse confidence or report count when available, and any missing-configuration status. An address with no provider record is unknown, not automatically benign.

Analysts should compare the address with the event context: destination port, protocol, frequency, direction, timestamps, and affected assets. Containment recommendations should be proportional to confidence and should require human review when they could disrupt legitimate shared infrastructure.
