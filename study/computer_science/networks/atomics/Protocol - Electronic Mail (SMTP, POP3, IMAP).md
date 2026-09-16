---
tags:
  - networks/protocol
  - networks/email
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Protocol: Electronic Mail (SMTP, POP3, IMAP)
*(Addresses Exercises 7 and 8)*

### 1. Two-Tier Email Architecture
Email uses an asymmetric architecture separating **message dispatch/relay** from **message access**:

```
+-----------+                +-------------+                     +-------------+                +-----------+
| Alice's   |     SMTP       | Alice's     |       SMTP          | Bob's       |  POP3 / IMAP   | Bob's     |
| User      | -------------> | Mail Server | ------------------> | Mail Server | -------------> | User      |
| Agent     |     (Push)     | (Queue)     |   Server-to-Server  | (Mailbox)   |     (Pull)     | Agent     |
+-----------+                +-------------+        (Push)       +-------------+                +-----------+
```

1. **SMTP (Simple Mail Transfer Protocol - RFC 5321):**
   - A **Push** protocol over **TCP Port 25**.
   - Used by the sending User Agent to push mail to its local mail server, and between intermediate mail transfer agents (MTAs) across the Internet.
2. **Mail Access Protocols (POP3, IMAP, HTTP):**
   - **Pull** protocols.
   - End-user devices cannot run permanent SMTP listening daemons (hosts are offline, roaming, or behind dynamic NATs). Mail servers store messages in user mailboxes until the recipient's User Agent initiates a connection to **pull** them.

---

### 2. SMTP Identity Spoofing Mechanics
*(Directly solves Exercise 7)*

#### Why Can Anyone Impersonate Anyone on Base SMTP?
When a client connects to an SMTP server:
```text
S: 220 mail.domain.com ESMTP
C: HELO attacker.com
S: 250 mail.domain.com
C: MAIL FROM: <reitor@ufc.br>           <-- Envelope Sender (Unchecked!)
S: 250 2.1.0 Ok
C: RCPT TO: <aluno@ufc.br>              <-- Envelope Recipient
S: 250 2.1.5 Ok
C: DATA
S: 354 Start mail input; end with <CRLF>.<CRLF>
C: From: "Reitor da UFC" <reitor@ufc.br> <-- Message Header Line
C: Subject: Prova Cancelada
C:
C: A prova de Redes foi cancelada.
C: .
S: 250 2.0.0 Ok: queued
```

#### Core Vulnerability Factors:
1. **No Built-in Authentication in RFC 821:** The base SMTP protocol was designed without any authentication handshake before accepting the `MAIL FROM:` command.
2. **Separation of Envelope and Body:** The mail server relies blindly on the address provided in `MAIL FROM:`, which requires no proof of password or cryptographic identity.
3. **Open Relays:** Servers configured without relay restrictions accept and forward mail claiming to be from any arbitrary source to any arbitrary destination.

*(Modern mitigations: **SMTP AUTH**, **SPF (Sender Policy Framework)** DNS TXT records, **DKIM (DomainKeys Identified Mail)** digital signatures, and **DMARC**).*

---

### 3. IMAP vs. POP3: Deep Structural Comparison
*(Directly solves Exercise 8)*

| Architectural Dimension | **POP3 (Post Office Protocol v3 - RFC 1939)** | **IMAP (Internet Message Access Protocol - RFC 3501)** |
| :--- | :--- | :--- |
| **Port & Default Mode** | TCP Port `110` (or `995` SSL). "Download-and-Delete" or "Download-and-Keep". | TCP Port `143` (or `993` SSL). Client-Server Remote State Sync. |
| **State Retention** | **Stateless across sessions.** Server forgets client actions once TCP closes. | **Stateful across sessions.** Server maintains message flags (`\Seen`, `\Answered`, `\Deleted`). |
| **Storage Architecture** | Messages downloaded to the local hard drive of one machine. | Messages reside permanently on the central mail server. |
| **Multi-Device Sync** | **Broken.** Reading an email on your phone leaves it marked as unread on your PC. | **Unified.** State changes on any device instantly synchronize across all devices. |
| **Folder Hierarchy** | None on server (folders exist solely on client disk). | Full server-side folder management (`INBOX`, `Work`, `Personal`). |
| **Partial Fetching** | Downloads the entire MIME message (including multi-MB attachments). | Can download message headers/text only, deferring attachment downloads on-demand. |

---

### 4. Why Sending Raw Binary Files Over Base SMTP Fails (Without Base64/MIME)

Sending an unencoded binary file (image, PDF, executable, zip) over raw SMTP fails due to **5 fundamental protocol and architectural collisions**:

```
+----------------------------------------------------------------------------------------------------+
|                               5 FAILURE MODES OF RAW BINARY OVER SMTP                              |
+------------------------------------+---------------------------------------------------------------+
| 1. 7-Bit ASCII Parity Stripping    | 8th bit (MSB) stripped/altered by legacy relays & gateways.   |
| 2. End-of-Message Collision        | Random occurrence of CRLF.CRLF (0x0D 0x0A 0x2E 0x0D 0x0A)     |
|                                    | prematurely terminates message transmission.                  |
| 3. Line-Length Limits              | Exceeds RFC 5321 max limit (998 characters per line).         |
| 4. Line-Ending (CRLF) Translation  | Mail transfer agents normalize 0x0A <-> 0x0D 0x0A, corrupting |
|                                    | mathematical byte offsets and hashes.                         |
| 5. Control Character Traps         | Null bytes (0x00) cause C string truncation; EOT/SUB trigger  |
|                                    | connection tears.                                             |
+------------------------------------+---------------------------------------------------------------+
```

#### Detailed Breakdown of the 5 Failure Modes:

1. **The 7-Bit Cleanliness Constraint (MSB Stripping):**
   * Raw binary files utilize all 256 byte values ($0\text{x}00$ to $0\text{xFF}$), meaning $50\%$ of bytes have the most significant bit (8th bit) set to `1`.
   * Base SMTP (RFC 821) strictly requires 7-bit ASCII ($0\text{x}00$ to $0\text{x}7F$). Legacy intermediate gateways, routers, and serial terminal servers overwrite or strip the 8th bit to calculate parity checks, corrupting binary payloads.

2. **Framing Collision — The `<CRLF>.<CRLF>` False Termination:**
   * SMTP signals the completion of the `DATA` phase using a single period on a blank line: `<CRLF>.<CRLF>` (in hex: `0x0D 0x0A 0x2E 0x0D 0x0A`).
   * In any arbitrary binary file, this 5-byte sequence can appear purely by random statistical chance.
   * If this sequence appears inside an unencoded file, the SMTP server treats the message as finished prematurely. The remaining bytes of the file are then parsed as invalid SMTP commands, crashing the session and truncating the file.

3. **Violation of the 998-Character Line Length Limit (RFC 5321):**
   * SMTP specifies that no line in a message may exceed **998 characters** (plus `<CRLF>`, totaling 1000 octets).
   * Binary data is a continuous byte stream without structured newline characters. A 5MB image could contain tens of thousands of bytes without a single `\r\n`.
   * Mail server line buffers overflow, leading to forced line truncation or connection termination.

4. **Newline Normalization Corrupts Binary Integrity:**
   * Operating systems use different line-ending conventions (Unix `\n`, Windows `\r\n`, classic Mac `\r`).
   * SMTP relays routinely convert isolated `\n` (`0x0A`) to `\r\n` (`0x0D 0x0A`) or strip carriage returns (`0x0D`).
   * In a binary file, `0x0A` and `0x0D` represent actual data values (pixel colors, executable instructions, compressed offsets). Converting them destroys file integrity and corrupts cryptographic checksums.

5. **Null Bytes (`0x00`) and Control Characters:**
   * C-based mail server software (Sendmail, Postfix) uses null-terminated strings (`\0`). An unescaped `0x00` in raw binary causes string functions to terminate reads prematurely.
   * Terminal control bytes like `0x04` (EOT - End of Transmission) or `0x1A` (DOS EOF) trigger connection aborts.

---

### 5. The Solution: MIME & Base64 Encoding

**MIME (Multipurpose Internet Mail Extensions — RFC 2045/2046)** resolves all 5 failure modes without altering the core SMTP transport protocol:

```
[Raw 8-bit Binary Stream] (24 bits = 3 bytes)
        │
        ▼
[Split into 4 chunks of 6 bits] (4 x 6 = 24 bits)
        │
        ▼
[Map to Safe 64-Character 7-Bit ASCII Alphabet (A-Z, a-z, 0-9, +, /)]
        │
        ▼
[Insert CRLF every 76 characters] (Enforces RFC line-length limits)
        │
        ▼
[SMTP Transport over TCP Port 25] (100% safe from parity, framing, & control traps)
```

* **Alphabet Safety:** Base64 uses only 64 characters: `A-Z`, `a-z`, `0-9`, `+`, and `/` (plus `=` for padding). None of these are control characters, none contain `0x00`, and all fit within 7-bit ASCII ($< 128$).
* **Framing Safety:** Base64 lines are wrapped at 76 characters with `<CRLF>`, and periods (`.`) are never generated at the start of an isolated line by Base64 encoding.
* **Trade-off:** Base64 introduces a $\approx 33.3\%$ bandwidth overhead ($3\text{ bytes} \rightarrow 4\text{ bytes}$), which is the cost of guaranteeing 7-bit safe transmission.

---

### 6. SMTP vs. HTTP Comparison (Kurose & Ross 8th Ed.)

| Dimension | **SMTP (RFC 5321)** | **HTTP (RFC 7230 / 9110)** |
| :--- | :--- | :--- |
| **Communication Type** | Primarily a **Push** protocol | Primarily a **Pull** protocol |
| **Payload Encoding** | Requires **7-bit ASCII** (binary must be Base64-encoded via MIME) | **8-bit binary transparent** (carries raw binary directly) |
| **Object Encapsulation** | Places **all objects/parts** of a message into a **single multipart body** | Encapsulates **each object in its own independent response message** |
| **Connection Port** | TCP Port `25` (persistent connection by default) | TCP Port `80` / `443` (supports persistent and non-persistent) |

---

### Summary
> [!abstract] Key Takeaways: Email Protocols
> - **SMTP:** Push protocol over TCP port 25 for sending and relaying. Lacks native authentication in base RFC 821, enabling address spoofing.
> - **Raw Binary Failure:** Unencoded binary files fail over base SMTP due to 7-bit parity stripping, false `<CRLF>.<CRLF>` framing termination, the 998-character line limit, and newline normalization.
> - **MIME & Base64:** Maps 8-bit binary to safe 7-bit ASCII ($3\text{ bytes} \rightarrow 4\text{ ASCII characters}$) with 76-character line wrapping.
> - **IMAP vs POP3:** IMAP provides centralized server-side storage, full folder structures, flag synchronization across multiple devices, and partial message retrieval.
