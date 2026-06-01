import paramiko
import time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('localhost', port=30101, username='onos', password='rocks')
chan = ssh.invoke_shell(width=200)
time.sleep(1)
chan.send("null-create-link optical netconf:10.42.0.1:1831/4201 netconf:10.42.0.1:1832/5101\n")
time.sleep(2)
chan.send("log:display | tail -n 20\n")
time.sleep(2)
out = chan.recv(99999).decode('utf-8')
print(out)
