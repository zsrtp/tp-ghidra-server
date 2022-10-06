#!/usr/bin/env python

from time import time
import boto3
import time
import re
import yaml
import sys

ssm_client = boto3.client('ssm')
ec2_client = boto3.client('ec2')


def get_instance_id():
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
    svr_admin_list_cmd = f'/opt/ghidra/server/svrAdmin -list --users'
    return run_ssm_command(svr_admin_list_cmd)


def add_user(user):
    svr_admin_add_cmd = f'/opt/ghidra/server/svrAdmin -add {user}'
    run_ssm_command(svr_admin_add_cmd)


def set_permission(user, perm):
    svr_admin_grant_cmd = f'/opt/ghidra/server/svrAdmin -grant {user} {perm} tp'
    run_ssm_command(svr_admin_grant_cmd)


def remove_user(user):
    svr_admin_remove_cmd = f'/opt/ghidra/server/svrAdmin -remove {user}'
    run_ssm_command(svr_admin_remove_cmd)


def check_and_set_permission(user, perm):
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


if __name__ == "__main__":
    current_users = get_ghidra_users()

    with open("users.yaml", "r") as stream:
        try:
            user_entry_list = yaml.safe_load(stream)
            yaml_users = []

            for entry in user_entry_list:
                yaml_users.append(entry["ghidraName"])

            # Remove any users not in source control anymore
            for ghidra_user in current_users.keys():
                if ghidra_user not in yaml_users:
                    print(ghidra_user, "isn't in the source control list anymore. Removing...",end='')
                    remove_user(ghidra_user)
                    print("Done.")

            # Add or update any users in source control
            for i in range(len(user_entry_list)):
                curr_yaml_name = user_entry_list[i]["ghidraName"]
                curr_yaml_perm = (user_entry_list[i]["permissions"]).lower()

                if curr_yaml_name not in current_users.keys():
                    print("User", curr_yaml_name,
                          "doesn't exist. Creating...", end='')
                    add_user(curr_yaml_name)
                    print("Done.")

                    print("Setting permissions for", curr_yaml_name + "...", end='')
                    check_and_set_permission(curr_yaml_name, curr_yaml_perm)
                    print("Done.")

                elif current_users[curr_yaml_name] != curr_yaml_perm:
                    print("User", curr_yaml_name,
                          "permissions don't match. Updating...", end='')
                    check_and_set_permission(curr_yaml_name, curr_yaml_perm)
                    print("Done.")

                else:
                    print("User", curr_yaml_name, "is up-to-date.")

        except yaml.YAMLError as err:
            print(err)
