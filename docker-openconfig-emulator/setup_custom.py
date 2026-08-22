import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect("localhost", port=30101, username="onos", password="rocks")
    channel = client.invoke_shell()
    time.sleep(1)
    
    commands = [
        "cfg set org.onosproject.provider.nil.NullProviders topoShape custom",
        "cfg set org.onosproject.provider.nil.NullProviders enabled true",
        "wipe-out please",
        "null-create-device ROADM null:roadm1 4",
        "null-create-device ROADM null:roadm2 4",
        "null-create-device ROADM null:roadm3 4",
        "null-create-link OPTICAL null:roadm1 null:roadm2",
        "null-create-link OPTICAL null:roadm2 null:roadm3"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(1.5)
        
    output = channel.recv(65535).decode("utf-8")
    print(output)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
