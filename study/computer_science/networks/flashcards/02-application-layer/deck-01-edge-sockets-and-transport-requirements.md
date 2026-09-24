---
tags:
  - flashcards
  - flashcards/networks/app/sockets
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: Application Layer Edge & Sockets

In which part of the physical network topology are application-layer protocols implemented, and why?::Exclusively on **end systems (hosts) at the network edge**. Network core devices (routers and link switches) process packets strictly up to Layer 3/2 to maximize line-rate packet forwarding throughput and preserve the **End-to-End Principle**, allowing applications to innovate without altering the network core.
<!--ID: 1726100001-->

In a network transmission, what two identifiers are required to uniquely address an application process on a remote machine?::The **IP Address (Layer 3)** to route the packet across the global Internet to the destination host interface, and the **Port Number (Layer 4, 16-bit integer $0-65535$)** to demultiplex the payload inside the kernel to the specific application socket.
<!--ID: 1726100002-->

What is a Socket in computer networks?::The software API boundary (the "door") bridging a user-space application process and the operating system kernel's transport layer (TCP or UDP).
<!--ID: 1726100003-->

What are the 3 primary socket types supported by the Berkeley Sockets API?::1. **`SOCK_STREAM` (TCP)**: Connection-oriented, reliable continuous byte stream.<br>2. **`SOCK_DGRAM` (UDP)**: Connectionless, best-effort discrete datagrams.<br>3. **`SOCK_RAW` (IP/ICMP)**: Direct access to Layer 3; allows constructing custom IP headers (requires root privileges, used by `ping` and Wireshark).
<!--ID: 1726100007-->

What is the sequence of Berkeley socket system calls executed by a connection-oriented (TCP) server process?::`socket()` $\to$ `bind()` $\to$ `listen()` $\to$ `accept()` $\to$ `recv()` / `send()` $\to$ `close()`.
<!--ID: 1726100004-->

How does a TCP server handle multiple concurrent clients compared to a UDP server?::* **TCP Server**: Uses a welcoming socket (`listen()`) to accept connections, with `accept()` returning a **new dedicated socket descriptor for each client** (keyed by the 4-tuple), handled concurrently via threads, processes, or `epoll`.<br>* **UDP Server**: Uses a **single shared socket**; all clients send datagrams into the same queue, and the server reads them sequentially using `recvfrom()` or offloads to a worker pool.
<!--ID: 1726100008-->

Why is the UDP receive function named `recvfrom()`, and how does it discover the client's address?::In `recvfrom(sockfd, buf, len, flags, &from_addr, &addrlen)`, the `from_addr` parameter is an **out-parameter** (output pointer). The kernel extracts the **Source IP** and **Source Port** from the incoming packet's headers and **populates `from_addr`**, informing the application who the packet was received *FROM*.
<!--ID: 1726100009-->

What happens when an application calls `connect()` on a UDP socket?::It does **NOT send any network handshake** over the wire. It registers an address filter in the local OS kernel: the socket will only accept datagrams from that specific remote `(IP, Port)`, and enables using standard `send()` and `recv()` without specifying addresses each time.
<!--ID: 1726100010-->

What are the 4 fundamental transport service dimensions an application can require from lower layers?::1. **Data Loss Tolerance**: 100% reliability vs loss tolerance.<br>2. **Throughput / Bandwidth**: Minimum guaranteed transmission rate.<br>3. **Timing / Latency**: Strict delay upper bounds (e.g. $\le 50\text{ ms}$).<br>4. **Security & Encryption**: Confidentiality, integrity, and endpoint authentication (provided via TLS).
<!--ID: 1726100005-->

Which of the 4 transport dimensions does TCP guarantee natively, and which does it NOT guarantee?::* **Guarantees natively**: 100% Reliable Data Transfer and In-order delivery.<br>* **Does NOT guarantee**: Minimum throughput (bandwidth), maximum delay (latency bounds), or native security (requires TLS).
<!--ID: 1726100006-->
