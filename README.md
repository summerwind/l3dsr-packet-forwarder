# L3DSR Packet Forwarder

L3DSR Packet Forwarder is an experimental XDP program that forwards packets to another host like L3DSR compatible load balancer.

## Requirements

- XDP supported network driver
- BCC (https://github.com/iovisor/bcc)

## Usage

The forwarder is started as follows. In the following example, the forwarder will set the value of DSCP to *7* for packet addressed to port *80* of *192.168.10.10* received on *eth1* interface and forward it to *192.168.10.11*.

```
$ sudo ./forwarder.py -i eth1 -v 192.168.10.10 -p 80 -d 192.168.10.11 -D 7
```

## Vagrant

You can build an experimental environment using Vagrant. Note that it is necessary to restart the VM for forwarder in order to change the kernel after `vagrant up`.

```
$ vagrant up
$ vagrant reload forwarder
$ vagrant ssh forwarder
```

