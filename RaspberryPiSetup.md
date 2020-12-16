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
Add to ```~/.profile```
```
set -o emacs
export EDITOR=/usr/bin/vi
```

Then keep for sudo
```
sudo visudo
Defaults env_keep += "EDITOR"
```

# Configure Raspberry Pi as AP, and also combined AP and STA

## Install/enable software to work as access point
```
sudo apt install hostapd
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo apt install dnsmasq
```


## Raspbery Pi as AP
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


### Wireless Interface Configuration
This requires deciding on the network to manage: (192.168.4.1/24)

Edit: **/etc/dhcpcd.conf**
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
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

# DNS suddenly stopped working on wlan0 - no idea why - so this required
interface wlan0
static domain_name_servers=8.8.8.8
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

Delete: **/etc/wpa_supplicant/wpa_supplicant.conf**
Create: **/etc/wpa_supplicant/wpa_supplicant-wlan0.conf**
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#ap_scan=1
update_config=1
network={
	ssid="LLS_BYOD"
	key_mgmt=NONE
}

network={
    ssid="foo"
    psk="bar"
}
```

### Hack for wpa_supplicant
This is requried because of a bug with the drivers - the different interfaces seem to fight with each other. The fix seems to be to restart the wpa_supplicant deamon.
# Not sure if the below actually required or could just continue with default wpa_supplicant?
```
sudo systemctl disable wpa_supplicant
sudo systemctl enabl wpa_supplicant@wlan0
```

Create file: **/usr/local/bin/restart_wpa_supplicant.sh**
```
#!/bin/bash
# nc quicker but need to specify interace with ip
#nc -zw 2 www.google.co.uk 81 > /dev/null 2>&1
#ping -I wlan0 -c 1  www.google.co.uk > /dev/null 2>&1
ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' > /dev/null 2>&1
if [ $? -ne 0 ]
then
    echo "Restarting wpa_supplicant on wlan0
    /bin/systemctl restart wpa_supplicant@wlan0.service
fi
```

```
sudo crontab -e
*/5 * * * * /usr/local/bin/restart_wpa_supplicant.sh | /usr/bin/logger -t jmht_wpa
```

## Commands for both types of Setup

### Use UFW as firewall
```
sudo apt-get install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22
sudo ufw enable
```

### Use UFW to manage routing and IP masquerading
From: https://gist.github.com/kimus/9315140
And: https://mike632t.wordpress.com/2019/02/02/configuring-a-linux-wireless-access-point/


In the file **/etc/default/ufw** change the parameter DEFAULT_FORWARD_POLICY

```
DEFAULT_FORWARD_POLICY="ACCEPT"
```

Also configure **/etc/ufw/sysctl.conf** to allow ipv4 forwarding (the parameters is commented out by default). Uncomment for ipv6 if you want.

```
net.ipv4.ip_forward=1
```

Alternative format
```
net/ipv4/ip_forward=1
```


** DON'T THINK BELOW REQUIRED DUE TO ufc sysctl.conf parameter? **
Edit: **/etc/sysctl.d/routed-ap.conf**
```
# https://www.raspberrypi.org/documentation/configuration/wireless/access-point-routed.md
# Enable IPv4 routing
net.ipv4.ip_forward=1
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
CHANGE INTERFACE wlan0 to uap0 for COMBINED
```
sudo ufw allow in on wlan0 from any port 68 to any port 67 proto udp
sudo ufw allow in on wlan0 from 192.168.4.1/24 to any port 53
```


## OPENVPN
**NEED TO ADD INSTRUCTIONS HERE OR IN OTHER DOC**

sudo systemctl enable openvpn-client@rpizero1



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

## Setting up webcams
Need to install motion

/etc/motion/motion.conf - changed settings
```
< daemon on
#v4l2_palette 17
v4l2_palette 9
width 640
height 480
framerate 60
output_pictures off
ffmpeg_output_movies off
target_dir /home/pi
stream_maxrate 10
stream_localhost off
stream_localhost on
```
camera2.conf
```
# /etc/motion/camera2.conf
camera_id = 2
videodevice /dev/v4l/by-id/usb-AVEO_Technology_Corp._USB2.0_Camera-video-index0
v4l2_palette 15

width 320
height 240

text_left CAMERA 2
picture_filename CAM2_%v-%Y%m%d%H%M%S-%q

framerate 5
stream_port 8082
# Maximum framerate for stream streams (default: 1)
stream_maxrate 3
```

Then need to use nginx to proxy to the 8081 port of the raspberry pi:

```
/etc/nginx/sites-available/influxdb
server {
    listen 192.168.4.1:8086;
    server_name _;
    location / {
        proxy_pass http://10.8.0.1:8086;
    }
}
```

## Actual sequence of commands
sudo apt-get update
sudo apt-get upgrade

#  Install software
sudo apt install hostapd
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo apt install dnsmasq

# Create interface
sudo bash -c 'cat <<EOF >  /etc/udev/rules.d/90-wireless.rules
ACTION=="add", SUBSYSTEM=="ieee80211", KERNEL=="phy0", \
 RUN+="/sbin/iw phy %k interface add uap0 type __ap"
EOF'

sudo bash -c 'cat <<EOF > /etc/network/interfaces.d/ap
allow-hotplug uap0
auto uap0
iface uap0 inet static
    address 192.168.4.1
    netmask 255.255.255.0
EOF'

sudo bash -c 'cat <<EOF >> /etc/dhcpcd.conf

# Wireless AP
interface uap0
nohook wpa_supplicant  # dont call the wpa_supplicant hook
static ip_address=192.168.4.1/24 # Not sure if needed?
EOF'

# Configure the DHCP and DNS services for the wireless network
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.bak
sudo bash -c 'cat <<EOF > /etc/dnsmasq.conf
interface=lo,uap0
no-dhcp-interface=lo,wlan0
bind-interfaces
server=8.8.8.8
domain-needed
bogus-priv
dhcp-range=192.168.4.100,192.168.4.200,255.255.255.0,24h
EOF'

# Configure the access point software
sudo bash -c 'cat <<EOF > /etc/hostapd/hostapd.conf
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
EOF'

# setup wireless access
sudo mv /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.bak
sudo bash -c 'cat <<EOF > /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#ap_scan=1
update_config=1
network={
	ssid="LLS_BYOD"
	key_mgmt=NONE
}

EOF'

# Enable UFWsudo apt-get install ufw
sudo apt-get install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22
sudo ufw enable


# Forwarding
sudo sed -i.bak -e 's/^DEFAULT_FORWARD_POLICY=.*$/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw


# /etc/ufw/sysctl.conf
sudo sed -.ibak -e \@net/ipv4/ip_forward@s@^#@@g' /etc/ufw/sysctl.conf

# NAT RULES
cat <<EOF > /tmp/nat.rules
# NAT table rules
*nat
:POSTROUTING ACCEPT [0:0]

# Forward traffic through eth0 - Change to match you out-interface
-A POSTROUTING -s 192.168.4.1/24 -o eth0 -j MASQUERADE

# don't delete the 'COMMIT' line or these nat table rules won't
# be processed
COMMIT

EOF

sudo sed -i.bak -e "/# Don't delete these required lines/ {r /tmp/nat.rules" -e 'N}' before.rules


# Webcam
sudo apt-get install motion
