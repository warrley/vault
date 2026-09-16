---
tags:
  - networks/protocol
  - networks/dns
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Protocol: Domain Name System (DNS)
*(Addresses UFC Exercises 9 and 10, RFC 1034/1035, RFC 2181, RFC 6891)*

## 1. Core Architectural Motivation & First Principles

The Internet relies on two distinct addressing paradigms:
1. **Hostnames (Human Identifiers):** Variable-length alphanumeric strings (e.g., `www.ufc.br`, `mail.google.com`) chosen for human memory, mnemonic clarity, and organizational independence.
2. **IP Addresses (Router Locators):** Fixed-length numerical identifiers ($32\text{-bit}$ IPv4 or $128\text{-bit}$ IPv6) optimized for hierarchical network prefix routing, hardware ternary content-addressable memory (TCAM) lookup tables, and fast packet forwarding.

$$\text{Human Mnemonic Name } (www.ufc.br) \underset{\text{DNS Resolution}}{\overset{\text{Query / Reply}}{\rightleftharpoons}} \text{Router Numerical Locator } (200.17.41.10)$$

### Why DNS Operates at the Application Layer (The End-to-End Principle)
- **Dumb Core, Smart Edges:** Intermediate routers in the network core do not parse variable-length strings, understand domain hierarchies, or execute name resolution. Routers strictly inspect fixed-length IP headers to forward packets at line rate.
- **Client-Server Service at the Edge:** DNS operates exclusively on end systems at the network edge. Application processes invoke the local operating system resolver before opening a transport connection.

---

## 2. The Scale Problem & The 3-Tier Distributed Hierarchy

In ARPANET, host resolution was managed via a single flat text file (`hosts.txt`) maintained centrally by SRI-NIC and fetched via FTP. This centralized model collapses at Internet scale due to four structural bottlenecks:
1. **Single Point of Failure:** A central failure incapacitates global name resolution.
2. **Traffic Bottleneck:** Billions of global nodes querying a centralized cluster saturate bandwidth and CPU resources.
3. **Geographic Propagation Latency:** Long physical distances introduce massive Round-Trip Time (RTT) penalties ($>150\text{ ms}$) on every new connection.
4. **Administrative Maintenance Gridlock:** Centralized records cannot accommodate millions of dynamic updates, additions, and reconfigurations across decentralized institutions.

To achieve scale, DNS organizes the global namespace into an **inverted hierarchical tree** of delegated authority:

```
                                  [ . (Root Zone) ]
                                    /     |     \
                                   /      |      \
                       [ .com gTLD ]  [ .org gTLD ]  [ .br ccTLD ]
                             |                             |
                     [ google.com ]                    [ ufc.br ]  <-- Authoritative Nameservers
                             |                             |
                    [ mail.google.com ]                [ www.ufc.br ]
```

### The Three Tiers of Authority:

```
+----------------------------------------------------------------------------------------------------+
|                                    THE 3 TIERS OF DNS AUTHORITY                                    |
+----------------------+-----------------------------------------------------------------------------+
| 1. Root Servers      | Sits at the apex ('.'). Does NOT know host IP addresses.                    |
|                      | Points exclusively to the TLD nameservers responsible for each top-level   |
|                      | domain (e.g., '.com', '.br', '.org').                                       |
+----------------------+-----------------------------------------------------------------------------+
| 2. TLD Servers       | Divided into Generic TLDs (gTLDs: .com, .net, .edu) and Country-Code TLDs   |
|                      | (ccTLDs: .br, .uk, .de). Managed by designated registries (e.g., Verisign,  |
|                      | Registro.br). Points to Authoritative Nameservers for registered domains.   |
+----------------------+-----------------------------------------------------------------------------+
| 3. Authoritative     | Maintained directly by organizations or managed DNS providers (Cloudflare,   |
|    Servers           | AWS Route53). Stores the definitive Resource Records (RRs) containing final |
|                      | IP mappings for all hosts under that organization's zone.                   |
+----------------------+-----------------------------------------------------------------------------+
```

---

## 3. Physical Architecture of the Root Servers
*(Directly solves UFC Exercise 9)*

- **13 Logical Root Names:**
  The global root authority is identified by **13 logical service names**, labeled alphabetically from `a.root-servers.net` to `m.root-servers.net`.
- **The 512-Byte UDP Constraint:**
  The number 13 was historically chosen because a complete DNS root referral message (listing 13 server hostnames alongside their corresponding IPv4 addresses in the additional section) had to fit within the **$512\text{-byte}$ maximum payload of standard UDP** over IP without triggering fragmentation or truncation.
- **Administrative Dispersion:**
  The 13 logical authorities are operated by 12 independent, geographically distributed institutions (including ICANN, NASA, Verisign, USC-ISI, US Army Research Lab, WIDE Project, and Netnod) to prevent political or institutional capture.
- **BGP Anycast Physical Replication:**
  These 13 logical identifiers are **not** 13 individual machines. Today, they are replicated across **over 1,500+ physical servers worldwide** using **BGP Anycast Routing**.
  - Multiple physical machines in hundreds of data centers worldwide announce the exact same IP prefix (e.g., `198.41.0.4` for `a.root-servers.net`) via BGP to local ISPs.
  - When a resolver emits a packet to a root address, the Internet's routing infrastructure routes the packet along the shortest BGP path to the topologically nearest physical instance, providing ultra-low latency and natural resilience against Distributed Denial of Service (DDoS) attacks.

---

## 4. Query Resolution Mechanics: Iterative vs. Recursive

When a client application on host `client.ufc.br` initiates a lookup for `www.amazon.com`:

```
                             [ Root Server ]
                                ^        |
                    (2) Query   |        | (3) Referral (Points to .com TLD)
                                |        v
[ Client Host ] <=======> [ Local DNS Server ] <-------- (4) Query --------> [ .com TLD Server ]
 (1) Recursive Query      (e.g., 8.8.8.8)      <======== (5) Referral ====== (Points to amazon.com NS)
 (8) Final IP Answer            |        ^
                                |        | (6) Query
                                v        | (7) Reply (Type A = 54.239.28.85)
                            [ Authoritative Server ]
                                (ns1.amazon.com)
```

### Resolution Modes:

1. **Recursive Query (Step 1):**
   - The querying entity delegates the entire burden of resolution to the queried server.
   - The queried server must return either the requested resource record or an explicit error (`NXDOMAIN`).
   - Used between the **End Host** and the **Local DNS Server (Resolver)** to keep client devices lightweight and stateless.
2. **Iterative Query (Steps 2–7):**
   - If the queried server does not possess the requested record, it replies with a **Referral Response** containing the `NS` (and associated glue `A`) records of the next lower authority in the hierarchy.
   - The querying entity (the Local Resolver) receives the pointer and initiates the next query itself.
   - **Why Root and TLD servers enforce iterative queries:** Handling recursive queries would force apex servers to maintain open connection states, allocate memory buffers, and wait for third-party responses for billions of concurrent requests, leaving them vulnerable to trivial resource exhaustion attacks.

### Caching Dynamics & TTL (Time-To-Live)
- **Local DNS Caching:** Whenever a resolver receives a response (including intermediate TLD delegations and authoritative host mappings), it stores the record in RAM for the duration specified by the **`TTL`** (in seconds).
- **Cache Bypass:** Because TLD delegations (`.com`, `.br`) typically have long TTLs ($24\text{--}48\text{ hours}$), the overwhelming majority of everyday user requests bypass Root and TLD servers entirely, querying Authoritative servers directly.
- **Negative Caching (RFC 2308):** Non-existent domain responses (`NXDOMAIN`) are also cached for a duration defined by the zone's `SOA Minimum TTL` to prevent continuous lookup floods for mistyped domains.

---

## 5. DNS Data Model: Resource Records (RRs)

A DNS database consists of **Resource Records (RRs)**. Every reply packet carries one or more RRs structured as a 4-tuple:

$$\mathbf{\text{RR} = (\text{Name}, \text{Value}, \text{Type}, \text{TTL})}$$

| Type | Meaning of `Name` | Meaning of `Value` | Concrete Zone File Syntax | Functional Role |
| :--- | :--- | :--- | :--- | :--- |
| **`A`** | Hostname | **IPv4 Address** (32-bit) | `relay.ufc.br.  86400  IN  A  200.17.41.10` | Resolves canonical hostnames to standard IPv4 addresses. |
| **`AAAA`** | Hostname | **IPv6 Address** (128-bit) | `relay.ufc.br.  86400  IN  AAAA  2801:80::1` | Resolves canonical hostnames to 128-bit IPv6 addresses. |
| **`NS`** | Domain Name | **Authoritative Server Hostname** | `ufc.br.  86400  IN  NS  dns1.ufc.br.` | Delegates a subdomain/zone to a specific nameserver. |
| **`CNAME`** | Alias Hostname | **Canonical (Real) Hostname** | `www.ufc.br.  86400  IN  CNAME  portal.ufc.br.` | Maps friendly aliases/services to a single canonical host. |
| **`MX`** | Domain Name | **Mail Server Hostname** (+ Priority) | `ufc.br.  86400  IN  MX  10  mail.ufc.br.` | Routes incoming SMTP email for the domain to a mail server. |
| **`TXT`** | Arbitrary String | **Text Data** | `ufc.br.  86400  IN  TXT  "v=spf1 mx ~all"` | Carries machine-readable security metadata (SPF, DKIM, DMARC). |
| **`SOA`** | Zone Name | **Zone Authority Metadata** | `ufc.br. IN SOA dns1.ufc.br. admin.ufc.br. (...)` | Defines zone serial, refresh/retry timers, and minimum negative TTL. |
| **`PTR`** | Reversed IP (`.in-addr.arpa`) | **Canonical Hostname** | `10.41.17.200.in-addr.arpa. IN PTR relay.ufc.br.` | Executes Reverse DNS (IP-to-Hostname) translation. |

### Crucial Record Mechanics:
1. **Glue Records (Breaking Circular Dependencies):**
   If the domain `ufc.br` specifies `dns1.ufc.br` as its authoritative nameserver (`NS`), a resolver looking up `ufc.br` cannot reach `dns1.ufc.br` without first resolving `dns1.ufc.br`. To break this circular dependency, the parent registry (`.br` TLD) provides an accompanying **Glue Record** (a Type `A` record mapping `dns1.ufc.br` to its IP address) inside the **Additional Section** of the referral response.
2. **CNAME vs. A Records:**
   A host can have multiple `CNAME` records pointing to one canonical `A` record. Changing the underlying physical server IP requires updating only the single canonical `A` record.
3. **MX Priority Weighting:**
   The `MX` record carries an explicit integer priority (e.g., `10 mail1.ufc.br.`, `20 mail2.ufc.br.`). Senders attempt delivery to the lowest numeric value first, failing over to higher numbers if unreachable.

---

## 6. Reverse DNS Resolution (IP $\to$ Hostname)
*(Directly solves UFC Exercise 10)*

**Reverse DNS (rDNS)** determines the canonical hostname associated with a numeric IP address.

```
                  [ in-addr.arpa ]
                         |
                 [ 200.in-addr.arpa ] (Delegated to LACNIC / Registro.br)
                         |
               [ 17.200.in-addr.arpa ]
                         |
             [ 41.17.200.in-addr.arpa ] (Delegated to UFC Authoritative Server)
                         |
           [ 10.41.17.200.in-addr.arpa ] --> Points to: relay.ufc.br (Type PTR)
```

### The Architectural Problem:
- Forward DNS is indexed hierarchically from right to left (child to parent: `www.ufc.br` $\rightarrow$ `.br` $\rightarrow$ `ufc` $\rightarrow$ `www`).
- IP addresses are structured with the network prefix on the left and the specific host identifier on the right (`200.17.41.10`).
- Without an inverted index, discovering the owner of an IP would require an exhaustive brute-force traversal across all global authoritative nameservers.

### Configuration & Resolution Mechanism:
1. **The Special `.in-addr.arpa` Domain:**
   Under the Infrastructure `.arpa` top-level domain, the dedicated reverse namespace `in-addr.arpa` is allocated for IPv4 (and `ip6.arpa` for IPv6).
2. **Reversing the Octets:**
   The four decimal octets of the IPv4 address are inverted so that the network prefix aligns with the right-to-left delegation of the DNS tree:
   $$\text{IP: } 200.17.41.10 \implies \mathbf{10.41.17.200.in\text{-}addr.arpa}$$
3. **Zone Delegation:**
   - The Root delegates `.in-addr.arpa` to IANA.
   - IANA delegates `200.in-addr.arpa` to the Regional Internet Registry (LACNIC / Registro.br).
   - Registro.br delegates the subnet reverse zone `41.17.200.in-addr.arpa` to UFC's authoritative nameserver.
4. **The `PTR` (Pointer) Record in the Zone File:**
   In UFC's reverse zone configuration file:
   ```text
   $ORIGIN 41.17.200.in-addr.arpa.
   $TTL 86400
   @    IN   SOA   dns1.ufc.br. hostmaster.ufc.br. ( 2025091601 28800 7200 604800 86400 )
   @    IN   NS    dns1.ufc.br.
   10   IN   PTR   relay.ufc.br.
   ```
5. **Lookup Execution:**
   A resolver sends a standard DNS query for `10.41.17.200.in-addr.arpa` with `Type = PTR`. The response returns `relay.ufc.br.`.

---

## 7. Transport Layer Dynamics: UDP vs. TCP Port 53

DNS operates across both UDP and TCP on well-known **port 53**:

```
+----------------------------------------------------------------------------------------------------+
|                                    DNS TRANSPORT LAYER SELECTION                                   |
+--------------------------+-------------------------------------------------------------------------+
| UDP Port 53              | - Default for standard interactive queries and responses.               |
| (Low Latency / Best-     | - Incurs zero connection-setup overhead (0-RTT vs TCP 1-RTT handshake). |
| Effort)                  | - Legacy RFC 1035 payload limit: 512 bytes.                             |
|                          | - Extended by EDNS0 (RFC 6891) up to 4,096 bytes via buffer negotiation.|
+--------------------------+-------------------------------------------------------------------------+
| TCP Port 53              | - Triggered when response size exceeds UDP limit (Truncation bit TC=1). |
| (Reliable / Stream)      | - Zone Transfers (AXFR / IXFR) between primary and secondary servers.   |
|                          | - Cryptographic responses with large DNSSEC key chains.                 |
+--------------------------+-------------------------------------------------------------------------+
```

### The Truncation Fallback Mechanism:
If an authoritative server constructs a response that exceeds the negotiated UDP buffer size, it sets the **`TC` (Truncation) flag bit to `1`** in the DNS header and sends the truncated packet. Upon seeing `TC=1`, the local resolver immediately discards the partial UDP datagram and re-issues the identical query over **TCP port 53**.

---

## 8. DNS Message Structure

Both DNS Query and DNS Reply packets share an identical application-layer message format:

```
+---------------------------------------------------------------+
|                    Identification (16 bits)                   |
+---------------------------------------------------------------+
| QR | Opcode (4b) | AA | TC | RD | RA | Z (3b) | RCODE (4 bits) |
+---------------------------------------------------------------+
|                  Question Count (QDCOUNT - 16b)               |
+---------------------------------------------------------------+
|                   Answer Count (ANCOUNT - 16b)                |
+---------------------------------------------------------------+
|                 Authority Count (NSCOUNT - 16b)               |
+---------------------------------------------------------------+
|                Additional Count (ARCOUNT - 16b)               |
+---------------------------------------------------------------+
|                       Question Section                        |
+---------------------------------------------------------------+
|                        Answer Section                         |
+---------------------------------------------------------------+
|                       Authority Section                       |
+---------------------------------------------------------------+
|                      Additional Section                       |
+---------------------------------------------------------------+
```

### Key Header Flags:
- **`Identification` (16 bits):** Unique transaction identifier assigned by the client resolver, matched by the server in the reply to associate queries with responses over stateless UDP.
- **`QR` (1 bit):** `0` = Query, `1` = Response.
- **`AA` (Authoritative Answer - 1 bit):** Set to `1` if the replying server is the designated authoritative authority for the requested zone.
- **`TC` (Truncation - 1 bit):** Set to `1` if the response was truncated due to exceeding transport payload limits.
- **`RD` (Recursion Desired - 1 bit):** Set by client to request recursive resolution.
- **`RA` (Recursion Available - 1 bit):** Set by server to indicate recursive queries are supported.
- **`RCODE` (Response Code - 4 bits):** `0` = No Error, `3` = Name Error (`NXDOMAIN` - Domain does not exist).

---

## 9. Security & Modern Extensions

1. **DNS Spoofing & Cache Poisoning (Kaminsky Attack):**
   - Because base DNS over UDP is unauthenticated and connectionless, an attacker can flood a resolver with forged DNS responses guessing the 16-bit `Transaction ID`.
   - **Mitigations:** Source Port Randomization (SPR - randomizing the client UDP source port across all 65,535 ephemeral ports) and **DNSSEC (DNS Security Extensions)**.
2. **DNSSEC (RFC 4033):**
   - Adds cryptographic authenticity and integrity to DNS records using public-key cryptography.
   - Introduces new record types: `RRSIG` (digital signature), `DNSKEY` (public key), and `DS` (Delegation Signer hash establishing a chain of trust back to the Root).
3. **Encrypted DNS Transports:**
   - **DoT (DNS over TLS - RFC 7858):** Encrypts DNS traffic inside a dedicated TLS tunnel over **TCP port 853**.
   - **DoH (DNS over HTTPS - RFC 8484):** Encapsulates DNS queries within standard HTTPS/HTTP/2/3 traffic over **TCP/UDP port 443**, concealing queries from local network observers and ISP surveillance.

---

### Summary
> [!abstract] Key Takeaways: DNS Infrastructure & Mechanisms
> - **Hierarchy:** 3-tier distributed model (Root $\to$ TLD $\to$ Authoritative) eliminating central points of failure and scaling globally.
> - **Root Servers:** 13 logical names (`a`–`m`), operated by 12 independent bodies, physically mirrored across **1,500+ servers worldwide via BGP Anycast**.
> - **Resolution:** Client $\to$ Resolver uses **Recursive** queries; Resolver $\to$ Hierarchy uses **Iterative** queries with caching governed by `TTL`.
> - **Records:** Core RRs include `A` (IPv4), `AAAA` (IPv6), `NS` (Nameserver), `CNAME` (Alias), `MX` (Mail), and `PTR` (Reverse Pointer).
> - **Reverse DNS:** Inverts decimal IP octets, appends `.in-addr.arpa`, and queries a **Type PTR** record.
