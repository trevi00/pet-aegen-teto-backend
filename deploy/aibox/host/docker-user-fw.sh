#!/bin/sh
# Docker 게시 포트가 ufw 를 우회하는 문제 차단 (DOCKER-USER 체인).
# LAN(enp6s0)에서 컨테이너로 들어오는 새 연결은 허용 IP 만, 나머지 DROP.
# 컨테이너의 외부 연결(cloudflared 등) 응답은 ESTABLISHED 로 통과.
# 허용 IP 가 바뀌면(공유기 교체 등) ALLOW_V4 만 고치고: sudo systemctl restart docker-user-fw
set -eu
IFACE="enp6s0"
ALLOW_V4="192.168.0.65"

for ipt in iptables ip6tables; do
    $ipt -N DOCKER-USER 2>/dev/null || true
    $ipt -F DOCKER-USER
    $ipt -A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN
done
for ip in $ALLOW_V4; do
    iptables -A DOCKER-USER -i "$IFACE" -s "$ip" -j RETURN
done
iptables  -A DOCKER-USER -i "$IFACE" -j DROP
ip6tables -A DOCKER-USER -i "$IFACE" -j DROP
iptables  -A DOCKER-USER -j RETURN
ip6tables -A DOCKER-USER -j RETURN
