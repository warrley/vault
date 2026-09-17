---
tags:
  - networks/architecture
  - networks/p2p
  - study-notes
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Architecture: Application Paradigms & P2P File Distribution

## 1. Overview & Separation of Concerns
Every network application running across distributed end systems must solve two fundamental, orthogonal problems:
1. **Indexing / Discovery Service:** How do clients locate the IP address and identity of the host holding the desired resource?
2. **Data Transfer Service:** How are the actual payload bits transported from the source host to the destination host?

Different application architectures allocate these two responsibilities differently between dedicated servers and edge peers.

```
+----------------------------------------------------------------------------------------------------+
|                               APPLICATION ARCHITECTURES OVERVIEW                                   |
+----------------------------------------------------------------------------------------------------+
| Architecture        | Indexing / Discovery            | Data Transfer           | Scalability      |
+---------------------+---------------------------------+-------------------------+------------------+
| Client-Server       | Centralized Server              | Centralized Server      | O(N) (Bottleneck)|
| Hybrid P2P (Napster)| Centralized Server Database     | Direct Peer-to-Peer     | O(1) Data, O(N) Ctl|
| Pure P2P (Gnutella) | Distributed (Overlay Flooding)  | Direct Peer-to-Peer     | O(1) Data, O(d^k)|
| Hierarchical (KaZaA)| Superpeer Overlay Flooding      | Direct Peer-to-Peer     | High Scalability |
| BitTorrent          | Tracker / DHT (Distributed Hash)| Chunks via Tit-for-Tat  | Self-Scalable    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Client-Server Architecture & Mathematical Derivation

### Characteristics
- **Server:** An always-on host with a static, permanent IP address and well-known port. Passively listens for connections.
- **Clients:** Dynamic IP addresses, intermittently connected, never communicate directly with one another.

### Mathematical Distribution Time ($D_{cs}$)
Distributing a file of size $F$ bits from a single server (upload capacity $u_s$) to $N$ independent clients (each with download capacity $d_i$ and upload capacity $u_i$):

1. **Server Upload Constraint:** The server must transmit $N$ independent copies of the file:
   $$D_{cs} \ge \frac{N \cdot F}{u_s}$$
2. **Client Minimum Download Constraint:** The slowest client ($d_{\min} = \min_i d_i$) must receive at least $F$ bits:
   $$D_{cs} \ge \frac{F}{d_{\min}}$$

Combining both constraints yields the theoretical lower bound:

$$D_{cs} \ge \max\left\{ \frac{N \cdot F}{u_s}, \; \frac{F}{d_{\min}} \right\}$$

$$\text{As } N \to \infty, \quad D_{cs} \approx \frac{N \cdot F}{u_s} = O(N)$$

> [!warning] The Client-Server Bottleneck
> In a Client-Server system, each incoming client adds **demand (load)** without contributing **supply (capacity)**. The required distribution time grows linearly with $N$.

---

## 3. P2P Architectures: Evolution & Mechanisms

### A. Hybrid P2P (Napster - 1999)
- **Mechanism:**
  1. **Centralized Index:** When peers connect, they register their IP address and file catalog with Napster's central directory server.
  2. **Decentralized Transfer:** Alice queries the central server for a song title $\rightarrow$ server returns Bob's IP $\rightarrow$ Alice downloads the file directly from Bob over a direct TCP connection.
- **Fatal Flaws:**
  - **Single Point of Failure (SPOF):** If the directory crashes, all file discovery ceases.
  - **Control Plane Bottleneck:** Millions of concurrent searches and presence updates saturate server CPU and bandwidth.
  - **Legal Vulnerability:** The central index created a single corporate target for copyright lawsuits, resulting in its legal shutdown.

---

### B. Pure Unstructured P2P (Gnutella - 2000)
- **Elimination of Central Server:** Every node functions simultaneously as a client and server (a **servent**).
- **Overlay Network (Rede de Sobreposição):**
  - An application-layer virtual graph built over physical Layer 3 IP infrastructure.
  - **Nodes:** Active peer processes.
  - **Edges:** Active TCP connections between pairs of peers.
  - *Why Layer 7 Flooding instead of Layer 3 IP Broadcast?* Internet routers intentionally drop IP broadcast packets (`255.255.255.255`) to prevent global broadcast storms. Thus, discovery must be routed logically at Layer 7.
- **Limited-Scope Flooding & Reverse Path Routing:**
  1. Peer sends a `Query` packet with a **Time-To-Live (TTL)** (e.g., $\text{TTL} = 5-7$) to all immediate overlay neighbors.
  2. Neighbors decrement $\text{TTL}$ and forward the query. Duplicate queries are detected and dropped using a unique **Message ID**.
  3. When a peer has the file, it sends a `QueryHit` message **backwards along the exact reverse path** of overlay TCP links to the requester.
  4. The requester establishes a direct HTTP/TCP connection to the provider's IP/port to fetch the file.
- **Limitation:** Exponential signaling overhead $O(d^{\text{TTL}})$, where $d$ is average node degree.

---

### C. Hierarchical P2P (KaZaA / FastTrack - 2001)
- **Heterogeneity Exploitation:** Recognizes that peers possess unequal bandwidth, processing power, and connection stability.
- **Two-Tier Topology:**
  - **Ordinary Peers:** Low-bandwidth or transient nodes. Connect to a single Superpeer and upload their file index to it. Never forward search queries.
  - **Superpeers (Group Leaders):** High-capacity nodes with public IPs and high uptime. Superpeers maintain local directories of their assigned children and form a high-speed inter-superpeer overlay.
- **Query Workflow:** Ordinary peer $\rightarrow$ its Superpeer. If unresolved locally, the Superpeer floods the query strictly across the Superpeer backbone.

---

## 4. Mathematical Modeling of P2P Self-Scalability ($D_{p2p}$)

In P2P file distribution, every peer receiving data simultaneously acts as a server uploading data to other peers.

### The Three Physical Bounds
1. **Server Seed Transmission:** The server must upload at least one full copy of the file into the swarm:
   $$D_{p2p} \ge \frac{F}{u_s}$$
2. **Client Minimum Download:** The slowest peer ($d_{\min}$) must download $F$ bits:
   $$D_{p2p} \ge \frac{F}{d_{\min}}$$
3. **Aggregate Swarm Upload Capacity:** The total number of bits required by all $N$ peers is $N \cdot F$. The maximum aggregate upload bandwidth across the entire network is $u_s + \sum_{i=1}^N u_i$:
   $$D_{p2p} \ge \frac{N \cdot F}{u_s + \sum_{i=1}^N u_i}$$

Combining all three gives the P2P distribution lower bound:

$$D_{p2p} \ge \max\left\{ \frac{F}{u_s}, \; \frac{F}{d_{\min}}, \; \frac{N \cdot F}{u_s + \sum_{i=1}^N u_i} \right\}$$

### Proof of Self-Scalability ($O(1)$)
If all peers have an average upload capacity $u$ ($u_i = u$):

$$\lim_{N \to \infty} \frac{N \cdot F}{u_s + N \cdot u} = \frac{F}{u}$$

$$\text{As } N \to \infty, \quad D_{p2p} \le \max\left( \frac{F}{u_s}, \; \frac{F}{d_{\min}}, \; \frac{F}{u} \right) = \boldsymbol{O(1)}$$

```
Time D
  ^
  |                     / Client-Server D_cs = O(N)
  |                    /
  |                   /
  |  ----------------+----------------- P2P D_p2p = O(1)
  | /
  +-------------------------------------> Number of Peers (N)
```

---

## 5. BitTorrent Protocol Engineering
BitTorrent implements practical, high-efficiency P2P swarm distribution:

1. **File Chunking:** Files are partitioned into equal chunks (typically $256\text{ KB}$). Peers download chunks in parallel from different neighbors.
2. **Rarest First Policy:** A peer queries neighbors' bitfields and requests the rarest chunks in the local swarm first. This prevents rare chunks from vanishing if the original seeder leaves and maximizes chunk diversity for cross-trading.
3. **Tit-for-Tat Incentive (Game Theory against Free-Riders):**
   - **Choking / Unchoking (every 10s):** Alice measures incoming download rates from all connected neighbors and unchokes (uploads to) the top 4 fastest providers.
   - **Optimistic Unchoking (every 30s):** Alice picks 1 random neighbor to unchoke. This allows newly joined peers (with no initial data) to bootstrap and helps Alice discover faster trading partners.

---

### Summary
> [!abstract] Architectural Comparison & Math Takeaway
> - **Client-Server ($D_{cs}$):** $D_{cs} \ge \max\{NF/u_s, F/d_{\min}\} = O(N)$. Saturated by server upload link.
> - **P2P ($D_{p2p}$):** $D_{p2p} \ge \max\{F/u_s, F/d_{\min}, NF/(u_s + \sum u_i)\} = O(1)$. Auto-scalable because each consumer brings upload capacity.
> - **Discovery Evolutions:** Napster (Centralized Index) $\rightarrow$ Gnutella (Overlay Flooding with TTL) $\rightarrow$ KaZaA (Superpeers) $\rightarrow$ BitTorrent / DHT (Trackerless distributed hashing).
