---
tags:
  - networks/mechanism
  - networks/sockets
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Mechanism: Sockets & Inter-Process Communication (Berkeley API)

### 1. Inter-Process Addressing & Protocol Multiplexing
A physical machine on the Internet can run hundreds of concurrent network applications. When an Ethernet frame arrives at the Network Interface Card (NIC), the OS kernel resolves destination endpoints through a multi-tier hierarchy:

```
+-----------------------------------------------------------------------------------+
| LAYER 2: Link Layer (MAC Address)                                                 |
| Routes frame across the local physical segment to the correct NIC                 |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 3: Network Layer (IP Header)                                                |
| Resolves Host IP Address. Inspects 8-bit "Protocol" field:                        |
|   * Protocol = 6  ===> TCP (Layer 4)                                              |
|   * Protocol = 17 ===> UDP (Layer 4)                                              |
|   * Protocol = 1  ===> ICMP (ping)                                                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 4: Transport Layer (TCP / UDP Header)                                       |
| Inspects 16-bit Destination Port Number (e.g., 80, 443, 53, 22)                   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 5: User-Space Application (The Socket Descriptor)                           |
| OS kernel demultiplexes payload into specific application socket buffer           |
+-----------------------------------------------------------------------------------+
```

$$\text{Application Process Address} = (\text{IP Address}, \text{Port Number})$$

- **Port Number Space ($16$ bits, $0 \text{ to } 65535$):**
  - **Well-Known / Privileged Ports ($0 - 1023$):** Reserved for system services; requires super-user / root privileges (HTTP: 80, HTTPS: 443, SSH: 22, DNS: 53, SMTP: 25).
  - **Registered / System Ports ($1024 - 49151$):** Used by user server applications (MySQL: 3306, Redis: 6379).
  - **Dynamic / Ephemeral Ports ($49152 - 65535$, often starting at $1024$ in Linux):** Assigned automatically by the OS kernel to outbound client connections.

---

### 2. The Socket Abstraction & Socket Types (BSD Unix)
A **Socket** is an operating system abstraction (represented as a standard integer **File Descriptor** in Unix-like systems) that acts as the software API boundary bridging user-space application processes and the kernel's transport protocol stack.

```
+-----------------------------------------------------------+
| User Space       Application Process (e.g., Web Server)  |
|                               |                           |
|                    write() / send() / recv()              |
+===============================v===========================+
| Socket API Boundary (The "Door" into the OS Kernel)       |
+===============================v===========================+
| OS Kernel                     Transport Layer (TCP / UDP) |
+-----------------------------------------------------------+
```

#### The 3 Fundamental Socket Types:
1. **`SOCK_STREAM` (TCP - RFC 793):**
   - Implements a connection-oriented, reliable, bidirectional, in-order **continuous byte stream**.
   - No message boundaries; data is read and written in arbitrary byte chunks.
2. **`SOCK_DGRAM` (UDP - RFC 768):**
   - Implements a connectionless, best-effort **discrete datagram service**.
   - Preserves message boundaries (one `sendto()` = one `recvfrom()`).
3. **`SOCK_RAW` (Network Layer IP / ICMP):**
   - Bypasses the transport layer to access Layer 3 directly.
   - Allows user applications to craft custom IP headers (e.g., `ping` sending raw ICMP packets, Wireshark packet capture). Requires root/admin privileges.

---

### 3. Client Handling & Server Architectures (TCP vs. UDP)

How a server manages multiple simultaneous clients differs fundamentally between TCP and UDP:

```
+-----------------------------------------------------------------------------------+
| TCP SERVER CONCURRENCY (Dedicated Connected Sockets)                              |
|                                                                                   |
|           Welcoming Socket: (*, *, 200.1.1.1, 80) [listen()]                      |
|                                /          \                                       |
|                    (accept() Client A)   (accept() Client B)                      |
|                              /              \                                     |
|                             v                v                                    |
|             [Socket A: 4-Tuple A]        [Socket B: 4-Tuple B]                    |
|             (Buffers for Client A)       (Buffers for Client B)                   |
+-----------------------------------------------------------------------------------+
| UDP SERVER CONCURRENCY (Single Shared Mailbox Socket)                             |
|                                                                                   |
|           Single Shared Socket: (*, *, 200.1.1.1, 53) [bind()]                    |
|                          ^                      ^                                 |
|            (Packet from Client A)   (Packet from Client B)                        |
|                          \                      /                                 |
|                recvfrom() pops packets sequentially with sender IP/Port           |
+-----------------------------------------------------------------------------------+
```

#### A. TCP Multi-Client Handling (Dedicated Sockets):
* **Welcoming Socket:** Listens on the well-known port (`listen()`). It never exchanges application data; its sole purpose is to process incoming connection handshakes (`SYN`).
* **Connected Socket:** When `accept()` completes a 3-way handshake, the kernel creates a **brand-new dedicated socket descriptor** uniquely keyed to that client's 4-tuple:
  $$\text{TCP Demux Key} = (\text{Source IP},\; \text{Source Port},\; \text{Dest IP},\; \text{Dest Port})$$
* **Concurrency Models:**
  - *Multi-Threaded / Thread Pool:* Main loop calls `accept()` and hands the new connected socket descriptor to a worker thread.
  - *I/O Multiplexing (Event Loop):* A single thread uses `epoll` (Linux) or `kqueue` (BSD/macOS) to monitor thousands of open client socket descriptors non-blockingly (Nginx, Node.js).

#### B. UDP Multi-Client Handling (Single Shared Socket):
* The server creates and binds **only ONE socket** for its entire lifetime.
* There is no `listen()` and no `accept()`.
* All incoming datagrams from all clients across the world land in the **exact same kernel receive queue**.
* The server calls `recvfrom()` in a loop. Each call pops the next available datagram and captures the sender's address.

---

### 4. Deep Dive: `recvfrom()` vs. `recv()` (The Out-Parameter Mechanism)

A common point of confusion is the name **`recvfrom`**:

> [!important] Why is it named `recvfrom`?
> In everyday speech, *"receive from Alice"* sounds like an instruction to only accept Alice's messages.
> In POSIX/C sockets, `from_addr` is an **OUTPUT parameter** (an out-parameter pointer).
> **`recvfrom` means:** *"Receive whatever packet is next in the queue, and tell me who it came **FROM**."*

```c
struct sockaddr_in client_addr;
socklen_t addr_len = sizeof(client_addr);
char buffer[1024];

// The server blocks here. client_addr is passed as EMPTY memory:
int bytes = recvfrom(
    server_socket, 
    buffer, 
    sizeof(buffer), 
    0, 
    (struct sockaddr *)&client_addr,   // <--- Kernel WRITES sender info here!
    &addr_len
);
```

#### How the UDP Socket Knows WHO and WHERE the Client Is:
Every UDP datagram carries the sender's identity stamped on its outer IP and UDP headers:
1. When a packet arrives, the kernel extracts **`Source IP`** (from IP header) and **`Source Port`** (from UDP header).
2. The kernel copies the application payload into `buffer` and writes the extracted `(Source IP, Source Port)` directly into the application's `client_addr` struct.
3. To reply, the server passes `client_addr` back to the kernel as a destination input in **`sendto()`**:
   ```c
   sendto(server_socket, reply_data, len, 0, (struct sockaddr *)&client_addr, addr_len);
   ```

#### Connecting a UDP Socket (`connect()` on UDP):
An application can optionally call `connect()` on a UDP socket. This does **not** send any handshake over the network; it simply registers a filter with the local kernel:
* The kernel will only deliver packets originating from that specific `(IP, Port)`.
* Allows using standard `send()` and `recv()` instead of `sendto()` and `recvfrom()`.

---

### 5. Berkeley Socket System Calls Summary

```
TCP Client-Server Lifecycle:
Server: socket() -> bind() -> listen() -> accept() [Blocks] -> read()/write() -> close()
Client: socket() -----------------------> connect() ---------> write()/read() -> close()

UDP Client-Server Lifecycle:
Server: socket() -> bind() -------------> recvfrom() [Blocks] -> sendto() ------> close()
Client: socket() -----------------------> sendto() -----------> recvfrom() -----> close()
```

| Function Call | Socket Type | Role / Operation |
| :--- | :--- | :--- |
| **`socket(domain, type, protocol)`** | TCP & UDP | Allocates a new socket endpoint descriptor in the OS kernel. |
| **`bind(sockfd, addr, len)`** | TCP & UDP | Associates socket with a specific local IP address and port number. |
| **`listen(sockfd, backlog)`** | TCP only | Transitions socket into passive listening mode and allocates handshake queue. |
| **`accept(sockfd, addr, len)`** | TCP only | Blocks until client completes 3-way handshake; returns a **new dedicated connection socket**. |
| **`connect(sockfd, addr, len)`** | TCP & UDP | In TCP: initiates 3-way handshake. In UDP: sets default remote peer address filter. |
| **`send()` / `recv()`** (or `write`/`read`) | TCP | Transmits/reads data over an established stream connection. |
| **`sendto(sockfd, buf, len, fl, dst, dstlen)`** | UDP | Transmits datagram to explicitly specified destination IP and Port. |
| **`recvfrom(sockfd, buf, len, fl, src, srclen)`**| UDP | Reads datagram and populates `src` struct with sender's IP and Port. |
| **`close(sockfd)`** | TCP & UDP | Releases socket descriptor; in TCP, initiates 4-way `FIN`/`ACK` teardown. |

---

### Summary
> [!abstract] Sockets & Inter-Process Communication Takeaway
> - **Socket:** The OS API boundary (file descriptor) bridging user-space application logic and kernel transport services.
> - **Socket Types:** `SOCK_STREAM` (TCP, byte stream), `SOCK_DGRAM` (UDP, datagrams), `SOCK_RAW` (IP/ICMP, root access).
> - **TCP Server Concurrency:** Uses a welcoming socket (`listen`) to accept handshakes, returning a new dedicated socket (`accept`) per client keyed by a 4-tuple.
> - **UDP Server Concurrency:** Uses a single shared socket; `recvfrom()` extracts sender `(IP, Port)` from incoming packet headers into an out-parameter.
