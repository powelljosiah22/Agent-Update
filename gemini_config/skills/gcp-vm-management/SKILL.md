---
name: gcp-vm-management
description: Guidelines and commands for managing, editing, and SSHing into Google Cloud VMs.
---
# GCP VM Management

Use this skill when the user asks you to update, edit, or configure a Google Cloud Virtual Machine.

## 1. Authentication & Sandbox Constraints
**CRITICAL RULE:** You **must** run all `gcloud compute` commands with `BypassSandbox: true` via the `run_command` tool. The standard sandbox prevents access to `~/.config/gcloud/credentials.db`, causing `gcloud` commands to fail. 
- You will need to ask the user for permission to bypass the sandbox.

## 2. Standard Workflow
1. **Identify the VM:** 
   Run `gcloud compute instances list` (with the project flag if known) to find the target VM Name and Zone.
2. **Execute Remote Commands:**
   Use SSH to run quick configuration commands (like checking logs or updating crontab):
   `gcloud compute ssh [VM_NAME] --zone=[ZONE] --command="[COMMAND]"`
3. **Deploying Code/Scripts:**
   Do not try to use `cat` or `echo` to write long multi-line python scripts over SSH. Instead:
   - Write the script to the local machine first using `write_to_file` (e.g. to a temporary workspace or `scratch/`).
   - Use SCP to securely copy the file to the VM:
     `gcloud compute scp /local/path [VM_NAME]:~/remote_path --zone=[ZONE]`

## 3. Common Operations
- **Updating Cron:**
  To safely update a crontab on a VM without wiping it out:
  `gcloud compute ssh [VM_NAME] --zone=[ZONE] --command="(crontab -l 2>/dev/null | grep -v 'old_script.py'; echo '30 9 * * * python3 ~/new_script.py') | crontab -"`
