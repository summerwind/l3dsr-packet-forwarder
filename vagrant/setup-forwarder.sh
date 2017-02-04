#!/bin/bash

apt-key adv --keyserver keyserver.ubuntu.com --recv-keys D4284CDD
echo "deb [trusted=yes] https://repo.iovisor.org/apt trusty kernel" | tee /etc/apt/sources.list.d/iovisor.list
echo "deb [trusted=yes] https://repo.iovisor.org/apt/trusty trusty-nightly main" | tee -a /etc/apt/sources.list.d/iovisor.list

apt-get update
apt-get install -y git bcc-tools "linux-headers-4.7.0-07282016-torvalds+" "linux-image-4.7.0-07282016-torvalds+"

#arp -s 192.168.10.11 08:00:27:33:3c:72
