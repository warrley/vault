---
tags:
  - networks/mechanism
  - networks/caching
  - networks/http
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Mechanism: Web Caching & HTTP Proxies
*(Addresses Exercise 5)*

### 1. Web Proxy (Cache) Architecture
A **Web Cache (Proxy Server)** is an intermediate network server that satisfies HTTP requests on behalf of an origin web server.

```
                    +--------------------+
                    | Origin Web Server  | (Remote Internet)
                    +---------^----------+
                              | Internet Access Link (High Latency / Bottleneck)
                              v
[Client 1] -----\   +--------------------+
                 ==>| Local Proxy Cache  | (Institutional LAN / ISP)
[Client 2] -----/   +--------------------+
```

#### Request Flow:
1. Client sends an HTTP request to the Proxy Cache.
2. If **Cache Hit** (object present and fresh): Proxy returns the cached object directly with minimal latency and $0\text{ bps}$ access link consumption.
3. If **Cache Miss** (object absent or stale): Proxy opens a TCP connection to the origin server, retrieves the object, stores a local copy, and returns it to the client.

---

### 2. Standard vs. Transparent Proxy
*(Directly solves Exercise 5)*

#### A. Standard (Explicit) Proxy:
- The user agent (browser) is explicitly configured with the IP address and port of the proxy (e.g., `proxy.ufc.br:8080`).
- The browser constructs the HTTP request line with the full absolute URI (`GET http://www.google.com/index.html HTTP/1.1`) and sends packets directly to the proxy's IP.

#### B. Transparent Proxy (Intercepting Proxy):
- The client browser is **completely unaware** of the proxy's existence (zero configuration on client devices).
- **How it is implemented:**
  1. An edge router, gateway, or firewall at the network perimeter inspects all outbound traffic.
  2. The router detects outbound TCP packets destined for port 80 (`HTTP`).
  3. Using **Destination Network Address Translation (DNAT) / Policy Routing (e.g., Linux `iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080`)**, the router silently intercepts the traffic and redirects it to the local proxy server daemon.
  4. The proxy terminates the TCP connection, handles the HTTP transaction, fetches upstream resources if required, and returns the response spoofing the origin server's identity to the client.

---

### 3. Cache Validation: The Conditional GET
To ensure the proxy does not serve stale (outdated) content without needlessly re-downloading unchanged files, HTTP uses the **Conditional GET**:

```
Proxy Cache                                                   Origin Server
     |                                                              |
     | ----- GET /pic.jpg HTTP/1.1 -------------------------------> |
     |       Host: www.site.com                                     |
     |       If-Modified-Since: Wed, 10 Sep 2025 09:00:00 GMT      |
     |                                                              |
     | <---- HTTP/1.1 304 Not Modified ---------------------------- | (No entity body!)
     |       [Cache is confirmed valid, served to client]           |
```

- **If the object has NOT changed:** Origin server replies with **`HTTP/1.1 304 Not Modified`** containing **no message body**.
- **If the object HAS changed:** Origin server replies with **`HTTP/1.1 200 OK`** containing the newly updated file in the entity body.

---

### Summary
> [!abstract] Key Takeaways: Proxies & Caching
> - **Transparent Proxy:** Intercepts port 80 traffic at the edge router via DNAT/iptables without requiring any browser configuration.
> - **Conditional GET:** Uses `If-Modified-Since` header. Server replies with `304 Not Modified` (empty body) if cache is fresh, saving bandwidth.
