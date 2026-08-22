import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect("localhost", port=30101, username="onos", password="rocks")
    channel = client.invoke_shell()
    time.sleep(1)
    
    commands = [
        "wipe-out please",
        "null-create-device ROADM null:0000000000000001 4",
        "null-create-device ROADM null:0000000000000002 4",
        "ports | grep null"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(2)
        
    output = channel.recv(65535).decode("utf-8")
    print(output)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
