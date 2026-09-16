---
tags:
  - networks/protocol
  - networks/http
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Protocol: Hypertext Transfer Protocol (HTTP)

### 1. Architectural Characteristics
**HTTP (RFC 1945/2616/7230)** is an application-layer request-response protocol operating over **TCP port 80** (or port 443 for HTTPS over TLS).

> [!important] The Stateless Nature of HTTP
> HTTP is fundamentally **stateless**. An HTTP server stores no state regarding past client requests. If a client requests the identical object twice within one millisecond, the server processes each request as entirely independent.

#### State Tracking via Cookies (RFC 6265)
Because web applications (e.g., e-commerce shopping carts, authenticated sessions) require state, HTTP uses **Cookies**:
1. Server issues `Set-Cookie: session_id=abc123xyz` in its HTTP response header.
2. The browser stores the cookie locally mapped to the domain.
3. Subsequent HTTP requests to that domain automatically include the header `Cookie: session_id=abc123xyz`.
4. The server uses the `session_id` to retrieve user session data from its backend database.

---

### 2. HTTP Form Methods: GET vs. POST
*(Addresses Exercise 4)*

When an HTML `<form>` is submitted, the browser encodes input fields and sends them via one of two methods:

```
+-----------------------------------------------------------------------------------+
| 1. GET Method: Form parameters encoded directly in Request Line URL Query String  |
| GET /search?query=networks&author=kurose HTTP/1.1                                  |
| Host: www.example.com                                                             |
| [No Message Body]                                                                 |
+-----------------------------------------------------------------------------------+
| 2. POST Method: Form parameters encoded in Request Message Entity Body            |
| POST /login HTTP/1.1                                                              |
| Host: www.example.com                                                             |
| Content-Type: application/x-www-form-urlencoded                                   |
| Content-Length: 25                                                                |
|                                                                                   |
| username=alice&pass=secret                                                        |
+-----------------------------------------------------------------------------------+
```

#### Comparison Table:
| Dimension | `GET` Method | `POST` Method |
| :--- | :--- | :--- |
| **Data Location** | URL Query string (`?key=val&key2=val2`) | Request Entity Body (payload) |
| **Idempotency** | Yes (repeated calls produce no side-effects) | No (may create/update records) |
| **Caching / History** | Cached by browsers and proxies; visible in logs | Never cached by default; omitted from history |
| **Payload Size** | Limited by maximum URL length ($\approx 2 \text{ KB} - 8 \text{ KB}$) | Arbitrary size (can upload gigabyte files) |
| **Security Risk** | Critical credentials leaked in URL, logs, and screen | Concealed from URL (encrypted under TLS payload) |

---

### 3. Non-Persistent vs. Persistent HTTP ($RTT$ Derivations)

Let $RTT$ (Round-Trip Time) be the time for a small packet to travel from client to server and back. Suppose a web page has **1 base HTML file** and **$M$ referenced objects** (images, stylesheets).

#### A. Non-Persistent HTTP (HTTP/1.0 default)
Each TCP connection is closed immediately after transmitting a single object.
- **Base HTML Retrieval:**
  - $1 \text{ RTT}$ (TCP 3-way handshake: SYN $\to$ SYN-ACK)
  - $1 \text{ RTT}$ (HTTP GET $\to$ Base HTML response)
  - $\text{Time}_{\text{base}} = 2 \text{ RTT}$
- **Referenced Objects (Sequential / Serial):**
  - For each of the $M$ objects: $1 \text{ RTT handshake} + 1 \text{ RTT data} = 2 \text{ RTT}$.
  - $\text{Time}_{\text{objects}} = 2M \text{ RTT}$.

$$\text{Total Response Time}_{\text{Non-Persistent}} = 2(M + 1) \cdot RTT + \sum \text{Transmission Delays}$$

*(Example: For $M = 3$ images $\implies 2(3 + 1) \cdot RTT = \mathbf{8 \cdot RTT}$).*

#### B. Persistent HTTP without Pipelining (HTTP/1.1 default)
The TCP connection remains open across requests.
- $1 \text{ RTT}$ (Initial TCP Handshake)
- $1 \text{ RTT}$ (Base HTML request/response)
- $1 \text{ RTT}$ per referenced object (sequential wait): $M \cdot RTT$.

$$\text{Total Response Time}_{\text{Persistent, No Pipelining}} = (M + 2) \cdot RTT + \sum \text{Transmission Delays}$$

#### C. Persistent HTTP with Pipelining
The client transmits all $M$ requests back-to-back immediately upon parsing the base HTML:
- $1 \text{ RTT}$ (TCP Handshake)
- $1 \text{ RTT}$ (Base HTML request/response)
- $1 \text{ RTT}$ (All $M$ object requests transmitted simultaneously)

$$\text{Total Response Time}_{\text{Persistent, Pipelined}} = \mathbf{3 \cdot RTT} + \sum \text{Transmission Delays}$$

---

### RTT Delay Formulation
> [!abstract] Mathematical Formula Reference
> - **Non-Persistent (Serial):** $T = 2(M + 1) \cdot RTT$
> - **Persistent (No Pipelining):** $T = (M + 2) \cdot RTT$
> - **Persistent (Pipelined):** $T = 3 \cdot RTT$
