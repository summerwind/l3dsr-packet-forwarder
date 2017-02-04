#!/usr/bin/env python

import ctypes
import time
import argparse
import subprocess
import os

from bcc import BPF

BPF_CODE = """
#define KBUILD_MODNAME "forwarder"
#include <uapi/linux/bpf.h>
#include <linux/in.h>
#include <linux/if_ether.h>
#include <linux/if_packet.h>
#include <linux/if_vlan.h>
#include <linux/ip.h>
#include <linux/ipv6.h>

BPF_HASH(counter, uint32_t, long);

static inline unsigned short checksum(unsigned short *buf, int bufsz) {
    unsigned long sum = 0;

    while (bufsz > 1) {
        sum += *buf;
        buf++;
        bufsz -= 2;
    }

    if (bufsz == 1) {
        sum += *(unsigned char *)buf;
    }

    sum = (sum & 0xffff) + (sum >> 16);
    sum = (sum & 0xffff) + (sum >> 16);

    return ~sum;
}

int forwarder(struct xdp_md *ctx) {
    int rc = XDP_PASS;
    uint64_t nh_off = 0;

    unsigned short old_daddr;
    unsigned long sum;

    uint32_t index;
    long *value;
    long zero = 0;

    // Read data
    void* data_end = (void*)(long)ctx->data_end;
    void* data = (void*)(long)ctx->data;

    // Handle data as an ethernet frame header
    struct ethhdr *eth = data;

    // Verify size of ethernet frame header
    nh_off = sizeof(*eth);
    if (data + nh_off > data_end) {
        return rc;
    }

    // Verify protocol of ethernet frame
    if (eth->h_proto != htons(ETH_P_IP)) {
        return rc;
    }

    // Verify size of IP header
    struct iphdr *iph = data + nh_off;
    nh_off += sizeof(struct iphdr);
    if (data + nh_off > data_end) {
        return rc;
    }

    // Verify protocol of IP header
    if (iph->protocol != IPPROTO_TCP) {
        return rc;
    }

    // Verify destination address of IP header
    if (iph->daddr != htonl([[VIP_NUM]])) {
        return rc;
    }

    // Verify size of TCP header
    struct tcphdr *tcph = data + nh_off;
    nh_off += sizeof(struct tcphdr);
    if (data + nh_off > data_end) {
        return rc;
    }

    // Verify destination port of TCP header
    if (tcph->dest != htons([[PORT]])) {
        return rc;
    }

    // Override destination address of ethernet frame
    unsigned long long mac = [[MAC_NUM]];
    memcpy(eth->h_dest, &mac, sizeof eth->h_dest);

    // Backup current destination address of IP header
    old_daddr = ntohs(*(unsigned short *)&iph->daddr);

    // Override IP headers
    iph->daddr = htonl([[DST_NUM]]);
    iph->tos = [[DSCP]] << 2;
    iph->check = 0;
    iph->check = checksum((unsigned short *)iph, sizeof(struct iphdr));

    // Update TCP checksum
    sum = old_daddr + (~ntohs(*(unsigned short *)&iph->daddr) & 0xffff);
    sum += ntohs(tcph->check);
    sum = (sum & 0xffff) + (sum>>16);
    tcph->check = htons(sum + (sum>>16) - 1);

    // Increment counter
    index = 1;
    value = counter.lookup_or_init(&index, &zero);
    (*value)++;

    return XDP_TX;
}
"""

def run(i, vip, port, dest, dscp):
  mac = get_next_hop_mac(args.interface, args.destination)
  if mac is None:
    print "Destination unreachable (%s)" % args.destination
    sys.exit(1)

  code = BPF_CODE
  code = code.replace('[[MAC_NUM]]', str(mac_to_num(mac)))
  code = code.replace('[[VIP_NUM]]', str(ip_to_num(vip)))
  code = code.replace('[[DST_NUM]]', str(ip_to_num(dest)))
  code = code.replace('[[PORT]]', str(port))
  code = code.replace('[[DSCP]]', dscp)

  bpf = BPF(text=code, cflags=["-w", "-DRETURNCODE=XDP_TX", "-DCTXTYPE=xdp_md"])
  func = bpf.load_func("forwarder", BPF.XDP)
  bpf.attach_xdp(i, func)
  print("Fowarder started.")

  counter = bpf.get_table("counter")

  while True:
    try:
      for k, v in counter.items():
        sys.stdout.write("\rForwarded packets: %d" % v.value)
        sys.stdout.flush()
        time.sleep(1)
    except KeyboardInterrupt:
      break;

  print("\nDone.")
  bpf.remove_xdp(i)

def get_next_hop_mac(i, dst):
  ip = get_next_hop_ip(i, dst)
  if ip is None:
    return None

  return get_mac_by_ip(i, ip)

def get_next_hop_ip(i, dst):
  cmd_ip_route = "ip route get %s" % dst
  route = subprocess.check_output(cmd_ip_route, shell=True)

  if route.find(i) == -1:
    return None

  if route.find("via") == -1:
    return dst

  chunk = route.split(" ")
  return chunk[2]

def get_mac_by_ip(i, ip):
  cmd_ping = "ping -c 1 -W 1 -I %s %s" % (i, ip)
  devnull = open(os.devnull, 'wb')
  subprocess.call(cmd_ping, stdout=devnull, shell=True)
  devnull.close()

  cmd_arp = "cat /proc/net/arp | grep %s | grep %s | awk '{print $4;}'" % (i, ip)
  mac = subprocess.check_output(cmd_arp, shell=True)
  mac = mac.rstrip()

  if mac == "00:00:00:00:00:00":
    return None

  return mac

def ip_to_num(ip):
  ip = ip.split(".")
  return reduce(lambda a,b: a<<8 | b, map(int, ip))

def mac_to_num(mac):
  mac = mac.split(":")
  mac.reverse()
  return reduce(lambda a,b: a<<8 | b, [int(x, 16) for x in mac])

if __name__ == '__main__':
  import sys

parser = argparse.ArgumentParser(description='L3DSR packet forwarder.')
parser.add_argument('-i', '--interface',   required=True, help='Interface name')
parser.add_argument('-v', '--vip',         required=True, help='Virtual IP address')
parser.add_argument('-p', '--port',        required=True, help='Port number for Virtual IP address')
parser.add_argument('-d', '--destination', required=True, help='Destination IP address')
parser.add_argument('-D', '--dscp',        required=True, help='DSCP value')

args = parser.parse_args()

run(args.interface, args.vip, args.port, args.destination, args.dscp)

