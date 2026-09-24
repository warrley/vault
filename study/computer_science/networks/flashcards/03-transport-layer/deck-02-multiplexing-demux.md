---
tags:
  - flashcards
  - flashcards/networks/transport/demux
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: Multiplexing & Demultiplexing

What is the operational definition of Multiplexing at the Transport Layer sender?::Gathering data chunks from multiple application sockets in user space, encapsulating them with transport headers containing Source and Destination Port numbers, and passing the segments down to the Network Layer (IP).
<!--ID: 1727200001-->

What is the operational definition of Demultiplexing at the Transport Layer receiver?::Examining the header fields of an incoming transport-layer segment to deliver its payload into the exact corresponding application socket buffer in kernel space.
<!--ID: 1727200002-->

What is the bit-width of a transport layer Port Number and what are the three standard IANA port ranges?::Port numbers are **16-bit unsigned integers** ($0 \text{ to } 65535 = 2^{16} - 1$):<br>1. **Well-Known Ports ($0 - 1023$)**: Reserved for standard system protocols (HTTP 80, HTTPS 443, SSH 22, DNS 53, SMTP 25).<br>2. **Registered Ports ($1024 - 49151$)**: Assigned to user application services (MySQL 3306, Redis 6379).<br>3. **Dynamic / Ephemeral Ports ($49152 - 65535$)**: Automatically allocated by the OS kernel for outbound client connections.
<!--ID: 1727200003-->

What fields constitute the Demultiplexing Key for a UDP socket vs a TCP socket?::* **UDP Demux Key (2-Tuple)**: `(Destination IP Address, Destination Port Number)`.<br>* **TCP Demux Key (4-Tuple)**: `(Source IP Address, Source Port Number, Destination IP Address, Destination Port Number)`.
<!--ID: 1727200004-->

If Host A (IP `10.0.0.1`, port 50000) and Host B (IP `10.0.0.2`, port 50000) both send UDP datagrams to Server C (IP `10.0.0.99`) on port 53, how are they demultiplexed?::Both UDP datagrams are delivered into the **exact same UDP socket buffer** on Server C because UDP demux matches only the destination IP and port.
<!--ID: 1727200005-->

Why does the UDP header contain a Source Port number if demultiplexing only checks the Destination Port?::The Source Port acts as the **return address** so the receiving application process can extract `(Source IP, Source Port)` and address its response datagram back to the sender.
<!--ID: 1727200006-->

Why does TCP demultiplexing require a full 4-tuple while UDP only needs a 2-tuple?::Because TCP is stateful and connection-oriented. The OS kernel must maintain a dedicated **Transmission Control Block (TCB)** (sequence numbers, ACKs, send/receive sliding window buffers, $cwnd$, $rwnd$, and timers) for each client connection. Sharing a socket between clients would corrupt the byte stream state.
<!--ID: 1727200007-->

What is the difference between a TCP Welcoming (Listening) Socket and a Connected Socket?::* **Welcoming / Listening Socket**: Bound to the well-known service port (e.g., port 80); passively listens for incoming TCP connection requests (`SYN` packets) to execute the 3-way handshake.<br>* **Connected Socket**: A brand-new dedicated socket descriptor returned by `accept()` upon handshake completion, uniquely bound to that client's 4-tuple to handle all subsequent data transfers.
<!--ID: 1727200008-->

Host A and Host B both open 2 concurrent TCP connections to Server S (port 80). If both hosts happen to use ephemeral source ports 55000 and 55001, how many total sockets exist on Server S?::**5 sockets total**: 4 dedicated connection sockets (each uniquely keyed by its distinct 4-tuple: `(10.0.0.1, 55000, S, 80)`, `(10.0.0.1, 55001, S, 80)`, `(10.0.0.2, 55000, S, 80)`, `(10.0.0.2, 55001, S, 80)`) $+$ 1 welcoming socket `(*, *, S, 80)`.
<!--ID: 1727200009-->
