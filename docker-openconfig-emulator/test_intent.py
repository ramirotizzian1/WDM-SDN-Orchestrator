import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect("localhost", port=30101, username="onos", password="rocks")
    channel = client.invoke_shell()
    time.sleep(1)
    
    # Send the optical intent command
    cmd = "add-optical-intent -b -s 4/50/1/dwdm netconf:10.42.0.1:11001/201 netconf:10.42.0.1:11003/201\n"
    print(f"Sending: {cmd}")
    channel.send(cmd)
    
    time.sleep(3)
    output = channel.recv(4096).decode("utf-8")
    print("OUTPUT:")
    print(output)
    
    # Check intents
    channel.send("intents\n")
    time.sleep(2)
    output2 = channel.recv(4096).decode("utf-8")
    print("INTENTS:")
    print(output2)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
