---
tags:
  - flashcards
  - flashcards/networks
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: Application Layer & Exercise Solutions

## 1. Network Edge, Sockets & Transport Requirements (Exercises 1, 3, 16, 17)

In which part of the physical network topology are application-layer protocols implemented, and why?::Exclusively on **end systems (hosts) at the network edge**. Network core devices (routers/switches) only process up to Layer 3/2 to maximize packet-forwarding throughput and adhere to the **End-to-End Principle**, allowing applications to innovate without modifying the core network.
<!--ID: 1726000001-->

In a network transmission, what two identifiers are required to uniquely identify a specific application process running on a remote host?::The **IP Address (Layer 3)** to identify the host interface across the global Internet, and the **Port Number (Layer 4)** (16-bit integer, $0-65535$) to demultiplex the segment to the specific application socket inside the host.
<!--ID: 1726000002-->

What is a Socket in computer networks?::The software API boundary (the "door") between a user-space application process and the operating system kernel's transport layer (TCP or UDP).
<!--ID: 1726000003-->

What is the sequence of Berkeley socket system calls executed by a connection-oriented (TCP) server process?::`socket()` $\rightarrow$ `bind()` $\rightarrow$ `listen()` $\rightarrow$ `accept()` $\rightarrow$ `recv()` / `send()` $\rightarrow$ `close()`.
<!--ID: 1726000004-->

What are the 4 fundamental transport service dimensions an application can require, and which ones does TCP guarantee?::1. **Data Loss Tolerance** (TCP guarantees 100% reliability)<br>2. **Throughput / Bandwidth** (TCP does NOT guarantee minimum bandwidth)<br>3. **Timing / Latency** (TCP does NOT guarantee maximum delay)<br>4. **Security / Encryption** (TCP does NOT provide natively; requires TLS).
<!--ID: 1726000005-->

---

## 2. HTTP, Web Caching & FTP Mechanics (Exercises 4, 5, 6)

What is the difference between HTTP GET and POST methods in HTML form submissions?::* **GET**: Form data is appended to the URL query string (`/search?q=networks`), is idempotent, cached by default, but insecure for passwords and limited in size.<br>* **POST**: Form data is placed in the HTTP Request **entity body**, is not cached by default, supports arbitrary payload sizes, and hides fields from the URL.
<!--ID: 1726000006-->

What is an HTTP Transparent Proxy (Intercepting Proxy) and how is it implemented at the network level?::A proxy where the client requires **zero configuration**. The network edge router intercepts outbound TCP packets destined for port 80 using **Destination NAT (DNAT) / Policy Routing (e.g., Linux iptables REDIRECT)** and forwards them to the local proxy daemon transparently.
<!--ID: 1726000007-->

What header and HTTP status code are used by a Web Cache to perform a Conditional GET validation?::* Header sent by cache: `If-Modified-Since: <cached_date>`<br>* Response if unmodified: `HTTP/1.1 304 Not Modified` (with **no entity body**, saving bandwidth).
<!--ID: 1726000008-->

Given a base HTML file referencing 4 separate JPEG images, what is the total response time in RTTs under Non-Persistent HTTP (serial) vs Persistent HTTP with Pipelining?::* **Non-Persistent (serial)**: $2(M + 1) \cdot RTT = 2(4 + 1) = \mathbf{10 \cdot RTT}$<br>* **Persistent with Pipelining**: $1 \text{ (handshake)} + 1 \text{ (base)} + 1 \text{ (all pipelined images)} = \mathbf{3 \cdot RTT}$.
<!--ID: 1726000009-->

Why is FTP described as an "Out-of-Band" protocol compared to HTTP?::FTP uses **two separate parallel TCP connections**: a persistent **Control Connection on Port 21** for commands/authentication, and separate **Data Connections on Port 20/ephemeral** opened per file transfer. HTTP is in-band because headers and data share the same TCP connection.
<!--ID: 1726000010-->

---

## 3. Electronic Mail Protocols (Exercises 7, 8)

Why is SMTP classified as a Push protocol while POP3/IMAP are classified as Pull protocols?::* **SMTP (Push over TCP 25)**: The sending entity actively connects to push messages forward to the destination mail server.<br>* **POP3 / IMAP (Pull)**: The recipient user agent connects to pull messages stored in its remote mailbox because end-user devices are frequently offline or behind dynamic NATs.
<!--ID: 1726000011-->

Why does base SMTP permit a sender to forge another person's email address without knowing their password?::The original SMTP protocol (RFC 821) contains **no authentication mechanism** for the `MAIL FROM:` command; the server blindly accepts the address specified in the envelope, completely decoupling identity from authentication.
<!--ID: 1726000012-->

What are the 3 key architectural advantages of IMAP over POP3?::1. **State Synchronization**: Server-side tracking of read/unread flags across multiple devices.<br>2. **Server-Side Folder Management**: Folders/labels are stored centrally on the mail server.<br>3. **Component / Partial Fetching**: Can download message headers/text without downloading multi-MB attachments.
<!--ID: 1726000013-->

---

## 4. Domain Name System (DNS) & Reverse Resolution (Exercises 9, 10)

Why is DNS implemented at the Application Layer rather than as a network-layer protocol inside routers?::To adhere to the **End-to-End Principle** and keep the network core fast and simple. Routers must forward packets at hardware speeds using fixed-length numerical IP addresses (via TCAM tables). Parsing variable-length, human-friendly text hostnames would severely degrade line-rate forwarding.
<!--ID: 1726000014-->

How are the Internet DNS Root Servers physically and logically organized? (Exercise 9)::Logically organized as **13 root server authorities** (`a.root-servers.net` to `m.root-servers.net`) operated by 12 independent institutions. Historically capped at 13 to ensure a complete referral fits inside standard 512-byte UDP datagrams. Physically replicated across **over 1,500+ servers worldwide** using **BGP Anycast routing**, which automatically routes queries to the topologically nearest physical instance.
<!--ID: 1726000015-->

What are the 3 tiers of the DNS hierarchy and what information does each tier hold?::1. **Root DNS Servers**: Knows the nameservers for all Top-Level Domains (TLDs). Does NOT store host IP addresses.<br>2. **TLD Servers**: Divided into generic (gTLDs: `.com`, `.org`) and country-code (ccTLDs: `.br`, `.uk`). Stores delegation records (`NS`) pointing to Authoritative nameservers.<br>3. **Authoritative DNS Servers**: Maintained by organizations/providers. Stores definitive Resource Records (`A`, `AAAA`, `MX`, etc.) containing actual IP addresses.
<!--ID: 1726000016-->

What is the operational difference between an Iterative and a Recursive DNS query, and why do Root/TLD servers default to Iterative?::* **Recursive**: The querying entity delegates the full resolution burden to the queried server, demanding the final IP or error.<br>* **Iterative**: The queried server replies statelessly with a referral (`NS` pointer) to the next server down the hierarchy.<br>* **Why Root/TLD are Iterative**: To prevent resource exhaustion. Handling recursive queries would force apex servers to maintain millions of concurrent open connection states and pending timers.
<!--ID: 1726000017-->

What are the 7 primary DNS Resource Record (RR) types and their Name-Value mappings?::* **`A`**: Name = Hostname $\rightarrow$ Value = 32-bit IPv4 Address<br>* **`AAAA`**: Name = Hostname $\rightarrow$ Value = 128-bit IPv6 Address<br>* **`NS`**: Name = Domain Name $\rightarrow$ Value = Hostname of Authoritative Nameserver<br>* **`CNAME`**: Name = Alias Hostname $\rightarrow$ Value = Canonical (Real) Hostname<br>* **`MX`**: Name = Domain Name $\rightarrow$ Value = Hostname of Mail Server (+ Priority)<br>* **`TXT`**: Name = Domain Name $\rightarrow$ Value = Arbitrary Text (SPF, DKIM, DMARC)<br>* **`PTR`**: Name = Inverted IP (`.in-addr.arpa`) $\rightarrow$ Value = Canonical Hostname.
<!--ID: 1726000018-->

What is a DNS Glue Record and what problem does it solve?::A Type `A` (or `AAAA`) record provided by a parent registry in the **Additional Section** alongside an `NS` delegation record when the authoritative nameserver's hostname is located *inside* the delegated domain itself (e.g., `ufc.br` served by `dns1.ufc.br`). It prevents an unresolvable circular dependency deadlock.
<!--ID: 1726000019-->

How is Reverse DNS (rDNS) configured and executed from registry to authoritative server? (Exercise 10)::1. **Octet Inversion**: The 4 decimal octets are reversed (`200.17.41.10` $\rightarrow$ `10.41.17.200`) so network prefixes align with right-to-left DNS tree structure.<br>2. **Namespace**: Appended to `.in-addr.arpa` (`10.41.17.200.in-addr.arpa`).<br>3. **Delegation**: The registry (Registro.br) delegates the subnet zone `41.17.200.in-addr.arpa` to the organization's nameserver.<br>4. **Record**: The organization configures a **Type PTR** record: `10 IN PTR relay.ufc.br.`.
<!--ID: 1726000020-->

When does DNS switch from UDP port 53 to TCP port 53?::1. When a DNS response exceeds the maximum UDP payload size ($512\text{ bytes}$ under legacy RFC 1035), causing the server to set the **Truncation flag bit (`TC = 1`)**, prompting the resolver to retry over TCP.<br>2. When performing **DNS Zone Transfers (AXFR / IXFR)** between primary and secondary servers.<br>3. When exchanging large cryptographic DNSSEC signature chains.
<!--ID: 1726000021-->

What is DNS Cache Poisoning (Kaminsky Attack) and how do modern resolvers defend against it?::An attack where a malicious actor floods a resolver with forged DNS responses guessing the 16-bit **Transaction ID** before the legitimate server replies. Defenses include **Source Port Randomization (SPR)** (randomizing ephemeral UDP client ports across 16-bit space, yielding $2^{32}$ entropy) and **DNSSEC** (cryptographic digital signature validation).
<!--ID: 1726000022-->

What is the difference between DNS over TLS (DoT) and DNS over HTTPS (DoH)?::* **DoT (RFC 7858)**: Runs DNS directly inside a TLS tunnel on a dedicated port (**TCP 853**). Visible as DNS traffic at the network layer.<br>* **DoH (RFC 8484)**: Encapsulates DNS queries within standard HTTPS/HTTP/2/3 traffic over **port 443**, making DNS queries indistinguishable from regular web traffic to prevent ISP monitoring and censorship.
<!--ID: 1726000023-->
