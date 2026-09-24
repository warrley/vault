---
tags:
  - flashcards
  - flashcards/networks/transport/udp
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: UDP Protocol & The Checksum Algorithm

What are the 4 foundational reasons an application chooses UDP over TCP?::1. **Fine-grained rate autonomy**: Sends data immediately without being throttled by TCP congestion control.<br>2. **Zero connection setup delay**: Sends payload in the very 1st packet ($0\text{ RTT}$ setup vs $1\text{ RTT}$ TCP handshake).<br>3. **Stateless server architecture**: Zero connection state/buffers allocated per client, allowing servers to scale to tens of thousands of active clients.<br>4. **Minimal header overhead**: Fixed 8-byte header vs 20–60-byte TCP header.
<!--ID: 1727300001-->

What are the 4 fields in the UDP segment header and their bit-widths?::1. **Source Port Number** ($16$ bits)<br>2. **Destination Port Number** ($16$ bits)<br>3. **Total Length** ($16$ bits, header $+$ payload in bytes; minimum $= 8\text{ bytes}$)<br>4. **Checksum** ($16$ bits).<br>Total fixed header size $= 8\text{ bytes}$ ($64\text{ bits}$).
<!--ID: 1727300002-->

How does a sender compute the Internet Checksum over a UDP segment?::1. Partition all bytes in the segment into **16-bit words** (pad odd bytes with a trailing zero byte).<br>2. Sum all 16-bit words using **1's complement addition** (wrap any overflow carry bit past the 16th bit back and add it to the LSB).<br>3. Compute the **bitwise inversion (1's complement)** ($0 \leftrightarrow 1$).<br>4. Store the resulting 16-bit value in the Checksum header field.
<!--ID: 1727300003-->

What is "end-around carry" in 1's complement binary addition?::Whenever standard binary addition generates an overflow carry bit beyond the 16th bit ($2^{16}$ position), that carry bit is not discarded; instead, it is **wrapped around and added to the least significant bit ($LSB$)** of the sum.
<!--ID: 1727300004-->

Calculate the 1's complement sum of `1110 0110 0100 1100` and `1101 0101 0101 0101`. What is the resulting checksum?::* Binary sum: `1 1011 1011 1010 0001` (Carry = 1)<br>* Wrap carry: `1011 1011 1010 0001 + 1` = `1011 1011 1010 0010` (`0xBBA2`)<br>* Bitwise Inversion: **`0100 0100 0101 1101` (`0x445D`)**.
<!--ID: 1727300005-->

How does a receiver verify incoming segment integrity using the Internet Checksum?::The receiver sums all 16-bit words of the incoming segment **plus the received Checksum field** using 1's complement addition:<br>* If the sum is **`1111 1111 1111 1111` (`0xFFFF`)**, no bit errors are detected.<br>* If **any bit in the sum is `0`**, bit corruption is detected and the packet is discarded.
<!--ID: 1727300006-->

Can the Internet Checksum correct corrupted bits, and what is its primary limitation?::* **No error correction**: It only detects errors; it cannot identify which bit was corrupted to correct it.<br>* **Undetected compensating errors**: If one bit flips $0 \to 1$ and another bit in the identical bit position in another word flips $1 \to 0$, the sum remains unchanged, leaving the corruption completely undetected.
<!--ID: 1727300007-->

What is the UDP Pseudo-Header, and why is it used during checksum calculation?::A temporary **12-byte block** containing Source IP, Destination IP, Protocol (17), and UDP length. The OS kernel includes it in the checksum computation to verify that the segment was not misdelivered to the wrong IP address due to an IP-layer header error, without transmitting the IP addresses twice on the wire.
<!--ID: 1727300008-->
