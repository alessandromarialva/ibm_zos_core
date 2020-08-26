#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) IBM Corporation 2019, 2020
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: zos_mqsc_operator
short_description: Execute MQSC commands
description:
    - Execute MQSC command and receive the output. Usage \\<CPF> <MQSC_COMMAND>
author: "Ping Xiao (@xiaopingBJ) & Alessandro R Marialva (@alessandromarialva)"
options:
  cmd:
    description:
      - The MQSC command to execute.
    type: str
    required: true
  verbose:
    description:
      - Return verbose information.
    type: bool
    required: false
    default: false
  debug:
    description:
      - Return debugging information.
    type: bool
    required: false
    default: false
"""

EXAMPLES = r"""
- name: Execute a MQSC command to display MQ Queue Manager details
  zos_mqsc_operator:
    cmd: '\\<CPF> DISPLAY QMGR'

- name: Execute a MQSC command to display MQ Queue Manager details with verbose information
  zos_mqsc_operator:
    cmd: '\\<CPF> DISPLAY QMGR'
    verbose: true

- name: Execute a MQSC command to display MQ Queue Manager details with verbose and debug information
  zos_mqsc_operator:
    cmd: '\\<CPF> DISPLAY QMGR'
    verbose: true
    debug: true

- name: Execute an operator command to purge all job logs (requires escaping)
  zos_mqsc_operator:
    cmd: "\\<CPF> DEFINE QLOCAL(ANSB.TEST.ZOS) DESCR('Local_queue_for_Ansible_tests')"

"""

RETURN = r"""
rc:
    description:
       Return code of the MQSC command
    returned: on success
    type: int
    sample: 0
content:
    description:
       The response resulting from the execution of the MQSC command
    returned: on success
    type: list
    sample:
        [ "E4E4      2020238  23:37:37.00             ISF031I CONSOLE BR20396 ACTIVATED",
          "E4E4      2020238  23:37:37.00            -##EE4Q DEFINE QLOCAL(ANSB.TEST.ZOS) DESCR(LOCAL_QUEUE_FOR_ANSIBLE_TESTS)",
          "E4E4      2020238  23:37:37.00  STC18668   CSQ9022I ##EE4Q CSQMAQLC ' DEFINE QLOCAL' NORMAL COMPLETION",
          ""
        ]
changed:
    description:
       Indicates if any changes were made during module operation.
       Given MQSC commands may introduce changes that are unknown to the
       module. True is always returned unless either a module or
       command failure has occurred.
    returned: always
    type: bool
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ibm_zos_core.plugins.module_utils.ansible_module import (
    AnsibleModuleHelper,
)
from ansible.module_utils.six import PY3


from ansible_collections.ibm.ibm_zos_core.plugins.module_utils.better_arg_parser import (
    BetterArgParser,
)

if PY3:
    from shlex import quote
else:
    from pipes import quote


def run_module():
    module_args = dict(
        cmd=dict(type="str", required=True),
        verbose=dict(type="bool", default=False),
        debug=dict(type="bool", default=False),
    )

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        new_params = parse_params(module.params)
        rc_message = run_operator_command(new_params)
        result["rc"] = rc_message.get("rc")
        result["content"] = rc_message.get("message").split("\n")
    except Error as e:
        module.fail_json(msg=repr(e), **result)
    except Exception as e:
        module.fail_json(
            msg="An unexpected error occurred: {0}".format(repr(e)), **result
        )
    result["changed"] = True
    module.exit_json(**result)


def parse_params(params):
    arg_defs = dict(
        cmd=dict(arg_type="str", required=True),
        verbose=dict(arg_type="bool", required=False),
        debug=dict(arg_type="bool", required=False),
    )
    parser = BetterArgParser(arg_defs)
    new_params = parser.parse_args(params)
    return new_params


def run_operator_command(params):
    module = AnsibleModuleHelper(argument_spec={})
    command = params.get("cmd")
    verbose = "-v" if params.get("verbose") else ""
    debug = "-d" if params.get("debug") else ""
    rc, stdout, stderr = module.run_command(
        "opercmd {0} {1} {2}".format(verbose, debug, command),
    )
    message = stdout + stderr
    if rc > 0:
        raise OperatorCmdError(command, rc, message.split("\n") if message else message)
    return {"rc": rc, "message": message}


class Error(Exception):
    pass


class OperatorCmdError(Error):
    def __init__(self, cmd, rc, message):
        self.msg = 'An error occurred executing the operator command "{0}", with RC={1} and response "{2}"'.format(
            cmd, str(rc), message
        )


def main():
    run_module()


if __name__ == "__main__":
    main()
