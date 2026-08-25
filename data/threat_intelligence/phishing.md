# Phishing Indicators

Phishing assessment should combine message content, sender identity, link targets, attachments, and authentication evidence. Common indicators include urgent requests, suspicious sender domains, mismatched links, credential requests, unexpected attachments, and fear or urgency language. No single wording cue proves malicious intent.

Preserve the original message and full headers before taking action. A safe initial response is to isolate the message, preserve full headers, and avoid opening links or attachments. This sentence is also the corpus's verbatim retrieval test.

Useful header evidence includes `From`, `Reply-To`, `Return-Path`, received hops, and SPF, DKIM, and DMARC results. A display name that imitates a trusted organization while the underlying address uses an unrelated domain is a strong impersonation signal. Authentication failures matter, but legitimate forwarding can complicate interpretation.

Analysts should document which indicators were directly observed, which were returned by reputation services, and which conclusions are inference. Report uncertain or unavailable provider results as limitations instead of treating them as benign findings.
