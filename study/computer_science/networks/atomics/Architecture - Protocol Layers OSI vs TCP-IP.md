---
tags:
  - networks/architecture
  - networks/osi
  - networks/tcp-ip
  - networks/kurose-ch1
parent: "[[01-introduction-to-networks]]"
---

# Architecture: Protocol Layers OSI vs. TCP/IP

## 1. Why Layered Network Architecture?

A modern computer network is an enormous, heterogeneous distributed system. Layering applies the fundamental computer engineering principle of **modularity and abstraction**:

1. **Explicit Conceptual Decomposition**: Breaks an impossibly complex system into well-defined, manageable sub-tasks.
2. **Standardized Interfaces & Transparency**: Modifying the internal implementation or algorithms of one layer has **zero impact** on adjacent layers as long as the service interface remains constant.
   * *Example*: Upgrading an Ethernet switch from $1\text{ Gbps}$ to $10\text{ Gbps}$, or switching a laptop from 1000BASE-T copper to 802.11ax Wi-Fi, requires zero changes to TCP/IP or web browsers.

---

## 2. Comparing the Reference Models

```
         OSI Model (7 Layers - Conceptual ISO standard)       TCP/IP Internet Stack (5 Layers - Practical Standard)
       ┌──────────────────────────────────────────────┐       ┌──────────────────────────────────────────────┐
     7 │ Aplicação (Application)                      │ ────► │ Aplicação (Application)                      │
       ├──────────────────────────────────────────────┤       │ (HTTP, DNS, SMTP, IMAP, FTP, SSH)            │
     6 │ Apresentação (Presentation)                  │ ────► │                                              │
       ├──────────────────────────────────────────────┤       │                                              │
     5 │ Sessão (Session)                             │ ────► │                                              │
       ├──────────────────────────────────────────────┤       ├──────────────────────────────────────────────┤
     4 │ Transporte (Transport)                       │ ────► │ Transporte (Transport)                       │
       │                                              │       │ (TCP, UDP)                                   │
       ├──────────────────────────────────────────────┤       ├──────────────────────────────────────────────┤
     3 │ Rede (Network)                               │ ────► │ Rede (Network)                               │
       │                                              │       │ (IPv4, IPv6, ICMP, OSPF, BGP)                 │
       ├──────────────────────────────────────────────┤       ├──────────────────────────────────────────────┤
     2 │ Enlace de Dados (Data Link)                  │ ────► │ Enlace (Link)                                │
       │                                              │       │ (Ethernet 802.3, Wi-Fi 802.11, PPP)          │
       ├──────────────────────────────────────────────┤       ├──────────────────────────────────────────────┤
     1 │ Física (Physical)                            │ ────► │ Física (Physical)                            │
       │                                              │       │ (Bits on copper, fiber optic, radio waves)   │
       └──────────────────────────────────────────────┘       └──────────────────────────────────────────────┘
```

---

## 3. Detailed Responsibilities and PDUs by Layer

### Layer 5: Application Layer (*Camada de Aplicação*)
* **Scope**: Host-to-Host distributed application processes.
* **Core Function**: Defines the message formats and exchange rules for distributed user applications.
* **Key Protocols**: HTTP (web), DNS (domain resolution), SMTP/IMAP (email), FTP (file transfer), SSH (secure shell).
* **PDU (*Unidade de Dados do Protocolo*)**: **Message (*Mensagem*)**.

### Layer 4: Transport Layer (*Camada de Transporte*)
* **Scope**: **Process-to-Process logical communication** between application endpoints running on different hosts.
* **Core Functions**:
  * **Multiplexing / Demultiplexing**: Uses 16-bit **Port Numbers** to deliver segments to the correct application process.
  * **TCP**: Reliable, in-order byte stream delivery, connection establishment (3-way handshake), flow control, congestion control.
  * **UDP**: Lightweight, connectionless, unreliable datagram transmission without overhead.
* **PDU**: **Segment (*Segmento*)** (or User Datagram).

### Layer 3: Network Layer (*Camada de Rede*)
* **Scope**: **Host-to-Host logical communication** and datagram routing across multiple intermediate networks.
* **Core Functions**:
  * **Logical Addressing**: Global IPv4 (32-bit) / IPv6 (128-bit) addressing.
  * **Routing (*Roteamento*)**: Global path calculation using routing algorithms (OSPF, RIP, BGP).
  * **Forwarding (*Encaminhamento*)**: Moving incoming packets to the correct output port inside a router using the forwarding table.
* **PDU**: **Datagram / Packet (*Datagrama / Pacote*)**.

### Layer 2: Data Link Layer (*Camada de Enlace*)
* **Scope**: **Node-to-Node transfer** across a single physical communication link or local area network segment.
* **Core Functions**:
  * **Physical Addressing**: 48-bit MAC addresses.
  * **Framing**: Packaging datagrams into frames with headers and error-checking trailers (CRC).
  * **Medium Access Control (MAC)**: Coordinating shared access to broadcast channels (e.g., CSMA/CD in Ethernet, CSMA/CA in Wi-Fi).
* **PDU**: **Frame (*Quadro*)**.

### Layer 1: Physical Layer (*Camada Física*)
* **Scope**: Raw bit transmission over physical media.
* **Core Function**: Converts digital bits (`0`s and `1`s) into physical signals (electrical voltages, light pulses, or electromagnetic radio waves).
* **PDU**: **Bits**.

---

## 4. Why Did TCP/IP Omit OSI Layers 5 & 6? (Exam Focus)

The OSI reference model introduced two intermediate layers that the practical Internet stack deliberately excluded:
* **Presentation Layer (Layer 6)**: Intended for data formatting, character encoding (e.g., ASCII/EBCDIC), data compression, and encryption.
* **Session Layer (Layer 5)**: Intended for establishing checkpoints, managing tokens, and synchronizing dialog states.

### The Reason: The "End-to-End" Argument
Internet designers realized that:
1. Not all applications need encryption, compression, or checkpointing.
2. If an application *does* need them (e.g., HTTPS requires TLS encryption, or video streaming requires compression), **the application itself knows best how to format and manage its data**.
3. Therefore, these features are implemented **directly inside the Application Layer** (e.g., TLS/SSL sits inside the application layer above TCP). This keeps the lower network layers lean, fast, and universal.

---

## 5. Architectural Comparison Matrix
> [!abstract] Key Takeaway
>
> | Layer | PDU Name | Addressing Type | Key Hardware Entity |
> | :--- | :--- | :--- | :--- |
> | **5. Application** | Message | Domain Name / URL | End Host (Computer, Server) |
> | **4. Transport** | Segment | Port Number (16-bit) | End Host Operating System Stack |
> | **3. Network** | Datagram | IP Address (32/128-bit) | Router |
> | **2. Link** | Frame | MAC Address (48-bit) | Link-Layer Switch / Network Interface Card |
> | **1. Physical** | Bit | Signal Voltage / Light Frequency | Hub / Repeater / Physical Cable |
