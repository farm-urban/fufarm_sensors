# Raspberry Pi Setup

### Hack for wpa_supplicant
This is requried because of a bug with the drivers - the different interfaces seem to fight with each other. The fix seems to be to restart the wpa_supplicant deamon.
> Not sure if the below actually required or could just continue with default wpa_supplicant?
```
sudo systemctl disable wpa_supplicant
sudo systemctl enabl wpa_supplicant@wlan0
```

Create file: ```/usr/local/bin/restart_wpa_supplicant.sh```
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

## OpenVPN
### On n8 server
Generate certificate:

```
/home/jmht/fu_sensors/mk_openvpn.py <client_name>
```

 Creates a file called <client_name>```.ovpn``` This needs to be copied into the ```/etc/openvpn/client``` directory on the raspberry pi.

 Create a file called ```/etc/openvpn/ccd/<client_name>``` containing:
 ```
 ifconfig-push 10.8.0.207 255.255.255.0 # CHANGE SECOND IP TO BE THAT GIVEN TO THE CLIENT
 push "redirect-gateway def1 bypass-dhcp"
 push "remote-gateway vpn_server_ip"
 push "dhcp-option DNS 8.8.8.8"
 push "dhcp-option DNS 8.8.4.4"
 ```

### On Raspberry Pi
```
sudo apt install openvpn
sudo scp jmht@farmuaa2.miniserver.com:fu_sensors/rpi2.ovpn /etc/openvpn/client/rpi2.conf
sudo systemctl enable openvpn-client@rpi2
```

## Sensor setup
sudo apt-get install git
cd /opt
sudo git clone https://github.com/linucks/fu_sensors.git
sudo chown -R pi:pi fu_sensors


Edit ```/opt/fu_sensors/InfluxDB/rpi_sensors.py``` to set:
```STATION_MAC = 'rpi2utc'```

```
sudo apt-get install  python3-gpiozero python3-pigpio
# Need to start as a service - does this need to be done on each restart?
sudo pigpiod
```

Create a service to run the sensor script. Create file: ```/etc/systemd/system/farm_sensors.service```

```
[Unit]
After=openvpn-client@loz1.service

[Service]
ExecStart=python3 /opt/fu_sensors/dfrobot/raspberrypi/poll_data.py
WorkingDirectory=/opt/fu_sensors/dfrobot/raspberrypi
Restart=always
StandardOutput=append:/opt/fu_sensors/dfrobot/raspberrypi/poll.log
StandardError=inherit
SyslogIdentifier=loz_sensors
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
```

Then enable with:
```
sudo systemctl enable farm_sensors.service
sudo systemctl start farm_sensors.service
```


## Setting up webcams
Install motion (https://motion-project.github.io/motion_config.html):
``
sudo apt-get install motion

```
In file ```/etc/motion/motion.conf``` Uncomment
```; camera_dir /etc/motion/conf.d
```

sudo mkdir /etc/motion/conf.d

Create file ```/etc/motion/conf.d/camera1.conf```
```
camera_id = 1
videodevice /dev/v4l/by-id/usb-Generic_USB_Camera_200901010001-video-index0
v4l2_palette 15

width 320
height 240

text_left CAMERA 1
picture_filename CAM1_%v-%Y%m%d%H%M%S-%q

stream_localhost off
stream_port 8081

framerate 5
# Maximum framerate for stream streams (default: 1)
stream_maxrate 3
```



Create file ```/etc/motion/conf.d/camera2.conf```
```
camera_id = 2
videodevice /dev/v4l/by-id/usb-AVEO_Technology_Corp._USB2.0_Camera-video-index0
v4l2_palette 15

width 320
height 240

text_left CAMERA 2
picture_filename CAM2_%v-%Y%m%d%H%M%S-%q

stream_localhost off
stream_port 8082

framerate 5
# Maximum framerate for stream streams (default: 1)
stream_maxrate 3
```

 sudo vi /etc/default/motion - change start_motion_daemon=yes
Enable as service
```
sudo chown -R motion:motion /var/log/motion/
sudo systemctl enable motion
sudo systemctl start motion
```


Then need to use nginx to proxy to the 8081 port of the raspberry pi, so on n8 server set up files like:

```
/etc/nginx/sites-available/rpi_cam1

server {
    listen 80;
    server_name cam1.farm.farmurban.co.uk;
    location / {
        proxy_pass http://10.8.0.208:8081;
    }
}
```

## Bluelab Setup
1. To allow remote desktop access set `hdmi_force_hotplug=1` in `/boot/config.txt` and reboot.
2. In `raspi-config` **Interface Options** enable VNC (might need to install vncserver-x11-serviced)
3. Log in via ssh and forward X11 connection using: `ssh -Y pi@raspberrypi.local` - this is required because running the setup script via the remote desktop gave a blank yellow screen.
4. Download connect software onto Pi from https://bluelab.com/united_kingdom/connect-software
5. Make script `bluelab_connect_unix_2_1_9.sh` executable and run via xterm as sudo  - it will install into `/opt/Connect/Bluelab`
6. Edit `/opt/Connect/Bluelab/connect` to add option `-Dsun.java2d.opengl=true` to the command-line flags.
7. Scripts and logs are found in: `$HOME/.local/share/Bluelab/Connect/logs`

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

## Actual sequence of commands
```
export CLIENT_NAME="rpi2"

sudo apt-get update
sudo apt-get upgrade

# https://raspberrypi.stackexchange.com/questions/28907/how-could-one-automate-the-raspbian-raspi-config-setup
# Wi-Fi is currently blocked by rfkill.
# Use raspi-config to set the country before use.
sudo raspi-config nonint do_wifi_country GB

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
#driver=nl80211
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
country=GB
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

sudo sed -i.bak -e "/# Don't delete these required lines/ {r /tmp/nat.rules" -e 'N}' /etc/ufw/before.rules

# OpenVpn
sudo apt install openvpn
sudo scp jmht@farmuaa2.miniserver.com:fu_sensors/${CLIENT_NAME}.ovpn /etc/openvpn/client/${CLIENT_NAME}.conf
sudo systemctl enable openvpn-client@${CLIENT_NAME}


# Webcam
sudo apt-get install motion
sudo mkdir /etc/motion/conf.d

# Camera 1 config
sudo bash -c 'cat <<EOF > /etc/motion/conf.d/camera1.conf
camera_id = 1
videodevice /dev/v4l/by-id/usb-Generic_USB_Camera_200901010001-video-index0
v4l2_palette 15

width 320
height 240

text_left CAMERA 1
picture_filename CAM1_%v-%Y%m%d%H%M%S-%q

stream_localhost off
stream_port 8081

framerate 5
# Maximum framerate for stream streams (default: 1)
stream_maxrate 3
EOF'

# Camera 2 config
sudo bash -c 'cat <<EOF > /etc/motion/conf.d/camera2.conf
camera_id = 2
videodevice /dev/v4l/by-id/usb-AVEO_Technology_Corp._USB2.0_Camera-video-index0
v4l2_palette 15

width 320
height 240

text_left CAMERA 2
picture_filename CAM2_%v-%Y%m%d%H%M%S-%q

stream_localhost off
stream_port 8082

framerate 5
# Maximum framerate for stream streams (default: 1)
stream_maxrate 3
EOF'


# /etc/motion/motion.conf
sudo sed -i.bak -e 's/^; camera_dir/camera_dir/' /etc/motion/motion.conf
# /etc/default/motion
sudo sed -i.bak -e 's/start_motion_daemon=no/start_motion_daemon=yes/' /etc/default/motion

# Enable as service - think the first is a bug
sudo chown -R motion:motion /var/log/motion/
sudo systemctl enable motion
sudo systemctl start motion


## Sensor setup
sudo apt-get install git
cd /opt
sudo git clone https://github.com/linucks/fu_sensors.git
sudo chown -R pi:pi fu_sensors
# Edit /opt/fu_sensors/InfluxDB/rpi_sensors.py to set: STATION_MAC = 'rpi2utc'

sudo apt-get install  python3-gpiozero python3-pigpio
# Need to start as a service - does this need to be done on each restart?
sudo pigpiod


sudo bash -c "cat <<EOF >/etc/systemd/system/farm_sensors.service
[Unit]
After=openvpn-client@${CLIENT_NAME}.service

[Service]
ExecStart=python3 /opt/fu_sensors/InfluxDB/rpi_sensors.py
WorkingDirectory=/opt/fu_sensors/InfluxDB
Restart=always
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=farm_sensors
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOF
"

sudo systemctl enable farm_sensors.service
sudo systemctl start farm_sensors.service

```