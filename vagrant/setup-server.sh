#!/bin/bash

apt-get update
apt-get install -y git build-essential iptables-dev nginx

echo "net.ipv4.conf.default.arp_ignore = 1"   | tee -a /etc/sysctl.d/nf.conf
echo "net.ipv4.conf.default.arp_announce = 2" | tee -a /etc/sysctl.d/nf.conf
echo "net.ipv4.conf.default.rp_filter = 0"    | tee -a /etc/sysctl.d/nf.conf
echo "net.ipv4.conf.all.arp_ignore = 1"       | tee -a /etc/sysctl.d/nf.conf
echo "net.ipv4.conf.all.arp_announce = 2"     | tee -a /etc/sysctl.d/nf.conf
echo "net.ipv4.conf.all.rp_filter = 0"        | tee -a /etc/sysctl.d/nf.conf
sysctl -p

cd /tmp
git clone https://github.com/yahoo/l3dsr.git
cd l3dsr/linux
sed -i -e "s/iptables.h/xtables.h/g" extensions-1.4/libxt_DADDR.c
make
install -m 644 kmod-xt/xt_DADDR.ko /lib/modules/`uname --kernel-release`/kernel/net/netfilter/
install -m 644 extensions-1.4/libxt_DADDR.so /lib/xtables

insmod /lib/modules/`uname --kernel-release`/kernel/net/netfilter/xt_DADDR.ko

iptables -t mangle -A PREROUTING -m dscp --dscp 7 -j DADDR --set-daddr=192.168.10.10
ifconfig lo:1 192.168.10.10 netmask 255.255.255.255
