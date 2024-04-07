#!/usr/bin/env python

from time import time
import boto3
import time
import re
import yaml
import sys
import click

ssm_client = boto3.client('ssm')
ec2_client = boto3.client('ec2')

def get_instance_id():
    """
    Returns the EC2 instance ID of the Ghidra server.
    """

    response = ec2_client.describe_instances(Filters=[
        {
            'Name': 'tag:Name',
            'Values': ['ghidra-*']
        },
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ])

    return response["Reservations"][0]["Instances"][0]["InstanceId"]

def run_ssm_command(cmd):
    """
    Runs an arbitrary command on the Ghidra server using SSM.

    Keyword arguments:
    cmd - The command to run on the Ghidra server.
    """

    instance_id = get_instance_id()
    run_commands = ["source /etc/profile", cmd]

    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': run_commands}
    )
    command_id = response['Command']['CommandId']
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id,
    )
    return output["StandardOutputContent"]

def list_users():
    """
    Lists all users on the Ghidra server.
    """

    svr_admin_list_cmd = f'/opt/ghidra/server/svrAdmin -list --users'
    return run_ssm_command(svr_admin_list_cmd)

def add_user(user):
    """
    Adds a user to the Ghidra server.

    Keyword arguments:
    user - The user to add to the Ghidra server.
    """

    svr_admin_add_cmd = f'/opt/ghidra/server/svrAdmin -add {user}'
    run_ssm_command(svr_admin_add_cmd)

def set_permission(user, perm):
    """
    Sets a permission for a user on the Ghidra server.

    Keyword arguments:
    user - The user to set permissions for.
    perm - The permission to set for the user. Should be one of: read-only, write, admin.
    """

    svr_admin_grant_cmd = f'/opt/ghidra/server/svrAdmin -grant {user} {perm} tp'
    run_ssm_command(svr_admin_grant_cmd)

def remove_user(user):
    """
    Removes a user from the Ghidra server.

    Keyword arguments:
    user - The user to remove from the Ghidra server.
    """

    svr_admin_remove_cmd = f'/opt/ghidra/server/svrAdmin -remove {user}'
    run_ssm_command(svr_admin_remove_cmd)

def check_and_set_permission(user, perm):
    """
    Checks if the supplied permission is valid and sets it for the user.

    Keyword arguments:
    user - The user to check and set permissions for.
    perm - The permission to set for the user. Should be one of: read-only, write, admin.
    """
    match perm:
        case "admin":
            set_permission(user, "+a")
        case "write":
            set_permission(user, "+w")
        case "read-only":
            set_permission(user, "+r")
        case _:
            print("User", user, "has invalid permissions. Should be one of: read-only, write, admin", file=sys.stderr)
            raise SystemExit(1)

def get_ghidra_users():
    """
    Returns a dictionary of all users on the Ghidra server and their permissions.
    """

    std_output = list_users()
    regex = r"tp"

    regex_search_result = re.search(regex, std_output)
    regex_search_result_stripped = std_output[regex_search_result.end(
    ):].strip()
    raw_user_list = regex_search_result_stripped.replace(
        '\n', '').replace(' ', ',').split(",")
    filtered_user_list = list(filter(None, (raw_user_list)))

    current_users = {}

    for i in range(1, len(filtered_user_list), 2):
        curr_user = {filtered_user_list[i-1]: filtered_user_list[i].replace("(","").replace(")","")}
        current_users.update(curr_user)

    return current_users

def remove_ghidra_users(current_users,yaml_users,dry_run):
    """
    Removes any users that are no longer in the source control list.

    Keyword arguments:
    current_users - The current users on the Ghidra server.
    yaml_users - The users in the source control list.
    dry_run - If set, the script will run in dry-run mode and no action will be taken.

    Returns:
    ret_users - The number of users that will be removed.
    """

    ret_users = 0

    users_to_remove = [ghidra_user for ghidra_user in current_users.keys() if ghidra_user not in yaml_users]

    # Remove any users that are no longer in the source control list
    for ghidra_user in users_to_remove:
        print(ghidra_user, "isn't in the source control list anymore. Removing...",end='')

        if not dry_run:
            # remove_user(ghidra_user)
            print("Done.")
        else:
            print("Dry run mode. Skipping.")
            ret_users += 1

    return ret_users

def update_ghidra_users(current_users,yaml_users,dry_run):
    """
    Updates any users that have had their permissions changed in the source control list.

    Keyword arguments:
    current_users - Dict of the current users and their permission on the Ghidra server.
    yaml_users - Dict of the users and their permissions in the source control list.
    dry_run - If set, the script will run in dry-run mode and no action will be taken.

    Returns:
    ret_users - The number of users that will be updated.
    """

    ret_users = 0

    for i in range(len(yaml_users)):
        curr_yaml_name = yaml_users[i]["ghidraName"]
        curr_yaml_perm = (yaml_users[i]["permissions"]).lower()

        # Check if any user permissions need to be updated
        if current_users[curr_yaml_name] != curr_yaml_perm:
            print("User", curr_yaml_name, "permissions don't match. Updating...", end='')
            if not dry_run:
                # check_and_set_permission(curr_yaml_name, curr_yaml_perm)
                print("Done.")
            else:
                print("Dry run mode. Skipping.")
                ret_users += 1

        else:
            print("User", curr_yaml_name, "is up-to-date.")

    return ret_users

def add_ghidra_users(current_users,yaml_users,dry_run):
    """
    Adds any users that are in the source control list but not on the Ghidra server.

    Keyword arguments:
    current_users - Dict of the current users and their permission on the Ghidra server.
    yaml_users - Dict of the users and their permissions in the source control list.
    dry_run - If set, the script will run in dry-run mode and no action will be taken.

    Returns:
    ret_users - The number of users and their permissions that will be added.
    """

    # dict to track num users to add and their permissions
    ret_users = {
        "num_users": 0,
        "permissions": []
    }

    # list comprehension to grab the user:permission pairs that appear in yaml_users but not in current_users
    users_to_add = [ghidra_user for ghidra_user in yaml_users if ghidra_user["ghidraName"] not in current_users.keys()]

    for ghidra_user in users_to_add:
        print("User", ghidra_user["ghidraName"],
                "doesn't exist. Creating...", end='')
        if not dry_run:
            # add_user(ghidra_user["ghidraName"])
            print("Done.")
        else:
            print("Dry run mode. Skipping.")
            ret_users["num_users"] += 1

        print("Setting permissions for", ghidra_user["ghidraName"] + "...", end='')

        if not dry_run:
            # check_and_set_permission(ghidra_user["ghidraName"], ghidra_user["permissions"])
            print("Done.")
        else:
            print("Dry run mode. Skipping.")
            ret_users["permissions"].append(ghidra_user["permissions"])
    
    return ret_users

@click.command()
@click.option('--dry-run', is_flag=True, help='Dry run mode.')
def manage_users(dry_run=False):
    """
    Manages users on the Ghidra server.

    Keyword arguments:
    dry_run - If set, the script will run in dry-run mode and no action will be taken.
    """

    ghidra_server_users = get_ghidra_users()

    with open("users.yaml", "r") as stream:
        try:
            source_control_users = yaml.safe_load(stream)

            rm_users = remove_ghidra_users(ghidra_server_users,source_control_users,dry_run)
            update_users = update_ghidra_users(ghidra_server_users,source_control_users,dry_run)
            add_users = add_ghidra_users(ghidra_server_users,source_control_users,dry_run)

            if dry_run:
                if rm_users > 0 or update_users > 0:
                    sys.exit(1)
                elif add_users > 0:
                    for permission in add_users["permissions"]:
                        if permission in ["write", "admin"]:
                            sys.exit(1)
                sys.exit(0)

        except yaml.YAMLError as err:
            print(err)

if __name__ == "__main__":
    manage_users()