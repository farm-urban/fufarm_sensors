# Running Ubuntu under QEMU

Notes from:
* https://graspingtech.com/ubuntu-desktop-18.04-virtual-machine-macos-qemu/

```
id=ubuntu-20.04.1-live-server-amd64
disk_img="${id}.img.qcow2.2"
iso="${id}.iso"

# Create image file for disk
qemu-img create -f qcow2 "$disk_img" 12G```

# Run image
qemu-system-x86_64 \
-cdrom "$iso" \
-drive "file=${disk_img},format=qcow2" \
-m 1G \
-nic user \
-no-reboot \
-cpu host,-rdtscp,-accel hvf \ # enable hardware acceleration on OSX
```
