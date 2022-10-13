## TP Community Ghidra Server

Ghidra server automation for the TP Speedrun and Decomp communities.

## Adding New Users

To add a new user, open a pull request and update the users.yaml file with the new username and their permissions. The new user will be added upon merge into the main branch.

The password for the new user will be "changeme" and will expire after 24 hours. (We will probably update this process in the future)

## Overview

```
├── README.md        - This README
├── backend.tf       - Terraform backend information for managing state
├── ghidra-server.tf - Ghidra Terraform module
├── manage-users.py  - Python script for managing users
├── requirements.txt - Python dependencies
└── users.yaml       - Ghidra users and permissions
```