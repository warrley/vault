---
tags:
  - flashcards
  - flashcards/networks
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: Transport Layer (Services, Demux, UDP & Checksum)

## 1. Transport Layer Services & Principles

What is the fundamental distinction between the Transport Layer and the Network Layer?::The **Network Layer** provides logical communication between **hosts** (host-to-host across intermediate routers). The **Transport Layer** provides logical communication between **application processes** running on different hosts (process-to-process via sockets).
<!--ID: 1727000001-->

In the Kurose household analogy for transport services, what corresponds to: Houses, Cousins, Letters, Mail Sorters (Ann/Bill), and the Postal Service?::* **Houses** = Hosts (End systems)<br>* **Cousins** = Application processes<br>* **Letters inside envelopes** = Application messages<br>* **Ann & Bill (mail sorters)** = Transport Layer protocol<br>* **Postal Service (trucks/planes)** = Network Layer (IP).
<!--ID: 1727000002-->

What transport services can TCP guarantee on top of best-effort IP, and what can it NOT guarantee?::* **Can guarantee**: 100% reliable data transfer (no loss/corruption), in-order byte stream delivery, flow control, and congestion control.<br>* **Cannot guarantee**: Hard delay/latency upper bounds (e.g. $\le 20\text{ ms}$) and minimum throughput/bandwidth guarantees (e.g. $\ge 10\text{ Mbps}$).
<!--ID: 1727000003-->

Where are transport-layer protocols implemented in the Internet architecture, and why?::Exclusively on **end systems (hosts)** at the network edge. Network core devices (routers and link switches) process packets strictly up to Layer 3/Layer 2 to preserve line-rate packet forwarding throughput and respect the **End-to-End Principle**.
<!--ID: 1727000004-->

What are the header sizes of a standard UDP datagram vs a standard TCP segment?::* **UDP Header**: Fixed **8 bytes** (4 fields of 16 bits each).<br>* **TCP Header**: Minimum **20 bytes** (up to 60 bytes with header options).
<!--ID: 1727000005-->

---

## 2. Multiplexing & Demultiplexing Mechanics

What are the definitions of Multiplexing and Demultiplexing at the Transport Layer?::* **Multiplexing (at Sender)**: Gathering data chunks from multiple application sockets, encapsulating them with transport headers (Source/Destination Port numbers), and passing segments to the Network Layer.<br>* **Demultiplexing (at Receiver)**: Inspecting incoming transport header fields to deliver each segment's payload to the exact corresponding socket buffer.
<!--ID: 1727000006-->

What is the size of a transport layer Port Number and what are the three standard IANA port ranges?::Port numbers are **16-bit unsigned integers** ($0 \text{ to } 65535$):<br>1. **Well-Known Ports ($0 - 1023$)**: Reserved for standard system services (HTTP 80, HTTPS 443, SSH 22, DNS 53).<br>2. **Registered Ports ($1024 - 49151$)**: Registered for user application services.<br>3. **Dynamic / Ephemeral Ports ($49152 - 65535$)**: Assigned automatically by the OS kernel for client outbound connections.
<!--ID: 1727000007-->

What fields constitute the Demultiplexing Key for a UDP socket vs a TCP socket?::* **UDP Socket Key (2-Tuple)**: `(Destination IP Address, Destination Port Number)`.<br>* **TCP Socket Key (4-Tuple)**: `(Source IP Address, Source Port Number, Destination IP Address, Destination Port Number)`.
<!--ID: 1727000008-->

If Host A (port 52000) and Host B (port 52000) both send UDP datagrams to Server C on port 53, how are they demultiplexed on Server C?::Both UDP datagrams are delivered into the **exact same UDP socket buffer** on Server C because UDP demux depends solely on destination IP and destination port.
<!--ID: 1727000009-->

Why does the UDP header contain a Source Port number if UDP demultiplexing only uses the Destination Port?::The Source Port provides the **return address** so the receiving application process can extract it from the datagram and address its reply datagram back to the sender.
<!--ID: 1727000010-->

Why does TCP demultiplexing require a 4-tuple while UDP demultiplexing requires only a 2-tuple?::Because TCP is connection-oriented and stateful. The OS kernel must maintain an independent **Transmission Control Block (TCB)** (with sequence numbers, ACKs, send/receive buffers, $cwnd$, $rwnd$, and timers) for every active connection. Delivering segments from different clients into the same socket would corrupt the connection state.
<!--ID: 1727000011-->

What is the difference between a TCP Welcoming (Listening) Socket and a Connected Socket?::* **Welcoming / Listening Socket**: Bound to the well-known server port (e.g. port 80); listens for incoming TCP connection requests (`SYN` packets) to complete the 3-way handshake.<br>* **Connected Socket**: A new, dedicated socket descriptor created by `accept()` upon handshake completion, uniquely bound to the specific client's 4-tuple to handle all subsequent data transfers.
<!--ID: 1727000012-->

Host A and Host B both open 2 concurrent TCP connections to Server S (port 80). If both hosts coincidentally use ephemeral source ports 55000 and 55001, how many total sockets exist on Server S?::**5 sockets total**: 4 dedicated connection sockets (each uniquely keyed by its 4-tuple) $+$ 1 welcoming/listening socket on port 80.
<!--ID: 1727000013-->

---

## 3. UDP Protocol & The Internet Checksum Algorithm

What are the 4 main reasons an application developer chooses UDP over TCP?::1. **Fine-grained rate control**: Transmits data immediately without being throttled by TCP congestion control.<br>2. **No connection setup delay**: Sends data in the 1st packet ($0\text{ RTT}$ setup vs $1\text{ RTT}$ TCP handshake).<br>3. **Stateless server architecture**: Zero connection state/buffers allocated per client, supporting vastly more concurrent clients.<br>4. **Low header overhead**: Fixed 8-byte header vs 20–60-byte TCP header.
<!--ID: 1727000014-->

What are the 4 fields in the UDP segment header?::1. **Source Port Number** (16 bits)<br>2. **Destination Port Number** (16 bits)<br>3. **Total Length** (16 bits, header $+$ payload in bytes)<br>4. **Checksum** (16 bits).
<!--ID: 1727000015-->

How does a sender calculate the Internet Checksum over a transport segment?::1. Divide segment bytes into **16-bit words**.<br>2. Sum the words using **1's complement addition** (wrap any overflow carry bit past the 16th bit back and add it to the LSB).<br>3. Compute the **bitwise inversion (1's complement)** of the sum ($0 \to 1, 1 \to 0$).<br>4. Insert this value into the Checksum header field.
<!--ID: 1727000016-->

How does a receiver verify the integrity of an incoming segment using the Internet Checksum?::The receiver adds all 16-bit words of the segment **plus the received Checksum field** using 1's complement addition:<br>* If the sum is **`1111 1111 1111 1111` (`0xFFFF`)**, no bit errors are detected.<br>* If **any bit in the sum is `0`**, an error is detected and the segment is discarded.
<!--ID: 1727000017-->

Can the Internet Checksum correct bit errors, and can it detect all possible multi-bit errors?::* **No error correction**: Checksum only detects errors; it cannot identify which bit was corrupted to fix it.<br>* **Undetected compensating errors**: If one bit flips from $0 \to 1$ and another bit in the same column flips from $1 \to 0$, the sum is identical, so the error passes undetected.
<!--ID: 1727000018-->
