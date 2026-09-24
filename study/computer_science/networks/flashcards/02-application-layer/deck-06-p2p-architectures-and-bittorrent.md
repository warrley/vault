---
tags:
  - flashcards
  - flashcards/networks/app/p2p
  - networks/application-layer
  - ufc/computer-networks
parent: "[[02-application-layer]]"
---

# Flashcards: P2P File Distribution & BitTorrent Algorithms

What are the theoretical lower bound formulas for file distribution time in Client-Server ($D_{cs}$) vs P2P ($D_{p2p}$)?::* **Client-Server**: $D_{cs} \ge \max\left\{ \frac{N \cdot F}{u_s}, \; \frac{F}{d_{\min}} \right\}$ (Scales linearly as $O(N)$ with number of clients $N$).<br>* **P2P**: $D_{p2p} \ge \max\left\{ \frac{F}{u_s}, \; \frac{F}{d_{\min}}, \; \frac{N \cdot F}{u_s + \sum_{i=1}^N u_i} \right\}$ (Asymptotically bounded by $O(1)$ as $N \to \infty$ due to self-scalability).
<!--ID: 1726600001-->

How do Pure P2P networks (e.g. Gnutella) differ from Hybrid P2P networks (e.g. Napster, KaZaA)?::* **Hybrid P2P (Napster)**: Centralized server maintains file index/directory; peers transfer data directly P2P (SPOF at server).<br>* **Pure P2P (Gnutella)**: Completely decentralized; discovery and data transfer are both performed over a distributed peer overlay graph.<br>* **Hierarchical P2P (KaZaA/Skype)**: Uses dynamically elected high-capacity peers (**Superpeers**) to maintain local indices for regular leaf peers.
<!--ID: 1726600002-->

How does the Gnutella protocol search for content across its overlay network?::Using **Overlay Query Flooding**: A peer sends a `Query` message to all its immediate overlay neighbors. Each neighbor searches local storage and forwards the `Query` to its own neighbors, governed by a **TTL (Time-To-Live)** counter decremented at each hop to prevent routing loops and broadcast storms. Hits return via `QueryHit` along the reverse path.
<!--ID: 1726600003-->

What is the BitTorrent "Rarest-First" chunk selection algorithm and why is it used?::A peer determines which chunk of the file is least replicated among all its active neighbors and requests that **rarest chunk first**. This balances chunk replication across the swarm and prevents critical pieces from disappearing if seeds go offline.
<!--ID: 1726600004-->

How does BitTorrent's "Tit-for-Tat" (TFT) unchoking algorithm enforce fairness against free-riders?::Every $10\text{ seconds}$, a peer measures the upload rates from all connected peers and unchokes (sends data to) the **top 4 peers** providing the fastest upload rates to it. Slow or non-contributing peers are choked (blocked), incentivizing everyone to contribute upload bandwidth.
<!--ID: 1726600005-->

What is "Optimistic Unchoking" in BitTorrent?::Every $30\text{ seconds}$, a peer randomly unchokes **1 additional peer** regardless of its upload rate. This allows new peers (who have no data yet to trade) to obtain their first chunks, and allows existing peers to discover faster potential partners.
<!--ID: 1726600006-->
