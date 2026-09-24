---
tags:
  - flashcards
  - flashcards/networks/app/http
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: HTTP Protocol, Cookies & RTT Formulations

Why is HTTP described as a "stateless" protocol, and how do web applications track state using Cookies?::HTTP is stateless because the server maintains **zero memory/state regarding past client requests**. To maintain sessions (e.g. shopping carts, logins), the server sends a `Set-Cookie: session_id=XYZ` header in its response. The client browser stores the cookie and automatically includes `Cookie: session_id=XYZ` in all subsequent requests to that domain.
<!--ID: 1726200001-->

What are the 5 core differences between the HTTP `GET` and `POST` form methods?::1. **Data Placement**: `GET` appends parameters to the URL query string (`/path?k=v`); `POST` places data in the HTTP Request **Entity Body**.<br>2. **Idempotency**: `GET` is idempotent (safe to repeat); `POST` is non-idempotent (may create new records).<br>3. **Caching**: `GET` responses are cached by default; `POST` is uncached by default.<br>4. **Payload Capacity**: `GET` is restricted by URL length limits ($\approx 2-8\text{ KB}$); `POST` supports arbitrary large payload sizes.<br>5. **Security Exposure**: `GET` exposes sensitive form inputs in URLs, history, and access logs; `POST` conceals data inside encrypted TLS payloads.
<!--ID: 1726200002-->

What is the mathematical formula for total page retrieval time under Non-Persistent HTTP (serial) for a base HTML file referencing $M$ objects?::$$\text{Total Time}_{\text{Non-Persistent}} = \mathbf{2(M + 1) \cdot RTT} + \sum d_{\text{trans}}$$
(Requires $1\text{ RTT TCP Handshake} + 1\text{ RTT HTTP GET}$ for the base HTML, plus $2\text{ RTTs}$ individually for each of the $M$ referenced objects).
<!--ID: 1726200003-->

What is the formula for total page retrieval time under Persistent HTTP with Pipelining?::$$\text{Total Time}_{\text{Pipelined}} = \mathbf{3 \cdot RTT} + \sum d_{\text{trans}}$$
($1\text{ RTT}$ for initial TCP Handshake, $1\text{ RTT}$ for base HTML file, and $1\text{ RTT}$ to retrieve all $M$ referenced objects requested back-to-back simultaneously).
<!--ID: 1726200004-->

Given a base HTML page containing 4 separate JPEG images, calculate the total RTT response time for Non-Persistent HTTP vs Persistent HTTP with Pipelining.::* **Non-Persistent (serial)**: $2(M + 1) \cdot RTT = 2(4 + 1) = \mathbf{10 \cdot RTT}$.<br>* **Persistent with Pipelining**: $1 \text{ (handshake)} + 1 \text{ (base)} + 1 \text{ (all 4 images)} = \mathbf{3 \cdot RTT}$.
<!--ID: 1726200005-->
