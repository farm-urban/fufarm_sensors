#!/usr/bin/env python3

# Need to run below command first:
# easyrsa build-client-full <CLIENT_NAME> nopass

import os
import re
import subprocess
import sys

def get_certificate(cfile):
    with open(cfile) as f:
        txt = f.read()
    cert_blob = re.search(r'.*-----BEGIN CERTIFICATE-----\n(.*)\n-----END CERTIFICATE-----.*', txt, re.DOTALL)
    return cert_blob.group(1)

def get_key(cfile):
    with open(cfile) as f:
        txt = f.read()
    cert_blob = re.search(r'.*-----BEGIN PRIVATE KEY-----\n(.*)\n-----END PRIVATE KEY-----.*', txt, re.DOTALL)
    return cert_blob.group(1)

OVPN = """client
dev tun
proto tcp
remote 78.31.105.128 443
nobind
persist-key
persist-tun
cipher AES-256-CBC

key-direction 1

<ca>
-----BEGIN CERTIFICATE-----
{ca_blob}
-----END CERTIFICATE-----
</ca>

<cert>
-----BEGIN CERTIFICATE-----
{cert_blob}
-----END CERTIFICATE-----
</cert>

<key>
-----BEGIN PRIVATE KEY-----
{key_blob}
-----END PRIVATE KEY-----
</key>
"""

easyrsa_dir = "/home/jmht/EasyRSA-v3.0.6"
easyrsa_exe = os.path.join(easyrsa_dir, 'easyrsa')
ca_passwd = "FarmUrban!sAwesome"

if len(sys.argv) != 2:
    print("Usage: {} <client_name>".format(sys.argv[0]))
    sys.exit(1)
client_name = sys.argv[1]

ca_file = os.path.join(easyrsa_dir, "pki/ca.crt")
cert_file = os.path.join(easyrsa_dir, "pki/issued/{}.crt".format(client_name))
key_file = os.path.join(easyrsa_dir, "pki/private/{}.key".format(client_name))

build_cmd = [easyrsa_exe, 'build-client-full', client_name, 'nopass']
if not os.path.isfile(cert_file):
    print("Generating keys with: easyrsa_exe build-client-full {} nopass".format(client_name))
    ret = subprocess.run(build_cmd, cwd=easyrsa_dir)
    ret.check_returncode()

#./pki/reqs/sam_android.req
#./pki/issued/sam_android.crt
#./pki/private/sam_android.key
ca_blob = get_certificate(ca_file)
cert_blob = get_certificate(cert_file)
key_blob = get_key(key_file)

d = {'ca_blob': ca_blob, 'cert_blob': cert_blob, 'key_blob': key_blob}
fname = client_name + '.ovpn'
with open(fname, 'w') as w:
    w.write(OVPN.format(**d))
