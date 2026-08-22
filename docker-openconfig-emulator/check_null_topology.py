import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect("localhost", port=30101, username="onos", password="rocks")
    channel = client.invoke_shell()
    time.sleep(1)
    
    channel.send("devices\n")
    time.sleep(2)
    output = channel.recv(65535).decode("utf-8")
    print("DEVICES:")
    print(output)
    
    channel.send("links\n")
    time.sleep(2)
    output2 = channel.recv(65535).decode("utf-8")
    print("LINKS:")
    print(output2)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
