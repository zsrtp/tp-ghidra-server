# THIS SERVER HAS BEEN MOVED

Please read carefully. This server has been moved to `ghidra.decomp.dev`.

- If you **already** have an account on both `ghidra.decomp.dev` and `ghidra.tpgz.io` - sign in with your `ghidra.decomp.dev` username and password. Your permissions to the project will remain the same.
- If you **only** have an account on `ghidra.tpgz.io` - please sign in using your `ghidra.tpgz.io` credentials to the new server. The easiest way to do this is to add a new shared project:
  1. File
  2. New Project...
  3. Shared Project
  4. Server Name: `ghidra.decomp.dev`, Port Number: `13100`
  5. Select TwilightPrincess
- If you **don't** have an account on either server **or** if you've forgotten your login credentials - send a DM to `encounter` on Discord and request an account / credential reset for the TwilightPrincess repo.

## TP Community Ghidra Server

Ghidra server automation for the TP Speedrun and Decomp communities.

## Adding New Users

To add a new user, open a pull request and update the users.yaml file with the new username and their permissions. The new user will be added upon merge into the main branch.

The password for the new user will be "changeme" and will expire after 24 hours. (We will probably update this process in the future)

## Server Info

Please use this information for first logins to the server:

```
hostname:  ghidra.tpgz.io
port:      13100
username:  <your_username>
password:  changeme
```

## Overview

```
├── README.md        - This README
├── backend.tf       - Terraform backend information for managing state
├── ghidra-server.tf - Ghidra Terraform module
├── manage-users.py  - Python script for managing users
├── requirements.txt - Python dependencies
└── users.yaml       - Ghidra users and permissions
```
