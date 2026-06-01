import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('localhost', port=30101, username='onos', password='rocks')

chan = ssh.invoke_shell()
time.sleep(1)
commands = [
    "link-add netconf:10.42.0.1:1831/4201 netconf:10.42.0.1:1832/5101",
    "link-add netconf:10.42.0.1:1832/4201 netconf:10.42.0.1:1833/5101",
    "link-add netconf:10.42.0.1:1833/4201 netconf:10.42.0.1:1834/5101",
    "link-add netconf:10.42.0.1:1834/4201 netconf:10.42.0.1:1831/5101",
    "links"
]

for cmd in commands:
    chan.send(cmd + "\n")
    time.sleep(0.5)

out = chan.recv(99999).decode('utf-8')
print(out)
