# Raspberry Pi Setup
* Copy image to disk: https://www.raspberrypi.org/documentation/installation/installing-images/mac.md
* Mount on OSX and goto /Volumes/boot folder and add:
   * `touch ssh`
   * Edit `config.txt` and append `dtoverlay=dwc2`
   * Edit `cmdline.txt` and after `rootwait` add text `modules-load=dwc2,g_ether`
   * (Possibly) `touch avahi`

Plug in OTG USB cable to middle USB port and then login with:
```
ssh pi@raspberrypi.local
```

### Set editor and make sure it's kept during sudo
```
~/.profile
EDITOR=/usr/bin/vi
sudo visudo
Defaults env_keep += "EDITOR"
```


## OPENVPN
**NEED TO ADD INSTRUCTIONS HERE OR IN OTHER DOC**

sudo systemctl enable openvpn-client@rpizero1


# Raspbery Pi as AP
[Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/configuration/wireless/access-point-routed.md])

**/etc/wpa_supplicant/wpa_supplicant.conf**
```
country=UK
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="virginmedia7305656"
    psk="vbvnqjxn"
}
```


### Install/enable software to work as access point
```
sudo apt install hostapd
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo apt install dnsmasq
```

### Wireless Interface Configuration
This requires deciding on the network to manage: (192.168.4.1/24)

Edit: **/etc/dhcpcd.conf**
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```
Reload
```
sudo service dhcpcd restart
```
??? Warning: The unit file, source configuration file or drop-ins of dhcpcd.service changed on disk. Run 'systemctl daemon-reload' to reload units.

### Enable routing and IP masquerading
**NB:** Don't think this first bit is required if using ufw

Edit: **/etc/sysctl.d/routed-ap.conf**
```
# https://www.raspberrypi.org/documentation/configuration/wireless/access-point-routed.md
# Enable IPv4 routing
net.ipv4.ip_forward=1
```

### Use UFW to manage Masqurading
From: https://gist.github.com/kimus/9315140
And: https://mike632t.wordpress.com/2019/02/02/configuring-a-linux-wireless-access-point/


In the file **/etc/default/ufw** change the parameter DEFAULT_FORWARD_POLICY

```
DEFAULT_FORWARD_POLICY="ACCEPT"
```

Also configure **/etc/ufw/sysctl.conf** to allow ipv4 forwarding (the parameters is commented out by default). Uncomment for ipv6 if you want.

```
net.ipv4.ip_forward=1
#net/ipv6/conf/default/forwarding=1
#net/ipv6/conf/all/forwarding=1
```


The final step is to add NAT to ufw’s configuration. Add the following to /etc/ufw/before.rules just before the filter rules.

```
# NAT table rules
*nat
:POSTROUTING ACCEPT [0:0]

# Forward traffic through eth0 - Change to match you out-interface
-A POSTROUTING -s 192.168.4.1/24 -o eth0 -j MASQUERADE

# don't delete the 'COMMIT' line or these nat table rules won't
# be processed
COMMIT
```

Set up rules to allow incoming connections for DNS and DHCP queries.
```
sudo ufw allow in on wlan0 from any port 68 to any port 67 proto udp
sudo ufw allow in on wlan0 from 192.168.4.1/24 to any port 53
```

Now enable the changes by restarting ufw.

```
$ sudo ufw disable && sudo ufw enable
```

### Configure the DHCP and DNS services for the wireless network

Backup **/etc/dnsmasq.conf** and create new file with:
```
interface=wlan0 # Listening interface
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h # Pool of IP addresses served via DHCP
## jmht - last 2 not included in old config
#domain=wlan # Local wireless DNS domain
#address=/gw.wlan/192.168.4.1 # Alias for this router
```
 ### Configure the access point software
 Edit **/etc/hostapd/hostapd.conf**
```
interface=wlan0
driver=nl80211
ssid=FUsensors
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=12345678
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

### Reboot
```
sudo systemctl reboot
```


# Raspbery Pi as AP and STA
Rather then using the wlan0 that was set up above as the AP interface we create a virtual interface called uap0.

https://superuser.com/questions/1272705/wifi-single-radio-acting-as-ap-and-ap-client-simultaneously
https://www.raspberrypi.org/forums/viewtopic.php?f=36&t=138730&sid=9b945f0b20a96d90875f80c1c8c06e8e
https://superuser.com/questions/615664/creating-wifi-access-point-on-a-single-interface-in-linux
https://imti.co/iot-wifi/
https://www.raspberrypi.org/forums/viewtopic.php?t=191306

https://github.com/peebles/rpi3-wifi-station-ap-stretch


### Create Interface
Create file: **/etc/udev/rules.d/90-wireless.rules**
```
ACTION=="add", SUBSYSTEM=="ieee80211", KERNEL=="phy0", \
    RUN+="/sbin/iw phy %k interface add uap0 type __ap"
```

Create file: **/etc/network/interfaces.d/ap**
```
allow-hotplug uap0
auto uap0
iface uap0 inet static
    address 192.168.4.1
    netmask 255.255.255.0
```


### Wireless Interface Configuration
This requires deciding on the network to manage: (192.168.4.1/24)

Edit: **/etc/dhcpcd.conf**
```
#denyinterfaces wlan0    # don't send DHCP requests
nohook wpa_supplicant   # don't call the wpa_supplicant hook

interface uap0
static ip_address=192.168.4.1/24 # Not sure if needed?
```

### Configure the DHCP and DNS services for the wireless network
Backup **/etc/dnsmasq.conf** and create new file with:

```
interface=lo,uap0
no-dhcp-interface=lo,wlan0
bind-interfaces
server=8.8.8.8
domain-needed
bogus-priv
dhcp-range=192.168.4.100,192.168.4.200,255.255.255.0,24h
```

### Configure the access point software
 Edit **/etc/hostapd/hostapd.conf**
```
interface=uap0
driver=nl80211
ssid=FUsensors
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=12345678
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

### Setup wireless access as STA
Delete: **/etc/wpa_supplicant/wpa_supplicant.conf**
Create: **/etc/wpa_supplicant/wpa_supplicant-wlan0.conf**
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#ap_scan=1
#update_config=1
network={
    ssid="virginmedia7305656"
    psk="vbvnqjxn"
}
```

### Hack for wpa_supplicant
This is requried because of a bug with the drivers - I think. The cure is to restart the wpa_supplicant servie on wlan0 after a pause and everything else has come up
```
sudo systemctl disable wpa_supplicant
```

Create file: **/etc/systemd/system/wpa_supplicant_hack.service**
```
[Unit]
Description=Service to restart wpa_supplicant@wlan0
After=wpa_supplicant@wlan0.service

[Service]
Type=simple
ExecStartPre=/bin/sh -c 'sleep 10'
ExecStart=/bin/systemctl restart wpa_supplicant@wlan0.service
#StandardOutput=file:/var/log/wpa_supplicant_hack.log
#StandardError=file:/var/log/wpa_supplicant_hack.log

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable wpa_supplicant_hack
```


### Use UFW to manage Masquerading
From: https://gist.github.com/kimus/9315140
And: https://mike632t.wordpress.com/2019/02/02/configuring-a-linux-wireless-access-point/


In the file **/etc/default/ufw** change the parameter DEFAULT_FORWARD_POLICY

```
DEFAULT_FORWARD_POLICY="ACCEPT"
```

Also configure **/etc/ufw/sysctl.conf** to allow ipv4 forwarding (the parameters is commented out by default). Uncomment for ipv6 if you want.

```
net.ipv4.ip_forward=1
#net/ipv6/conf/default/forwarding=1
#net/ipv6/conf/all/forwarding=1
```


The final step is to add NAT to ufw’s configuration. Add the following to /etc/ufw/before.rules just before the filter rules.

```
# NAT table rules
*nat
:POSTROUTING ACCEPT [0:0]

# Forward traffic through eth0 - Change to match you out-interface
-A POSTROUTING -s 192.168.4.1/24 -o eth0 -j MASQUERADE

# don't delete the 'COMMIT' line or these nat table rules won't
# be processed
COMMIT
```

Set up rules to allow incoming connections for DNS and DHCP queries.
```
sudo ufw allow in on uap0 from any port 68 to any port 67 proto udp
sudo ufw allow in on uap0 from 192.168.4.1/24 to any port 53
```

Now enable the changes by restarting ufw.

```
$ sudo ufw disable && sudo ufw enable
```

## Debugging/Maintainence commands
```
sudo systemctl stop dhcpcd
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
#wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
sudo wpa_cli -i wlan0 reconfigure
sudo systemctl stop wpa_supplicant
sudo wpa_supplicant -d -iwlan0 -c /etc/wpa_supplicant/wpa_supplicant-wlan0.conf 
sudo systemctl edit --full wpa_supplicant@wlan0
sudo /etc/init.d/networking restart
sudo ifconfig wlan0 down
sudo ifconfig wlan0 up
```