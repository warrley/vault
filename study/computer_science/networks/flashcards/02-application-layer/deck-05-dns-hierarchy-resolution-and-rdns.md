---
tags:
  - flashcards
  - flashcards/networks/app/dns
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: Domain Name System (DNS) & Reverse Resolution

Why is DNS implemented at the Application Layer rather than as an internal routing mechanism in core routers?::To preserve the **End-to-End Principle** and maintain hardware line-rate forwarding. Core routers switch packets at gigabits/terabits per second using fixed-length numerical IP addresses via hardware TCAM lookup tables. Parsing variable-length text hostnames inside routers would destroy routing throughput.
<!--ID: 1726500001-->

How are the 13 Root DNS authorities organized logically and physically?::* **Logically**: 13 root server authorities (`a.root-servers.net` to `m.root-servers.net`) operated by 12 independent institutions (historically capped at 13 so a full referral fits inside a 512-byte UDP datagram).<br>* **Physically**: Replicated across **over 1,500 physical server nodes worldwide** using **BGP Anycast routing**, automatically directing queries to the topologically nearest physical instance.
<!--ID: 1726500002-->

What are the 3 tiers of the DNS hierarchy and what information does each tier hold?::1. **Root DNS Servers**: Know the IP addresses of the Top-Level Domain (TLD) servers. Do NOT hold host IP addresses.<br>2. **TLD Servers**: Divided into generic (gTLD: `.com`, `.org`) and country-code (ccTLD: `.br`, `.uk`). Hold delegation records (`NS`) pointing to Authoritative nameservers.<br>3. **Authoritative DNS Servers**: Maintained by domain owners/organizations; hold definitive Resource Records (`A`, `AAAA`, `MX`, `CNAME`, `TXT`) mapping hostnames to IP addresses.
<!--ID: 1726500003-->

What is the operational difference between an Iterative and a Recursive DNS query, and why do Root/TLD servers default to Iterative?::* **Recursive**: Querying entity forces the contacted server to handle the full resolution burden and return the final IP or error.<br>* **Iterative**: Contacted server responds statelessly with a referral (`NS` pointer) to the next server down the hierarchy.<br>* **Why Root/TLD are Iterative**: To prevent resource exhaustion. Handling recursive queries would force apex servers to maintain millions of open socket connections and pending timers simultaneously.
<!--ID: 1726500004-->

What are the 7 primary DNS Resource Record (RR) types and their Name-Value mappings?::* **`A`**: Name = Hostname $\to$ Value = 32-bit IPv4 Address<br>* **`AAAA`**: Name = Hostname $\to$ Value = 128-bit IPv6 Address<br>* **`NS`**: Name = Domain Name $\to$ Value = Hostname of Authoritative Nameserver<br>* **`CNAME`**: Name = Alias Hostname $\to$ Value = Canonical (Real) Hostname<br>* **`MX`**: Name = Domain Name $\to$ Value = Hostname of Mail Server (+ Priority)<br>* **`TXT`**: Name = Domain Name $\to$ Value = Arbitrary Text (SPF, DKIM, DMARC, Domain verification)<br>* **`PTR`**: Name = Inverted IP address (`.in-addr.arpa`) $\to$ Value = Canonical Hostname.
<!--ID: 1726500005-->

What is a DNS Glue Record and what circular dependency deadlock does it solve?::A Type `A` (or `AAAA`) record supplied by a parent registry in the **Additional Section** alongside an `NS` delegation record when the authoritative nameserver's hostname is located *inside* the delegated domain itself (e.g. `ufc.br` served by `dns1.ufc.br`). It breaks the circular resolution deadlock.
<!--ID: 1726500006-->

How is Reverse DNS (rDNS) configured and executed from IP address to hostname?::1. **Octet Inversion**: The 4 decimal octets are reversed (`200.17.41.10` $\to$ `10.41.17.200`).<br>2. **Namespace**: Appended to `.in-addr.arpa` (`10.41.17.200.in-addr.arpa`).<br>3. **Delegation**: Registry (Registro.br) delegates `41.17.200.in-addr.arpa` to the organization's nameservers.<br>4. **Record**: Organization adds a **Type PTR** record: `10 IN PTR relay.ufc.br.`.
<!--ID: 1726500007-->

How does DNS provide Load Balancing across replicated servers (e.g. Web server cluster)?::By configuring **multiple Type `A` records for the identical hostname** with different IP addresses (e.g., `example.com $\to$ 10.0.0.1`, `10.0.0.2`, `10.0.0.3`). The authoritative DNS server rotates the order of returned IP addresses (**DNS Round-Robin**) on each query, distributing incoming client traffic evenly across all backend nodes.
<!--ID: 1726500008-->

When does DNS switch from UDP port 53 to TCP port 53?::1. When a DNS response exceeds the UDP payload limit ($512\text{ bytes}$ under standard RFC 1035), causing the server to set the **Truncation Flag (`TC = 1`)**, prompting the client to retry over TCP.<br>2. During **Zone Transfers (AXFR / IXFR)** between primary and secondary nameservers.<br>3. When exchanging large DNSSEC cryptographic signature chains.
<!--ID: 1726500009-->

What is DNS Cache Poisoning (Kaminsky Attack) and how do modern resolvers defend against it?::An attack where an adversary floods a resolver with forged DNS responses guessing the 16-bit **Transaction ID** before the legitimate server replies. Defenses include **Source Port Randomization (SPR)** (randomizing ephemeral UDP client ports across 16-bit space, multiplying entropy to $2^{32}$) and **DNSSEC** (cryptographic digital signature verification).
<!--ID: 1726500010-->
