---
tags:
  - flashcards
  - flashcards/networks/app/exercises
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: Lista 1 de Exercícios (Aplicação - UFC)

In which part of the physical network topology are application-layer protocols implemented, and why? (Exercise 1)::Exclusively on **end systems (hosts) at the network edge**. Network core devices (routers and switches) operate strictly up to Layer 3/2 to maximize packet-forwarding throughput and preserve the **End-to-End Principle**, allowing applications to evolve without changing network core infrastructure.
<!--ID: 1726700001-->

Differentiate Client-Server architecture from Peer-to-Peer (P2P), with advantages and disadvantages of each. (Exercise 2)::* **Client-Server**: Central server services always-on requests. Advantage: central security and data consistency. Disadvantage: server is a single point of failure and bottleneck ($O(N)$ capacity).<br>* **P2P**: Direct communication between peers. Advantage: self-scalability and low cost. Disadvantage: peer churn, security risks, and complex overlay routing.
<!--ID: 1726700002-->

Differentiate the main transport requirements an application can have, with concrete examples. (Exercise 3)::1. **Loss Tolerance**: File transfer (FTP/HTTP) requires 0% loss (TCP); VoIP/real-time video can tolerate 1-5% packet loss (UDP).<br>2. **Throughput Sensitivity**: Audio/video streaming requires minimum bandwidth (e.g. 5 Mbps for HD video); elastic applications (email, web) adapt to any rate.<br>3. **Timing / Latency**: Multiplayer games and IP telephony require delay $\le 100\text{ ms}$; email has no delay constraint.<br>4. **Security**: Banking requires TLS encryption and authentication.
<!--ID: 1726700003-->

Explain HTTP form methods (GET vs. POST). (Exercise 4)::* **`GET`**: Form data is appended to URL query string (`/search?q=networks`), is idempotent, cached by default, limited in length, and visible in browser history.<br>* **`POST`**: Form data is sent inside the HTTP Request **Entity Body**, is non-idempotent, uncached by default, supports arbitrary sizes, and keeps parameters out of the URL.
<!--ID: 1726700004-->

Explain what an HTTP proxy is and how a "transparent proxy" is implemented. (Exercise 5)::An **HTTP Proxy** is an intermediary caching server satisfying requests on behalf of origin servers.<br>* **Transparent Proxy**: Requires zero client browser configuration. The edge router intercepts outbound traffic on TCP port 80 using **Destination NAT (DNAT) / `iptables` REDIRECT** and forwards the packets to the local proxy daemon transparently.
<!--ID: 1726700005-->

Explain why the FTP protocol is said to be controlled "out-of-band". (Exercise 6)::Because FTP uses **two separate parallel TCP connections**: a persistent **Control Connection on Port 21** for sending commands and authentication, and separate temporary **Data Connections on Port 20/ephemeral** opened dynamically for each file transfer.
<!--ID: 1726700006-->

Explain why it is possible to send messages using SMTP impersonating someone else without knowing their password. (Exercise 7)::Because base SMTP (RFC 821) contains **no authentication mechanism** for the `MAIL FROM:` envelope command; the mail server blindly accepts any address specified in the header, completely decoupling identity from authentication.
<!--ID: 1726700007-->

Why is it necessary to convert a binary file to attach it to an email? (Exercise 8)::Because original SMTP is restricted to **7-bit ASCII text**. Raw binary files contain 8-bit bytes (including control characters like `NUL` or `CRLF.CRLF`) that break or terminate SMTP connections. **MIME (RFC 2045)** encodes binary files into safe 7-bit ASCII text (Base64 encoding).
<!--ID: 1726700008-->

What are the advantages of the IMAP protocol compared to POP3? (Exercise 9)::1. **State Synchronization**: Keeps read/unread/flagged message states synchronized across multiple devices.<br>2. **Server-Side Folder Management**: Mail folders/labels are created and organized centrally on the server.<br>3. **Component / Partial Fetching**: Allows downloading message headers or plain text without downloading large attachments.
<!--ID: 1726700009-->

Explain how the DNS protocol root servers are organized. (Exercise 10)::Logically organized as **13 root server authorities** (`a.root-servers.net` to `m.root-servers.net`) operated by 12 independent institutions. Physically replicated across **over 1,500+ servers worldwide** using **BGP Anycast routing**, which automatically directs queries to the topologically closest physical server.
<!--ID: 1726700010-->

How is reverse name resolution configured and executed (IP address to hostname)? (Exercise 11)::1. Reverse the 4 octets of the IP address (`200.17.41.10` $\to$ `10.41.17.200`).<br>2. Append to `.in-addr.arpa` (`10.41.17.200.in-addr.arpa`).<br>3. Registry delegates zone `41.17.200.in-addr.arpa` to the organization's nameserver.<br>4. Authoritative nameserver creates a **Type PTR** record: `10 IN PTR relay.ufc.br.`.
<!--ID: 1726700011-->

How does DNS provide server Load Balancing? Explain and give an example. (Exercise 12)::By configuring **multiple Type `A` records with different IP addresses for the same hostname** (e.g. `web.ufc.br` has IPs `200.17.41.1`, `200.17.41.2`, `200.17.41.3`). The authoritative DNS server rotates the order of returned IP addresses on every query (**DNS Round-Robin**), evenly distributing incoming client connections across the server farm.
<!--ID: 1726700012-->

Differentiate pure P2P networks from hybrid P2P networks. (Exercise 13)::* **Hybrid P2P (e.g. Napster)**: Uses a centralized index server for search/discovery; peers transfer files directly P2P.<br>* **Pure P2P (e.g. Gnutella)**: Has no central servers whatsoever; peers form an overlay mesh and search content using decentralized query flooding.
<!--ID: 1726700013-->

How does the Gnutella protocol work for content searching? (Exercise 14)::A peer sends a `Query` message to all its immediate overlay neighbors. Neighbors search local storage and forward the query to their own neighbors. Each query has a **TTL (Time-To-Live)** decremented at each hop to prevent infinite flooding. Responses return via `QueryHit` back along the reverse path.
<!--ID: 1726700014-->

Application Layer Synthesis Question: What is a DNS Glue Record and why is it essential? (Exercise 15)::A Type `A`/`AAAA` record provided by the parent TLD registry in the Additional Section alongside an `NS` delegation record when the authoritative nameserver's hostname resides *inside* the delegated zone (e.g. `ufc.br` served by `ns1.ufc.br`). It breaks the circular dependency that would otherwise make the domain unresolvable.
<!--ID: 1726700015-->
