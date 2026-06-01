import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('localhost', port=30101, username='onos', password='rocks')

chan = ssh.invoke_shell()
time.sleep(1)
chan.send("drivers\n")
time.sleep(1)
out = chan.recv(99999).decode('utf-8')
for line in out.splitlines():
    if "lumentum" in line.lower():
        print(line)
