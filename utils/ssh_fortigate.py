
import paramiko
import re

def fetch_firmware_from_fortigate(ip, username, password):
    """
    Connects to FortiGate via SSH and retrieves firmware version using 'get system status'.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname=ip, username=username, password=password, timeout=10)
        stdin, stdout, stderr = client.exec_command("get system status")
        output = stdout.read().decode()
        client.close()

        match = re.search(r"Version:\s+(.+)", output)
        if match:
            return match.group(1).strip()
        else:
            return "Unknown"
    except Exception as e:
        return f"Error: {e}"
