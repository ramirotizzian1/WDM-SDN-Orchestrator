import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect("localhost", port=30101, username="onos", password="rocks")
    channel = client.invoke_shell()
    time.sleep(1)
    
    channel.send("add-optical-intent null:roadm1/1 null:roadm3/1\n")
    time.sleep(2)
    output = channel.recv(65535).decode("utf-8")
    print("OUTPUT:", output)
    
    channel.send("intents\n")
    time.sleep(2)
    output = channel.recv(65535).decode("utf-8")
    print("INTENTS:", output)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
