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
        "cfg set org.onosproject.provider.nil.NullProviders enabled true"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(1)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
