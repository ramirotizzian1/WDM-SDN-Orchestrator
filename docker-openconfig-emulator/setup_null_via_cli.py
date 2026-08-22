import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect("localhost", port=30101, username="onos", password="rocks")
    channel = client.invoke_shell()
    time.sleep(1)
    
    commands = [
        "cfg set org.onosproject.provider.nil.NullProviders topoShape reroute",
        "cfg set org.onosproject.provider.nil.NullProviders deviceCount 4",
        "cfg set org.onosproject.provider.nil.NullProviders enabled true"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(2)
        
    channel.send("devices | grep null\n")
    time.sleep(2)
    output = channel.recv(65535).decode("utf-8")
    print(output)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
