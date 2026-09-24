> [!quote] YOU

given my discipline folder 4s/computer_networs my study folder (with flashcards) ./study/computer_science/networks/ and the my teacher past exams ./output/files/network_exam/ 
give me a exam-style questions about the content, each question must created and I must answer in terminal (without options)

> [!question] Question
> [Questão 1 - AP1 Redes de Computadores / Camadas & Modelos]
>
> (a) Explique a função principal de cada uma das 5 camadas da arquitetura Internet (TCP/IP de 5 camadas) e cite qual unidade de dados de protocolo (PDU) ou estrutura trafega em cada uma delas.
> (b) Por que dizemos que o núcleo da rede (roteadores e comutadores tradicionais) opera apenas até a camada de rede, enquanto as camadas de transporte e aplicação residem estritamente na borda (hosts)?
>
> Digite sua resposta detalhada diretamente no terminal (sem opções de múltipla escolha). Após sua resposta, analisarei e pontuarei seu raciocínio com base nos critérios de prova do Prof. Callado e no Kurose/Tanenbaum.

> [!example] Answer
> Porque voce colocou 2 questoes juntas? mas valos lá

(a): Aplicacao: Nessa camada tratamos de MENSAGENS, ela suporta mensagens trocadas por aplicacos dos usuarios (nao estou certo disso)
     Tansporte: Essa camada cuida da comunicação lógica entre os processos
com comunicacao fim-a-fim transportando os SEGMENTOS
     Rede: Essa camada cuida da comunicao lógica entre os hosts com o endereco de cada host IP, transportando os DATAGRAMAS
     Enlace: Essa camada cuida da comunicacao entre os vizinhos na rede, transportando os Frames
     Fisica: Essa camada transporta os BITS

(b): Isso é o que diz o principio fim-a-fim, que o processamento dos dados só devem ser feitos nos dispositvos de borda, deixando o nucleo o mais simples e rapido possível, os hosts implementam L1-L5, os roteadores L1-L3 e os comutadores L1-L2

> [!question] Question
> [Questão 2 - AP1 Redes / HTTP e Web Caching]
>
> No contexto do protocolo HTTP e arquiteturas Web:
> Explique detalhadamente o que é um **Proxy HTTP Transparente** (Transparent Proxy), como ele difere de um **Proxy Explícito / Convencional** na perspectiva do cliente (navegador), e como o tráfego é interceptado na rede.
>
> Digite sua resposta dissertativa diretamente no terminal.

> [!example] Answer
> vamos fazer assim, só vou tentar responder as questoes que nao tenho certeza, pois as que eu sei, vou perder muito tempo escrevendo elas

> [!question] Question
> [Questão 3 - AP1 Redes / Correio Eletrônico e SMTP]
>
> Por que é estritamente necessário codificar um arquivo binário (como uma imagem JPEG ou executável) em formato texto (ex.: Base64 / MIME) antes de anexá-lo e enviá-lo em uma mensagem de e-mail via protocolo SMTP clássico? O que acontece no protocolo SMTP que exige isso?
>
> Se souber com certeza, pode digitar apenas 'sei' / 'pass' para avançarmos rápido com o gabarito. Se estiver em dúvida ou quiser testar, digite sua resposta ou 'não sei'.

> [!example] Answer
> sei
quero que em cada questao voce me corrija se eu tiver respondido, e me de uma resposta detalhada, comece respondendo as de cima

> [!question] Question
> ---
> ### 📌 Gabaritos & Correções das Questões Anteriores
>
> #### ✅ Correção da Questão 1 (Sua Resposta: 10/10)
> Sua resposta foi precisa:
> * **Aplicação**: PDU = **Mensagem** (*Message*). Provê protocolos de alto nível para processos de aplicação (HTTP, DNS, SMTP).
> * **Transporte**: PDU = **Segmento** (*Segment*, ou Datagrama UDP). Comunicação lógica fim-a-fim entre **processos** (portas de sockets).
> * **Rede**: PDU = **Datagrama** (*Datagram* / Pacote). Comunicação lógica host-a-host, endereçamento global (IP) e roteamento.
> * **Enlace**: PDU = **Quadro** (*Frame*). Transferência física local entre nós vizinhos/adjacentes no mesmo enlace (MAC/Ethernet/Wi-Fi).
> * **Física**: PDU = **Bits** / Sinal eletromagnético ou óptico. Transmissão bruta de bits pelo meio físico.
> * **Princípio Fim-a-Fim (*End-to-End*)**: A inteligência e o estado da aplicação ficam estritamente nos *hosts* de borda (L1–L5). O núcleo da rede permanece enxuto e de alto desempenho, com roteadores operando em L1–L3 e switches de enlace em L1–L2.
>
> ---
>
> #### 📘 Gabarito Detalhado da Questão 2 (Proxy HTTP Transparente vs Convencional)
> 1. **Proxy Convencional (Explícito)**:
>    * O cliente (navegador/SO) é **configurado explicitamente** com o IP e porta do proxy (ex: `192.168.1.1:8080`).
>    * O navegador abre a conexão TCP diretamente com o IP do Proxy e envia a URI absoluta na linha de requisição: `GET http://www.google.com/index.html HTTP/1.1`.
> 2. **Proxy Transparente (Interceptador / *Inline*)**:
>    * O cliente **não sabe** que o proxy existe (nenhuma configuração no navegador/SO). Ele envia os pacotes TCP com endereço IP de destino do servidor web real (ex: IP do Google, porta 80).
>    * **Como é interceptado na rede**: Um elemento intermediário no caminho (geralmente o roteador/firewall da borda da rede usando regras de *iptables* / NAT ou protocolo WCCP) intercepta os pacotes com porta de destino 80 e os desvia (redireciona a porta) para a porta local do processo de proxy (ex: Squid).
>    * O proxy atende a requisição, consulta/alimenta o cache local, busca do servidor original se necessário, e devolve a resposta ao cliente forjando o IP de origem do servidor de destino.
>
> ---
>
> #### 📘 Gabarito Detalhado da Questão 3 (Anexos Binários no SMTP / MIME / Base64)
> * **Origem e Limitação do SMTP (RFC 821)**: O protocolo SMTP foi projetado originalmente na década de 1980 para transmitir estritamente **texto legível ASCII de 7 bits** (*7-bit ASCII*).
> * **O Problema dos Binários**: Arquivos binários (imagens, PDFs, executáveis) utilizam palavras de **8 bits** completas (valores de 0 a 255). Se bytes com valores arbitrários (como caracteres de controle `NUL`, bytes com bit mais significativo `1`, ou a sequência de terminação CRLF.CRLF `\r\n.\r\n`) fossem transmitidos diretamente:
>   1. Servidores/gateways de correio antigos truncavam ou descartavam o 8º bit (destruindo o binário).
>   2. O servidor SMTP interpretaria erroneamente padrões de bytes como comandos de protocolo ou encerramento prematuro da mensagem (`<CRLF>.<CRLF>`).
> * **A Solução (MIME & Base64)**: O padrão MIME (*Multipurpose Internet Mail Extensions*) empacota o binário convertendo blocos de 3 bytes (24 bits) em 4 caracteres ASCII imprimíveis seguros de 6 bits (codificação **Base64**), adicionando os cabeçalhos `Content-Type:` e `Content-Transfer-Encoding: base64` para que o receptor reconstrua o binário perfeitamente.
>
> ---
>
> ### 📝 [Questão 4 - AP1 Redes / DNS e Resolução de Nomes]
>
> No sistema DNS (*Domain Name System*):
> (a) Por que existe um tipo específico de registro de recurso chamado **MX (*Mail Exchange*)**, em vez de utilizar apenas o registro padrão **A** para servidores de correio? Cite a vantagem para uma organização.
> (b) Explique a diferença entre uma **consulta DNS Iterativa** e uma **consulta DNS Recursiva** a partir do servidor DNS Local (*Local DNS Server* / Resolver).
>
> Responda caso queira testar/treinar a escrita, ou digite 'sei' / 'pass' / 'não sei'. Em todos os casos eu trarei a correção e o gabarito detalhado padrão prova.

> [!example] Answer
> de um /md-log em ./output/files/network_exam/ap1_sim

> [!abstract] PI

O log completo com todas as 10 questões padrão de prova dissertativa, critérios rigorosos de correção e gabaritos detalhados foi gerado e salvo em:

📁 **`./output/files/network_exam/ap1_sim.md`**

---

### 📋 Resumo dos Tópicos Contemplados no Documento:

1. **Questão 1 — Camadas, PDUs e Princípio Fim-a-Fim:**  
   As 5 camadas L1–L5, suas unidades de dados (Mensagem, Segmento, Datagrama, Quadro, Bits) e por que o núcleo opera apenas até L3.
2. **Questão 2 — HTTP Proxy Transparente vs Explícito:**  
   Diferença na perspectiva do cliente e mecanismo de interceptação de rede via *iptables*/NAT/WCCP no gateway.
3. **Questão 3 — Correio Eletrônico e SMTP:**  
   Origem da limitação ASCII de 7 bits no SMTP clássico, codificação MIME/Base64 para anexos binários de 8 bits e arquitetura Push (SMTP) vs Pull (POP3/IMAP).
4. **Questão 4 — DNS (Registros MX & Consultas):**  
   Por que o registro MX existe (desacoplamento de domínio web/mail e tolerância a falhas com prioridades) e a diferença entre Consultas Recursivas vs Iterativas.
5. **Questão 5 — HTTP Cookies & Estado:**  
   Conceito de protocolo *stateless*, vantagens para servidores e os 4 componentes de manutenção de estado (`Set-Cookie`, armazenamento local, `Cookie`, banco backend).
6. **Questão 6 — P2P Puro (Gnutella) vs Híbrido (BitTorrent) vs Cliente-Servidor:**  
   Mecanismos de busca (*Query Flooding* vs Trackers centralizados), vantagens e desvantagens de robustez vs escalabilidade.
7. **Questão 7 — Hierarquia de Servidores DNS:**  
   Papel dos Servidores Raiz (13 IPs Anycast), TLDs, Autoritativos e Servidores DNS Locais (caching e TTL).
8. **Questão 8 — Camada de Transporte (Multiplexação/Demultiplexação):**  
   Identificação de Sockets UDP (2-tupla) vs Sockets TCP (4-tupla) e a razão do *Listening Socket* dedicado no TCP.
9. **Questão 9 — RDT & Pipelining (Stop-and-Wait vs GBN vs SR):**  
   Cálculo de utilização do enlace ($U$), ACKs cumulativos vs individuais, política de timers e buffers de recepção.
10. **Questão 10 — TCP (Controle de Fluxo vs Congestionamento):**  
    Diferença conceitual e de variáveis (`rwnd` vs `cwnd`), cálculo da janela efetiva ($\min(\text{rwnd}, \text{cwnd})$) e a evolução da `cwnd` nos estados *Slow Start*, *Congestion Avoidance* e *Fast Recovery*.


> [!quote] YOU

continue com as questoes


> [!question] Question
> [Questão 11 - AP1 Redes / TCP: Handshake em 3 Vias e Estado TIME_WAIT]
>
> Considere o gerenciamento de conexão no protocolo TCP:
>
> (a) Descreva o processo do **3-Way Handshake** (estabelecimento de conexão), especificando as flags (SYN, ACK) e números de sequência trocados em cada um dos 3 passos. Por que um handshake de apenas duas vias (2-Way) seria vulnerável a conexões fantasmas/duplicadas?
>
> (b) No encerramento da conexão (via flags FIN e ACK), por que o host que envia o primeiro FIN é obrigado a permanecer no estado **`TIME_WAIT`** aguardando um período de $2 \times \text{MSL}$ (*Maximum Segment Lifetime*) antes de fechar o socket definitivamente? Cite os 2 motivos fundamentais.
>
> Digite sua resposta no terminal, ou digite 'sei' / 'pass' se já domina, ou 'não sei' / 'explica' para ver o gabarito direto.
