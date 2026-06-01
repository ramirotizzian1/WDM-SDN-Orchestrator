import paramiko
import time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('localhost', port=30101, username='onos', password='rocks')
chan = ssh.invoke_shell(width=200)
time.sleep(1)
chan.send("help | grep -i optical\n")
time.sleep(2)
out = chan.recv(99999).decode('utf-8')
print(out)
