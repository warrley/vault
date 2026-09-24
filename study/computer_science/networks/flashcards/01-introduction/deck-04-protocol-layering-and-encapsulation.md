---
tags:
  - flashcards
  - flashcards/networks/intro/layering
  - networks/fundamentals
  - ufc/computer-networks
parent: "[[01-introduction-to-networks]]"
---

# Flashcards: Protocol Layering & Encapsulation

What are the 5 layers of the practical Internet (TCP/IP) model from top to bottom?::1. **Application (Camada de Aplicação)** - Layer 5<br>2. **Transport (Camada de Transporte)** - Layer 4<br>3. **Network (Camada de Rede)** - Layer 3<br>4. **Link / Data Link (Camada de Enlace)** - Layer 2<br>5. **Physical (Camada Física)** - Layer 1.
<!--ID: 1715400001-->

What are the specific Protocol Data Unit (PDU) names at each of the 5 layers of the Internet stack?::* Layer 5 (Application): **Message (Mensagem)**<br>* Layer 4 (Transport): **Segment (Segmento)**<br>* Layer 3 (Network): **Datagram / Packet (Datagrama / Pacote)**<br>* Layer 2 (Link): **Frame (Quadro)**<br>* Layer 1 (Physical): **Bits**.
<!--ID: 1715400002-->

Why did the Internet (TCP/IP) architecture omit OSI Layers 5 (Session) and 6 (Presentation)?::Following the **End-to-End Principle**, functions like session management, data encryption, and compression belong in the application itself (e.g. TLS inside HTTPS) rather than adding mandatory overhead inside the network protocol stack.
<!--ID: 1715400003-->

What layers of the protocol stack are processed by an End Host, a Router, and a Link-Layer Switch?::* **End Host**: Processes **all 5 layers** (L1–L5: Physical through Application).<br>* **Core Router**: Processes up to **Layer 3** (L1–L3: Physical, Link, Network).<br>* **Link-Layer Switch**: Processes up to **Layer 2** (L1–L2: Physical, Link).
<!--ID: 1715400004-->

What does a router do to the Layer 2 (Link) frame header when forwarding an IP datagram between two interfaces?::It strips off (decapsulates) the incoming Layer 2 frame header ($H_l$), inspects the Layer 3 destination IP in the datagram header ($H_n$) to determine the next hop, decrements TTL, and encapsulates the datagram into a **brand-new Layer 2 frame header** ($H_l'$) formatted for the outgoing link type (e.g. Ethernet, Wi-Fi, DOCSIS).
<!--ID: 1715400005-->

What is the operational definition of Encapsulation and Decapsulation?::* **Encapsulation (Sender)**: Top-down process where each layer wraps the payload from the layer above with its own header metadata (and optional trailer).<br>* **Decapsulation (Receiver)**: Bottom-up process where each layer strips its header, interprets the control metadata, and delivers the payload to the layer above.
<!--ID: 1715400006-->
