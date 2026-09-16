---
tags:
  - flashcards
  - flashcards/networks
  - networks/intro
parent: "[[01-introduction-to-networks]]"
---

# Flashcards: Introduction to Networks & Layered Architecture

## 1. Network Edge, Paradigms & Protocols

What is the definition of a network protocol?::A protocol defines the syntax/format of messages, the exact order in which they are exchanged between network entities, and the actions taken upon transmission or receipt of messages.
<!--ID: 1715000001-->

In what part of the network physical topology are application-layer protocols implemented, and why?::Exclusively at the **network edge (on hosts / end systems)**, because core routers and switches only process lower layers (up to Layer 3) to keep forwarding fast and simple without needing to know application logic (End-to-End Principle).
<!--ID: 1715000002-->

What is the main advantage and disadvantage of the Client-Server architecture?::**Advantage**: Centralized administration, security, and data consistency. **Disadvantage**: Central server is a single point of failure and a bandwidth/CPU bottleneck under heavy traffic.
<!--ID: 1715000003-->

What is the main advantage and disadvantage of the Peer-to-Peer (P2P) architecture?::**Advantage**: High self-scalability and cost efficiency (peers distribute data). **Disadvantage**: Complex distributed coordination, peer churn (unpredictable joins/leaves), and security challenges.
<!--ID: 1715000004-->

In a network transmission, how is a specific process running on a destination machine identified?::Via **Two-Level Addressing**: the **IP Address (Layer 3)** identifies the destination host globally, while the **Port Number (Layer 4)** (16-bit number, 0–65535) identifies the specific application process / socket inside that host.
<!--ID: 1715000020-->

What is a Socket and what are the primary system call functions required to use Berkeley sockets?::A **Socket** is the software API/door between user-space application processes (Layer 5) and kernel-space transport protocols (Layer 4). Key functions: `socket()`, `bind()`, `listen()`, `accept()`, `connect()`, `send()`/`write()`, `recv()`/`read()`, and `close()`.
<!--ID: 1715000021-->

---

## 2. Core Switching & Performance

Why did the Internet adopt packet switching over circuit switching for computer communication?::Computer traffic is bursty with long periods of silence. Packet switching uses **statistical multiplexing** to dynamically share link capacity on-demand, whereas circuit switching wastes reserved capacity when idle.
<!--ID: 1715000005-->

What is multiplexing, and what is an example outside the transport layer?::Multiplexing is combining multiple independent signals or channels over a single shared physical transmission medium. Example: **FDM in wireless radio/cable TV broadcasting** or **TDM in telephone carrier lines (T1/E1)** or **WDM in fiber optics**.
<!--ID: 1715000006-->

How is it possible for two datagram packets sent from the same host to the same destination to arrive out of order?::In a datagram packet-switched network, each packet is routed independently. If routing changes or intermediate link congestion varies, packets may traverse different paths with different delays.
<!--ID: 1715000007-->

What is the formula and physical meaning of transmission delay?::$$\text{Delay}_{\text{trans}} = \frac{L}{R}$$ It is the time required to push/serialize all $L$ bits of a packet onto a link with transmission rate $R$ bps. It depends only on packet size and link bandwidth, not physical distance.
<!--ID: 1715000008-->

What is the formula and physical meaning of propagation delay?::$$\text{Delay}_{\text{prop}} = \frac{d}{s}$$ It is the time required for a physical signal bit to travel across the distance $d$ of the medium at the propagation speed of light in that medium $s$ ($s \approx 2 \times 10^8\text{ m/s}$).
<!--ID: 1715000009-->

Under what exact condition does packet loss occur at an intermediate router?::When packets arrive faster than the outgoing link transmission rate ($\frac{L \cdot a}{R} > 1$) and completely fill the router's finite memory buffer queue, causing incoming packets to be dropped/discarded.
<!--ID: 1715000010-->

How does the Internet Checksum algorithm detect bit errors?::The sender treats the header as a sequence of 16-bit integers, computes their sum using **1's complement arithmetic**, and inverts all bits. The receiver repeats the sum over all words plus the checksum; if no bits flipped, the result must be all 1s (`0xFFFF`).
<!--SR:!2026-09-17,3,268-->
<!--ID: 1715000022-->

---

## 3. ISP Structure, Transit & Peering

What is the economic and topological difference between IP Transit and Settlement-Free Peering?::* **IP Transit**: Paid commercial service where an upstream provider sells global reachability to the entire Internet ($0.0.0.0/0$).<br>* **Settlement-Free Peering**: Mutual free barter where two ISPs exchange traffic destined exclusively for *each other's direct customers*, never providing free third-party transit.
<!--ID: 1715000023-->

What is Hot-Potato Routing (*Roteamento Batata-Quente*)?::An intra-domain routing policy where an origin ISP hands off an outbound inter-AS packet to the **physically closest egress router** connecting to the neighbor ISP, dumping the cost and distance of long-haul transport onto the destination/neighbor network.
<!--ID: 1715000024-->

What is an IXP (Internet Exchange Point / PTT) and what role does a Route Server play?::An **IXP** is a shared Layer-2 switching fabric where multiple ISPs and CDNs meet to peer traffic directly. An **IXP Route Server** allows multilateral peering: an ISP establishes one BGP session with the route server to exchange routes with all participating members simultaneously.
<!--SR:!2026-09-18,3,268-->
<!--ID: 1715000025-->

---

## 4. Protocol Layering & Encapsulation

What are the 5 layers of the Internet (TCP/IP) model from top to bottom?::1. Application (Aplicação)<br>2. Transport (Transporte)<br>3. Network (Rede)<br>4. Link (Enlace)<br>5. Physical (Física)
<!--ID: 1715000011-->

What are the names of the PDUs (Protocol Data Units) at each of the 5 layers of the TCP/IP stack?::* Application: **Message (Mensagem)**<br>* Transport: **Segment (Segmento)**<br>* Network: **Datagram / Packet (Datagrama / Pacote)**<br>* Link: **Frame (Quadro)**<br>* Physical: **Bits**
<!--ID: 1715000012-->

Why did the TCP/IP model omit OSI Layers 5 (Session) and 6 (Presentation)?::Following the End-to-End argument, if an application requires encryption, compression, or session management, it is implemented directly inside the Application layer (e.g. TLS/HTTPS), keeping the network stack lean and fast.
<!--ID: 1715000013-->

What layers of the protocol stack are processed by a standard Link-Layer Switch vs. a Router vs. a Host?::* **Host**: All 5 layers (L1–L5)<br>* **Router**: Up to Layer 3 (L1–L3: Physical, Link, Network)<br>* **Switch**: Up to Layer 2 (L1–L2: Physical, Link)
<!--SR:!2026-09-18,3,268-->
<!--ID: 1715000014-->

What does a router do to the Layer 2 (Link) header when forwarding a datagram across different physical links?::It strips off the incoming Layer 2 frame header ($H_l$), inspects the Layer 3 IP header ($H_n$) to route the packet, and encapsulates the datagram into a brand-new Layer 2 frame header ($H_l'$) suitable for the next physical link technology.
<!--ID: 1715000015-->

---

## 5. Physical Media, Topologies & Devices

What is the difference in operational layer and collision domain handling between a Hub, a Switch, and a Router?::* **Hub**: Layer 1 (repeats raw bits to all ports; 1 single collision domain).<br>* **Switch**: Layer 2 (forwards frames by MAC address; isolates collision domains per port).<br>* **Router**: Layer 3 (routes datagrams by IP address; isolates broadcast domains and collision domains).
<!--ID: 1715000016-->

Why are copper network cables arranged as twisted pairs (par trançado)?::Twisting pairs of copper conductors cancels out electromagnetic interference (EMI) and crosstalk from adjacent pairs and external electrical noise.
<!--ID: 1715000017-->

Why are radio frequency bands strictly regulated by government agencies rather than freely usable by anyone?::Because the radio frequency spectrum is a shared finite medium; unregulated transmissions would cause overlapping frequency interference, rendering wireless communication unusable.
<!--ID: 1715000018-->

What is the key trade-off of a Star network topology compared to a Bus network topology?::**Star**: Cable cut affects only 1 node and troubleshooting is easy, but the central switch is a single point of failure. **Bus**: Cheaper with minimal cabling, but a single cable break halts the entire network.
<!--SR:!2026-09-16,1,190-->
<!--ID: 1715000019-->
