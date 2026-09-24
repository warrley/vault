---
tags:
  - flashcards
  - flashcards/networks/app/email
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: Electronic Mail Protocols (SMTP, POP3, IMAP & MIME)

Why is SMTP classified as a Push protocol while POP3 and IMAP are classified as Pull protocols?::* **SMTP (Push over TCP port 25)**: The sending entity actively connects to push messages forward to the recipient mail server.<br>* **POP3 / IMAP (Pull over TCP ports 110/143)**: The recipient user agent actively connects to pull stored messages from its remote mailbox server because end-user devices are frequently offline, power-cycled, or behind dynamic NATs.
<!--ID: 1726400001-->

Why does base SMTP permit a sender to forge another person's email address without knowing their password?::The original SMTP protocol specification (RFC 821) contains **zero cryptographic authentication** for the `MAIL FROM:` command. The receiving mail server blindly accepts whatever string is placed in the envelope sender field, completely decoupling email identity from sender authentication.
<!--ID: 1726400002-->

What modern standards are used to authenticate SMTP email senders and prevent spoofing?::1. **SPF (Sender Policy Framework)**: DNS `TXT` record listing authorized sending IP addresses for a domain.<br>2. **DKIM (DomainKeys Identified Mail)**: Cryptographic asymmetric signature attached to email headers, verified against a public key published in DNS.<br>3. **DMARC**: Policy instructing receivers what to do (reject/quarantine) if SPF or DKIM fails.
<!--ID: 1726400003-->

Why is it necessary to encode a binary file (e.g. PDF, JPEG) using MIME (e.g. Base64) to attach it to an email?::Original SMTP was strictly designed to transmit **7-bit ASCII text**. Binary files contain raw 8-bit bytes (including control characters like `NUL` or `CRLF.CRLF` end-of-message markers) that corrupt or prematurely terminate SMTP connections. **MIME (RFC 2045)** transforms arbitrary 8-bit binary data into safe 7-bit ASCII characters (Base64 encoding).
<!--ID: 1726400004-->

What are the 3 major architectural advantages of IMAP over POP3?::1. **Multi-Device State Synchronization**: Server-side tracking of message state (read/unread, answered, deleted flags) synchronized across all client devices.<br>2. **Centralized Server-Side Folder Management**: Folders and labels are stored on the remote server, allowing users to organize mail from any device.<br>3. **Partial / Component Fetching**: Allows clients to retrieve only the message headers or plain text part without downloading large multi-megabyte attachments.
<!--ID: 1726400005-->
