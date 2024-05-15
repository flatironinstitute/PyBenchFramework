import paramiko

def execute_ssh_command(hostname, username, command):
    # Create SSH client
    ssh_client = paramiko.SSHClient()

    # Automatically add host keys
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the SSH server
        ssh_client.connect(hostname, username=username)

        # Execute the command
        stdin, stdout, stderr = ssh_client.exec_command(command)

        # Read the output
        output = stdout.read().decode().strip()

        # Print output
        #print("Output of the command:")
        #print(output)

    except paramiko.AuthenticationException:
        print("Authentication failed.")
    except paramiko.SSHException as e:
        print("SSH error:", e)
    finally:
        # Close the SSH connection
        ssh_client.close()
    
    return output