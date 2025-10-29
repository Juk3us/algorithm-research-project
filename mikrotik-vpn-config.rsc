# =====================================================
# MikroTik VPN Server Configuration
# =====================================================
# Scenario:
# - Port 1: PPPoE connection to national intranet (via wireless radio link)
# - Port 2: Backup for Port 1 via VDSL
# - Port 5: Internet connection
# - WireGuard VPN Server for clients
# =====================================================

# =====================================================
# 1. INTERFACE CONFIGURATION
# =====================================================

# Set interface names for clarity
/interface ethernet
set [ find default-name=ether1 ] name=ether1-wan-radio comment="WAN: Radio Link to Intranet"
set [ find default-name=ether2 ] name=ether2-wan-vdsl comment="WAN Backup: VDSL to Intranet"
set [ find default-name=ether3 ] name=ether3-lan comment="LAN Port"
set [ find default-name=ether4 ] name=ether4-lan comment="LAN Port"
set [ find default-name=ether5 ] name=ether5-internet comment="Internet Connection"

# =====================================================
# 2. VLAN CONFIGURATION (Port 1)
# =====================================================

/interface vlan
add interface=ether1-wan-radio name=vlan1787 vlan-id=1787 comment="VLAN for PPPoE"

# =====================================================
# 3. PPPoE CLIENT CONFIGURATION (Port 1)
# =====================================================

/interface pppoe-client
add add-default-route=yes \
    default-route-distance=1 \
    disabled=no \
    interface=vlan1787 \
    name=pppoe-intranet \
    user=1331626494 \
    password=351598 \
    use-peer-dns=yes \
    keepalive-timeout=60 \
    comment="Primary WAN: Intranet via Radio Link"

# =====================================================
# 4. DHCP CLIENT CONFIGURATION
# =====================================================

# Port 2: VDSL Backup Connection
/ip dhcp-client
add disabled=no \
    interface=ether2-wan-vdsl \
    add-default-route=yes \
    default-route-distance=2 \
    use-peer-dns=no \
    comment="Backup WAN: VDSL Intranet"

# Port 5: Internet Connection
add disabled=no \
    interface=ether5-internet \
    add-default-route=yes \
    default-route-distance=3 \
    use-peer-dns=yes \
    comment="Internet Connection"

# =====================================================
# 5. LAN IP ADDRESS CONFIGURATION
# =====================================================

/ip address
add address=192.168.100.1/24 interface=ether3-lan comment="LAN Network"

# Create bridge for LAN ports (optional but recommended)
/interface bridge
add name=bridge-lan comment="LAN Bridge"

/interface bridge port
add bridge=bridge-lan interface=ether3-lan
add bridge=bridge-lan interface=ether4-lan

# Move IP address to bridge
/ip address
remove [find interface=ether3-lan]
add address=192.168.100.1/24 interface=bridge-lan comment="LAN Network"

# =====================================================
# 6. DHCP SERVER FOR LAN
# =====================================================

/ip pool
add name=lan-pool ranges=192.168.100.10-192.168.100.254

/ip dhcp-server
add address-pool=lan-pool disabled=no interface=bridge-lan name=dhcp-lan

/ip dhcp-server network
add address=192.168.100.0/24 \
    gateway=192.168.100.1 \
    dns-server=192.168.100.1,8.8.8.8,1.1.1.1 \
    comment="LAN DHCP Network"

# =====================================================
# 7. WIREGUARD VPN SERVER CONFIGURATION
# =====================================================

# WireGuard Server Keys:
# Private key: KEODtvSQS68bLhQLdJ8jmwdW7vxwCroQuVVv3hAzy3k=
# Public key: OkMrWI423O6h0Fgvg40RRvzWBLv1bC4CEfNi9INlph0=

# Create WireGuard interface
/interface wireguard
add listen-port=13231 \
    mtu=1420 \
    name=wireguard-vpn \
    private-key="KEODtvSQS68bLhQLdJ8jmwdW7vxwCroQuVVv3hAzy3k=" \
    comment="WireGuard VPN Server"

# Add IP address to WireGuard interface
/ip address
add address=192.168.200.1/24 interface=wireguard-vpn comment="WireGuard Server IP"

# Add WireGuard peer (Client 1)
/interface wireguard peers
add allowed-address=192.168.200.2/32 \
    interface=wireguard-vpn \
    public-key="L1MLvxKfg0zzA6JYQbCbhYtZm/QFadlllHbYRqlD5SM=" \
    comment="WireGuard Client 1"

# =====================================================
# 8. NAT CONFIGURATION
# =====================================================

# NAT for LAN clients going to Internet
/ip firewall nat
add action=masquerade \
    chain=srcnat \
    out-interface=ether5-internet \
    comment="NAT: LAN to Internet"

# NAT for VPN clients going to Internet
add action=masquerade \
    chain=srcnat \
    src-address=192.168.200.0/24 \
    out-interface=ether5-internet \
    comment="NAT: VPN Clients to Internet"

# NAT for traffic through PPPoE (if needed)
add action=masquerade \
    chain=srcnat \
    out-interface=pppoe-intranet \
    comment="NAT: Through PPPoE"

# NAT for traffic through VDSL backup
add action=masquerade \
    chain=srcnat \
    out-interface=ether2-wan-vdsl \
    comment="NAT: Through VDSL Backup"

# =====================================================
# 9. ROUTING CONFIGURATION
# =====================================================

# Route VPN clients to Internet via Port 5
/ip route
add dst-address=0.0.0.0/0 \
    gateway=ether5-internet \
    distance=3 \
    comment="Default route via Internet"

# Routes are automatically created by DHCP and PPPoE clients
# PPPoE: distance=1 (Primary)
# VDSL: distance=2 (Backup)
# Internet: distance=3 (for VPN traffic)

# =====================================================
# 10. FIREWALL CONFIGURATION
# =====================================================

/ip firewall filter

# Allow established and related connections
add action=accept \
    chain=input \
    connection-state=established,related \
    comment="Accept established/related"

# Allow WireGuard VPN connections
add action=accept \
    chain=input \
    protocol=udp \
    dst-port=13231 \
    comment="Allow WireGuard VPN"

# Allow ICMP (ping)
add action=accept \
    chain=input \
    protocol=icmp \
    comment="Allow ICMP"

# Allow access from LAN
add action=accept \
    chain=input \
    in-interface=bridge-lan \
    comment="Allow from LAN"

# Allow access from VPN
add action=accept \
    chain=input \
    in-interface=wireguard-vpn \
    comment="Allow from VPN"

# Drop all other input
add action=drop \
    chain=input \
    comment="Drop all other input"

# Forward chain rules
add action=accept \
    chain=forward \
    connection-state=established,related \
    comment="Accept established/related forward"

# Allow VPN clients to access Internet
add action=accept \
    chain=forward \
    in-interface=wireguard-vpn \
    out-interface=ether5-internet \
    comment="VPN to Internet"

# Allow LAN to all WANs
add action=accept \
    chain=forward \
    in-interface=bridge-lan \
    comment="Allow LAN to WAN"

# Allow Internet to VPN (return traffic)
add action=accept \
    chain=forward \
    in-interface=ether5-internet \
    out-interface=wireguard-vpn \
    connection-state=established,related \
    comment="Internet to VPN (return traffic)"

# Drop invalid connections
add action=drop \
    chain=forward \
    connection-state=invalid \
    comment="Drop invalid"

# Drop all other forward
add action=drop \
    chain=forward \
    comment="Drop all other forward"

# =====================================================
# 11. DNS CONFIGURATION
# =====================================================

/ip dns
set allow-remote-requests=yes \
    servers=8.8.8.8,1.1.1.1

# =====================================================
# 12. ADDITIONAL SECURITY
# =====================================================

# Disable unnecessary services
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=no
set api disabled=yes
set api-ssl disabled=yes

# Enable only SSH and Winbox
set ssh disabled=no
set winbox disabled=no

# Change default ports (recommended)
set ssh port=22222
set winbox port=8291

# =====================================================
# 13. MONITORING AND LOGGING
# =====================================================

/system logging
add topics=wireguard action=memory
add topics=firewall action=memory

# =====================================================
# CONFIGURATION COMPLETE
# =====================================================
#
# IMPORTANT NOTES:
# 1. Replace "YOUR_SERVER_PRIVATE_KEY_HERE" with your actual WireGuard private key
# 2. Server public key: OkMrWI423O6h0Fgvg40RRvzWBLv1bC4CEfNi9INlph0=
# 3. Client 1 public key: L1MLvxKfg0zzA6JYQbCbhYtZm/QFadlllHbYRqlD5SM=
# 4. Test connectivity after applying configuration
# 5. Verify routing with: /ip route print
# 6. Check WireGuard status: /interface wireguard print
# 7. Monitor firewall: /ip firewall filter print stats
#
# TRAFFIC FLOW:
# - VPN Clients (192.168.200.0/24) -> Port 5 (Internet)
# - LAN Clients (192.168.100.0/24) -> Port 1 (Primary) or Port 2 (Backup) to Intranet
# - Failover: Port 1 (distance=1) -> Port 2 (distance=2) -> Port 5 (distance=3)
#
# =====================================================
