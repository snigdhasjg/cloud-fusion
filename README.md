# aws fusion

> [!WARNING]
> This repository is archived. Development has moved to [cloud-fusion](https://github.com/snigdhasjg/cloud-fusion), published on PyPI as [cloud-fusion](https://pypi.org/project/cloud-fusion). Please migrate to the new project.

Unified CLI tool for streamlined AWS operations, enhancing developer productivity

[![Tag][tag-badge]][tag]
[![Publish][actions-workflow-publish-badge]][actions-workflow-publish]

## Installation
Install via pip install

```shell
pip install aws-fusion
```

## Command line tool
To invoke the cli, there are 2 option
1. Directly use `aws-fusion` command
2. Use it via [aws cli alias](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-alias.html) with `aws fusion`

## Usage

```commandline
usage: aws-fusion [<flags>] <command> ...

Unified CLI tool for streamlined AWS operations, enhancing developer productivity

Flags:
  -h, --help    show this help message and exit
  -v, --version Display the version of this tool
  --debug       Turn on debug logging

Command:
  init [<flags>]
    Initialize fusion app with creation of aws fusion alias.
  
  open-browser [<flags>] [<args>]
    Open a web browser for graphical access to the AWS Console.
    
    -p, --profile PROFILE The AWS profile to create the pre-signed URL with
    -r, --region REGION   The AWS Region to send the request to
        --no-logout       Skip logging out of the existing AWS console session before signing in (needed for AWS multi-session)
        --clip            Don't open the web browser, but copy the signin URL to clipboard
        --stdout          Don't open the web browser, but echo the signin URL to stdout
  
  iam-user-credentials [<flags>] <sub-command>
    IAM User credential helper.

  iam-user-credentials get [<flags>] [<args>]
    Retrieve IAM user credentials for AWS CLI profiles or application authentication.
        
        --access-key ACCESS_KEY AWS access key
        --account-id ACCOUNT_ID AWS Account ID for the name
        --username USERNAME     Username of a AWS user associated with the access key for the name
        --credential-process    Output the credential in AWS credential process syntax

  iam-user-credentials store [<flags>] [<args>]
    Store IAM user access key and secret key securely for streamlined authentication.
    
        --access-key ACCESS_KEY AWS access key
        --account-id ACCOUNT_ID AWS Account ID for the name
        --username USERNAME     Username of a AWS user associated with the access key for the name
        --secret-key SECRET_KEY AWS secret key
        
  okta [<flags>] <sub-command>
    Generate AWS session credentials from Okta.
    
  okta device-auth [<flags>] [<args>]
    Generate AWS session credentials using SAML assertion from Okta device authentication.

        --org-domain ORG_DOMAIN                   Full domain hostname of the Okta org e.g. example.okta.com
        --oidc-client-id OIDC_CLIENT_ID           The ID is the identifier of the client is Okta app acting as the IdP for AWS
        --aws-acct-fed-app-id AWS_ACCT_FED_APP_ID The ID for the AWS Account Federation integration app
        --aws-iam-role AWS_IAM_ROLE               The AWS IAM Role ARN to assume
        --credential-process                      Output the credential in AWS credential process syntax

  config-switch [<flags>] <sub-command>
    Switching between AWS config.
    
  config-switch profile [<flags>]
    Switch between available aws profile.
  
  config-switch region [<flags>]
    Switch between available aws region.
```

---
## Use case of `open-browser`
This only works with assume-role and federated-login, doesn't work with IAM user or user session.

#### IAM assume role
Profiles that use IAM roles pull credentials from another profile, and then apply IAM role permissions. 

In the following examples, `iam-user` is the source profile for credentials and `iam-assume-role` borrows the same credentials then assumes a new role.

**Credentials file**
```
[profile iam-user]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Config file**
```
[profile iam-user]
region = us-east-1
output = json

[profile iam-assume-role]
source_profile = iam-user
role_arn = arn:aws:iam::777788889999:role/user-role
role_session_name = my-session
region = ap-south-1
output = json
```

#### Federated login
Using IAM Identity Center, you can log in to Active Directory, a built-in IAM Identity Center directory, or another IdP connected to IAM Identity Center. You can map these credentials to an AWS Identity and Access Management (IAM) role for you to run AWS CLI commands.

In the following examples, using `aws-sso` profile assumes `sso-read-only-role` on `111122223333` account.

**Config file**
```
[profile aws-sso]
sso_session = my-sso-session
sso_account_id = 111122223333
sso_role_name = sso-read-only-role
role_session_name = my-session
region = us-east-1
output = json

[sso-session my-sso-session]
sso_region = us-east-2
sso_start_url = https://my-sso-portal.awsapps.com/start
sso_registration_scopes = sso:account:access
```

### Refer
The docs
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_enable-console-custom-url.html
- https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html

---
## Usa case of `iam-user-credentials store`
To store IAM user credential in the system credential store for best security rather than plain text `~/.aws/credentials` file.

Manually the save the credential in the store using
```bash
aws-fusion iam-user-credentials store \
    --access-key 'AKIAIOSFODNN7EXAMPLE' \
    --secret-key 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' \
    --account-id '123456789012' \
    --username 'my-iam-user'
```

---
## Use case of `iam-user-credentials get`
Configure aws config file to use credential process

**Config file**
```
[profile iam-user]
region = us-east-1
output = json
credential_process = aws-fusion iam-user-credentials get --account-id 123456789012 --username 'my-iam-user' --access-key 'AKIAIOSFODNN7EXAMPLE' --credential-process
```

### Refer
The docs
- https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html

---
## Use case of `okta device-auth`
Configure aws config file to use credential process

**Config file**
```
[profile iam-user]
region = us-east-1
output = json
credential_process = aws-fusion okta device-auth --org-domain my.okta.com --oidc-client-id 0pbs4fq1q2vbGoFkC1m7 --aws-acct-fed-app-id 0oa8z9xa8BS9b2AFb1t7 --aws-iam-role arn:aws:iam::123456789012:role/PowerUsers --credential-process
```

---
## Use case of `config-switch`
A special of utility script to help easily switch `profile` and `region`

### For Linux & Darwin (MacOS)
This works with 2 bash script, namely `_awsp` and `_awsr`

Post installing the app, create 2 aliases in `.bashrc` or `.zshrc` file.
```shell
## aws fusion setup
alias awsp="source _awsp"
alias awsr="source _awsr"
```

> _Using the command without the aliases will have no effect_

### For Windows
This works with 2 powershell script, namely `_awsp.ps1` and `_awsr.ps1`

Post installing the app, create 2 aliases in `$PROFILE` (i.e. `$HOME\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`) file.
```ps1
## aws fusion setup
Set-Alias awsp "_awsp.ps1"
Set-Alias awsr "_awsr.ps1"
```

<img src="https://raw.githubusercontent.com/snigdhasjg/aws-fusion/main/doc/images/config-switch.png" width="300" alt="config-switch-image"/>

---
## License
This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](./LICENSE) file for details.

<!-- badge links -->

[tag]: https://github.com/snigdhasjg/aws-fusion/tags
[tag-badge]: https://img.shields.io/github/v/tag/snigdhasjg/aws-fusion?style=for-the-badge&logo=github

[actions-workflow-publish]: https://github.com/snigdhasjg/aws-fusion/actions/workflows/publish.yml
[actions-workflow-publish-badge]: https://img.shields.io/github/actions/workflow/status/snigdhasjg/aws-fusion/publish.yml?branch=main&label=Publish&style=for-the-badge&logo=githubactions
