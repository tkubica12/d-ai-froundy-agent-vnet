# Jump Host Module

Provisions an Ubuntu 24.04 Linux VM as a jump host with Azure Bastion Standard SKU for secure SSH access without public IPs.

## Features

- **Azure Bastion Standard SKU**: Enables native SSH client support and tunneling for VS Code Remote SSH
- **Ubuntu 24.04 LTS**: Modern Linux environment with pre-installed developer tools
- **Azure AD Authentication**: SSH access using Azure AD credentials with MFA support
- **System Managed Identity**: Secure access to Azure resources without credentials
- **Pre-configured Tools**: Azure CLI, Terraform, Git, jq pre-installed via cloud-init

## VS Code Remote SSH Setup

### Prerequisites

1. Install the [Remote - SSH extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) in VS Code
2. Install Azure CLI on your local machine: `az cli install`
3. Add the Azure CLI SSH extension: `az extension add --name ssh`

### Method 1: Direct SSH via Bastion (Simple)

1. Get the SSH command from Terraform output:
   ```bash
   terraform output ssh_command
   ```

2. Run the command to connect:
   ```bash
   az network bastion ssh --name bastion-<name> --resource-group <rg> --target-resource-id <vm-id> --auth-type AAD
   ```

3. Authenticate with your Azure AD credentials when prompted

### Method 2: VS Code Remote SSH with ProxyCommand (Recommended)

This method allows VS Code to connect through Azure Bastion using SSH config.

1. Get your VM details from Terraform outputs:
   ```bash
   terraform output jump_host_name
   terraform output jump_host_id
   terraform output bastion_host_name
   ```

2. Edit your SSH config file (`~/.ssh/config` on Linux/Mac or `%USERPROFILE%\.ssh\config` on Windows):

   ```ssh
   Host azure-jump
       HostName <jump-private-ip>
       User <admin-username>
       StrictHostKeyChecking no
       UserKnownHostsFile /dev/null
       ProxyCommand az network bastion ssh --name <bastion-name> --resource-group <rg> --target-resource-id <vm-id> --auth-type AAD -- -W %h:%p
   ```

   **Note**: The `-- -W %h:%p` at the end is critical for ProxyCommand to work correctly.

3. In VS Code:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Remote-SSH: Connect to Host..."
   - Select `azure-jump`
   - VS Code will authenticate via Azure AD and establish the connection

### Method 3: SSH Tunnel for Port Forwarding

Create a tunnel to access services running on the jump host:

```bash
az network bastion tunnel \
  --name <bastion-name> \
  --resource-group <rg> \
  --target-resource-id <vm-id> \
  --resource-port 22 \
  --port 2222
```

Then connect via localhost:
```bash
ssh -p 2222 <admin-username>@localhost
```

## RBAC Requirements

To connect via Azure Bastion with Azure AD authentication, you need one of these roles on the VM:

- **Virtual Machine Administrator Login**: Full admin access (sudo privileges)
- **Virtual Machine User Login**: Standard user access

Assign the role via Terraform or Azure CLI:

```bash
az role assignment create \
  --assignee <user-or-group-object-id> \
  --role "Virtual Machine Administrator Login" \
  --scope <vm-id>
```

## Troubleshooting

### SSH Connection Fails

1. Verify you're logged into Azure CLI: `az login`
2. Check you have the SSH extension: `az extension list | grep ssh`
3. Verify RBAC role assignment on the VM
4. Ensure NSG allows SSH from VirtualNetwork source

### VS Code Remote SSH Issues

1. Check SSH config syntax (especially the `-- -W %h:%p` part)
2. Ensure Azure CLI is in your PATH
3. Try connecting via terminal first to verify authentication works
4. Check VS Code Remote SSH logs: `View > Output > Remote - SSH`

### AAD Extension Not Working

The AADSSHLoginForLinux extension should install automatically. If issues occur:

```bash
az vm extension set \
  --publisher Microsoft.Azure.ActiveDirectory \
  --name AADSSHLoginForLinux \
  --resource-group <rg> \
  --vm-name <vm-name>
```

## Architecture

```
Developer Workstation (VS Code)
         |
         | Azure CLI + SSH Extension
         v
Azure Bastion (Standard SKU)
         |
         | Private SSH (port 22)
         v
Jump Host (Ubuntu 24.04)
    - Azure AD Auth
    - System Managed Identity
    - Developer Tools
```

## Security Features

- No public IP address on the VM
- SSH access only through Azure Bastion
- Azure AD authentication with MFA support
- Network Security Group restricting inbound to SSH from VirtualNetwork
- AllowTcpForwarding enabled for VS Code Remote SSH
- System Managed Identity for secure Azure resource access

## Pre-installed Tools

- Azure CLI
- Terraform
- Git
- jq
- curl
- unzip

Additional tools can be installed via standard apt package manager.

## References

- [Azure Bastion Documentation](https://learn.microsoft.com/azure/bastion/)
- [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh)
- [Azure AD Login for Linux VMs](https://learn.microsoft.com/azure/active-directory/devices/howto-vm-sign-in-azure-ad-linux)
- [Azure Bastion Native Client Support](https://learn.microsoft.com/azure/bastion/connect-vm-native-client-windows)
