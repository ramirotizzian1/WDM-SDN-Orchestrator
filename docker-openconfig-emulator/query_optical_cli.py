import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect("localhost", port=30101, username="onos", password="rocks")
    stdin, stdout, stderr = client.exec_command("help")
    out = stdout.read().decode()
    for line in out.split('\n'):
        if 'optical' in line.lower() or 'intent' in line.lower():
            print(line)
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
