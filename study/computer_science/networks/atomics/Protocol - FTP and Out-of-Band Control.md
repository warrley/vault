---
tags:
  - networks/protocol
  - networks/ftp
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Protocol: File Transfer Protocol (FTP) & Out-of-Band Control
*(Addresses Exercise 6)*

### 1. Dual-Connection Architecture (RFC 959)
Unlike HTTP or SMTP, **FTP (File Transfer Protocol)** separates control commands and actual file data into **two separate, parallel TCP connections**:

```
+---------------+                                        +---------------+
|               | ====== Control Connection (Port 21) ==> |               |
|  FTP Client   |   (Commands: USER, PASS, LIST, RETR)   |  FTP Server   |
|               |   (Maintained open throughout session) |               |
|               |                                        |               |
|               | <==== Data Connection (Port 20/Eph.) == |               |
|               |   (Carries raw file bytes / directory) |               |
|               |   (Opens per file, closes on finish)   |               |
+---------------+                                        +---------------+
```

---

### 2. Why FTP is Called "Out-of-Band"
*(Directly solves Exercise 6)*

- **In-Band Protocol (e.g., HTTP):** Control information (request methods, header lines, response status codes) and the actual resource payload (HTML, JPEG, video) travel across the **exact same TCP connection**.
- **Out-of-Band Protocol (FTP):** Control signaling (user authentication, directory navigation, file transfer commands) is sent over a dedicated **Control Connection (TCP Port 21)**, while the raw file data is transferred over an entirely separate **Data Connection (TCP Port 20 in Active mode, or an ephemeral port in Passive mode)**.

---

### 3. Active vs. Passive FTP Modes
1. **Active Mode (`PORT` command):**
   - Client opens control connection to server port 21.
   - Client opens a listening port $N$ and tells server: `PORT <client_ip>,<N>`.
   - Server initiates a TCP connection from **server port 20** to client port $N$ to transfer data.
   - *Problem:* Blocked by modern client-side NATs/firewalls (firewalls block incoming connections from the server).
2. **Passive Mode (`PASV` command):**
   - Client sends `PASV` command over control connection.
   - Server opens an unprivileged listening port $P$ and tells client: `227 Entering Passive Mode (<server_ip>,<P>)`.
   - Client initiates the TCP connection from an ephemeral port to server port $P$.
   - *Advantage:* Works smoothly through client-side firewalls/NATs because all connections originate from the client.

---

### Summary
> [!abstract] Key Takeaways: FTP Control Architecture
> - FTP is **out-of-band** because control signaling (port 21) and file data transfers (port 20/ephemeral) use separate TCP connections.
> - The control connection remains open for the entire user session, while a new data connection is spawned and torn down for each individual file transfer.
