---
tags:
  - flashcards
  - flashcards/networks/intro/edge-switching
  - networks/fundamentals
  - ufc/computer-networks
parent: "[[01-introduction-to-networks]]"
---

# Flashcards: Network Edge & Switching Paradigms

What is the formal definition of a network protocol?::A protocol defines the **format and order of messages** exchanged between two or more communicating entities, as well as the **actions taken** upon transmitting or receiving a message or other event.
<!--ID: 1715100001-->

In what part of the physical network topology are application-layer protocols implemented, and why?::Exclusively on **end systems (hosts) at the network edge**. Network core devices (routers and link switches) process only up to Layer 3/2 to maximize forwarding speed and adhere to the **End-to-End Principle**, allowing application developers to innovate without modifying core hardware.
<!--ID: 1715100002-->

What are the main advantages and disadvantages of the Client-Server architecture?::* **Advantages**: Centralized administration, simplified security, and strict data consistency.<br>* **Disadvantages**: The central server is a **single point of failure (SPOF)** and becomes a bandwidth/CPU bottleneck as the number of clients scales ($O(N)$ capacity demand).
<!--ID: 1715100003-->

What are the main advantages and disadvantages of the Peer-to-Peer (P2P) architecture?::* **Advantages**: **Self-scalability** (each peer brings upload capacity) and low infrastructure cost.<br>* **Disadvantages**: Complex distributed coordination, peer churn (unpredictable joins/leaves), difficult security/governance, and ISP uplink saturation.
<!--ID: 1715100004-->

Why did the Internet adopt Packet Switching over Circuit Switching for computer data?::Computer traffic is **bursty** with long idle periods between requests. Packet switching uses **Statistical Multiplexing** to dynamically allocate link capacity on-demand, accommodating vastly more simultaneous users than circuit switching, which wastes dedicated reserved channels during silence.
<!--ID: 1715100005-->

What is the operational difference between Frequency-Division Multiplexing (FDM) and Time-Division Multiplexing (TDM) in circuit switching?::* **FDM**: The physical spectrum is divided into **dedicated frequency bands**, with each user transmitting continuously on their reserved band (e.g. analog radio, cable TV).<br>* **TDM**: The entire frequency band is allocated to one user at a time during **periodic, dedicated time slots** (e.g. traditional T1 telephony).
<!--ID: 1715100006-->

How is it possible for two packets sent sequentially from Host A to Host B across a packet-switched network to arrive out of order?::Because the network core uses **datagram forwarding**. Each packet is routed independently; if routing tables update or intermediate link congestion varies, packets may traverse different physical paths with different propagation and queuing delays.
<!--ID: 1715100007-->
