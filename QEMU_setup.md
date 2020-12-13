## Running Ubuntu under QEMU

Notes from:
* https://graspingtech.com/ubuntu-desktop-18.04-virtual-machine-macos-qemu/

In order to get a full command-line version, additional options need to be appended to the linux kernel parameters (this would normally be done by using -append "console=ttyS0" as a QEMU command-line flag). As we're not booting using our own kernel, we can't do this, so I booted graphically and then edited **/etc/default/grub** to set:
```
GRUB_CMDLINE_LINUX_DEFAULT=""
```

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
-nographic \
-vga none \ # not sure if last two actually needed
-serial mon:stdio \
```


## Raspberry Pi Setup
https://raspberrypi.stackexchange.com/questions/100384/running-raspbian-buster-with-qemu
https://blog.agchapman.com/using-qemu-to-emulate-a-raspberry-pi/
https://github.com/guysoft/CustomPiOS
https://medium.com/@r.robipozzi/use-ansible-to-automate-installation-and-deployment-of-raspberry-boxes-cfe04ac10ce6\
https://opensource.com/article/20/9/raspberry-pi-ansible
https://github.com/kenfallon/fix-ssh-on-pi
https://github.com/jonashackt/raspberry-ansible
https://hackernoon.com/raspberry-pi-cluster-emulation-with-docker-compose-xo3l3tyw

1. Download Server lite image
2. Mount image from linux and extract kernel and dtd files, or download from: https://github.com/dhruvvyas90/qemu-rpi-kernel/
3. Resize image to desired size: ```qemu-img resize 2020-12-02-raspios-buster-armhf-lite.img +6G```
4. Run using the following command:

```
qemu-system-arm \
  -drive "file=./2020-12-02-raspios-buster-armhf-lite.img,if=none,index=0,media=disk,format=raw,id=disk0" \
  -device "virtio-blk-pci,drive=disk0,disable-modern=on,disable-legacy=off" \
  -nic user,hostfwd=tcp::5555-:22 \ # user networking and allow ssh on local machine 5555
  -no-reboot \
  -M versatilepb -cpu arm1176 -m 256 \
  -dtb ./versatile-pb-buster.dtb \
  -kernel ./kernel-qemu-4.19.50-buster \
  -append 'root=/dev/vda2 panic=1' \
  -serial mon:stdio \
  -nographic \
```

5. Use parted to resize the partition to fill the desired space (up to last sector): ```parted /dev/vda resizepart 2 yes -- -1s```
6. Reread partition table: ```partprobe /dev/vda # re-read partition table```
7. Make filesystem fill available space: ```resize2fs /dev/vda5 # get your space```
