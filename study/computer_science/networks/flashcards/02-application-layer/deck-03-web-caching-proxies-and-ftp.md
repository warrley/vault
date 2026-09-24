---
tags:
  - flashcards
  - flashcards/networks/app/caching-ftp
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: Web Caching, Proxies & FTP

What is an HTTP Proxy (Web Cache) and what are its primary network benefits?::A network entity that stores copies of recently requested web objects locally to satisfy client requests on behalf of the origin server.<br>* **Benefits**: Drastically reduces response time for local clients, reduces traffic on the institutional access link bottleneck, and reduces load on the origin server.
<!--ID: 1726300001-->

What is an HTTP Transparent Proxy (Intercepting Proxy) and how is it implemented at the network level?::A proxy configuration where the client browser requires **zero manual configuration**. The institutional edge router intercepts all outbound TCP packets destined for port 80 and uses **Destination NAT (DNAT) / Policy Routing (e.g. `iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 3128`)** to redirect the TCP streams to the local proxy daemon.
<!--ID: 1726300002-->

What request header and response status code are used by a Web Cache to perform a Conditional GET validation?::* **Request Header**: `If-Modified-Since: <cached_last_modified_date>`<br>* **Response if object has NOT changed**: `HTTP/1.1 304 Not Modified` (sent with **no entity body**, saving bandwidth).<br>* **Response if object HAS changed**: `HTTP/1.1 200 OK` (containing the updated object in the entity body).
<!--ID: 1726300003-->

Why is FTP described as an "Out-of-Band" protocol, unlike HTTP?::FTP uses **two separate parallel TCP connections**:
1. A persistent **Control Connection on Port 21** used exclusively for user authentication, directory browsing, and command transfer.
2. Separate, transient **Data Connections on Port 20 / Ephemeral ports** opened dynamically for each individual file transfer.
HTTP is "In-Band" because request/response headers and data payload share the exact same TCP stream.
<!--ID: 1726300004-->

How does FTP maintain state regarding a client session, unlike stateless HTTP?::An FTP server is strictly **stateful**: it maintains the client's current working directory path, active authentication credentials, and transfer mode across the control connection for the entire duration of the session.
<!--ID: 1726300005-->
