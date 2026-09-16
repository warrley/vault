---
tags:
  - networks/mechanism
  - networks/sockets
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Mechanism: Sockets & Inter-Process Communication

### 1. Inter-Process Addressing
A host on the Internet can run hundreds of concurrent network processes. An IP address alone identifies only the network interface card of a physical host.

To address a specific application process, the network uses a **two-level addressing tuple**:
$$\text{Process Address} = (\text{IP Address}, \text{Port Number})$$

- **IP Address (32-bit IPv4 / 128-bit IPv6):** Directs packets hop-by-hop across intermediate routers to the destination host.
- **Port Number (16-bit integer, $0 \text{ to } 65535$):** Demultiplexes incoming transport segments inside the host's kernel to the specific application socket buffer.
  - **Well-Known Ports ($0 - 1023$):** Standardized by IANA (HTTP: 80, HTTPS: 443, SMTP: 25, DNS: 53, SSH: 22, FTP: 20/21).
  - **Registered Ports ($1024 - 49151$):** Used by user applications.
  - **Dynamic / Ephemeral Ports ($49152 - 65535$):** Automatically assigned by the OS kernel to client processes for outbound connections.

---

### 2. The Socket Abstraction
A **Socket** is the software interface (API) that bridges the boundary between the **user-space application program** and the **operating system kernel's transport layer**.

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

### 3. Core Berkeley Socket System Calls

#### For a TCP Stream Server (Connection-Oriented):
1. `socket(AF_INET, SOCK_STREAM, 0)`: Allocates an OS socket endpoint.
2. `bind(sockfd, &addr, sizeof(addr))`: Associates the socket with a specific local IP address and port number.
3. `listen(sockfd, backlog)`: Transitions the socket into passive mode to listen for incoming client connection requests.
4. `accept(sockfd, &client_addr, &len)`: Blocks until a client completes the 3-way handshake, returning a **new dedicated connection socket descriptor** for that client.
5. `recv()` / `send()` (or `read()` / `write()`): Reads/writes bytes over the established TCP stream.
6. `close(conn_sock)`: Closes the active TCP connection.

#### For a TCP Client:
1. `socket()`: Creates socket descriptor.
2. `connect(sockfd, &server_addr, sizeof(server_addr))`: Initiates the TCP 3-way handshake to the server's IP and port.
3. `send()` / `recv()`: Exchanging data.
4. `close()`: Terminating the connection.

#### For UDP Sockets (Connectionless Datagram):
- Uses `socket(AF_INET, SOCK_DGRAM, 0)`.
- No `listen()`, `accept()`, or `connect()`.
- Data is transmitted using `sendto(sockfd, buf, len, flags, &dest_addr, addrlen)` and received using `recvfrom(...)` because each packet carries its destination IP/Port independently.

---

### Summary
> [!abstract] Key Takeaways: Sockets & Process Identification
> - A network process is uniquely identified across the Internet by `(IP Address, Port Number)`.
> - A **Socket** is the API boundary between user-space application logic and kernel transport services.
> - TCP server lifecycle: `socket` $\to$ `bind` $\to$ `listen` $\to$ `accept` $\to$ `recv/send` $\to$ `close`.
