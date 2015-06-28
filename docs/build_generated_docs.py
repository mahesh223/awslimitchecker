"""
awslimitchecker docs/build_generated_docs.py

Builds documentation that is generated dynamically from awslimitchecker.

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of awslimitchecker, also known as awslimitchecker.

    awslimitchecker is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    awslimitchecker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with awslimitchecker.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import json
import logging
import os
import sys
import subprocess
from textwrap import dedent

my_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PYTHONPATH'] = os.path.join(my_dir, '..')
sys.path.insert(0, os.path.join(my_dir, '..'))

from awslimitchecker.checker import AwsLimitChecker

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

def build_iam_policy(checker):
    logger.info("Beginning build of iam_policy.rst")
    # get the policy dict
    logger.info("Getting IAM Policy")
    policy = checker.get_required_iam_policy()
    # serialize as pretty-printed JSON
    policy_json = json.dumps(policy, sort_keys=True, indent=2)
    # indent each line by 4 spaces
    policy_str = ''
    for line in policy_json.split("\n"):
        policy_str += (' ' * 4) + line + "\n"
    doc = """
    .. -- WARNING -- WARNING -- WARNING
       This document is automatically generated by
       awslimitchecker/docs/build_generated_docs.py.
       Please edit that script, or the template it points to.

    .. _iam_policy:

    Required IAM Permissions
    ========================

    Below is the sample IAM policy from this version of awslimitchecker, listing the IAM
    permissions required for it to function correctly:

    .. code-block:: json

    {policy_str}
    """
    doc = dedent(doc)
    doc = doc.format(policy_str=policy_str)
    fname = os.path.join(my_dir, 'source', 'iam_policy.rst')
    logger.info("Writing {f}".format(f=fname))
    with open(fname, 'w') as fh:
        fh.write(doc)

def build_limits(checker):
    logger.info("Beginning build of limits.rst")
    ta_limits = {}
    logger.info("Getting Limits")
    limit_info = ''
    limits = checker.get_limits()
    # this is a bit of a pain, because we need to know string lengths to build the table
    for svc_name in sorted(limits):
        ta_limits[svc_name] = []
        limit_info += svc_name + "\n"
        limit_info += ('+' * (len(svc_name)+1)) + "\n"
        limit_info += "\n"
        # build a dict of the limits
        slimits = {}
        # track the maximum string lengths
        max_name = 0
        max_default_limit = 0
        for limit in limits[svc_name].values():
            lname = limit.name
            if limit.ta_limit is not None:
                lname += ' :sup:`(TA)`'
                ta_limits[svc_name].append(limit.name)
            slimits[lname] = str(limit.default_limit)
            # update max string length for table formatting
            if len(lname) > max_name:
                max_name = len(lname)
            if len(str(limit.default_limit)) > max_default_limit:
                max_default_limit = len(str(limit.default_limit))
        # create the format string
        sformat = '{name: <' + str(max_name) + '} ' \
                  '{limit: <' + str(max_default_limit) + '}\n'
        # separator lines
        sep = ('=' * max_name) + ' ' + ('=' * max_default_limit) + "\n"
        # header
        limit_info += sep
        limit_info += sformat.format(name='Limit', limit='Default')
        limit_info += sep
        # limit lines
        for lname, limit in sorted(slimits.iteritems()):
            limit_info += sformat.format(name=lname, limit=limit)
        # footer
        limit_info += sep

    # TA limit list
    ta_info = """
    So long as the Service and Limit names used by Trusted Advisor (and returned
    in its API responses) exactly match those shown below, all limits listed in
    Trusted Advisor "Service Limit" checks should be automatically used by
    awslimitchecker. The following service limits have been confirmed as being
    updated from Trusted Advisor:
    """
    ta_info = dedent(ta_info) + "\n\n"
    for sname in sorted(ta_limits.keys()):
        if len(ta_limits[sname]) < 1:
            continue
        ta_info += '* {s}\n\n'.format(s=sname)
        for lname in sorted(ta_limits[sname]):
            ta_info += '  * {l}\n\n'.format(l=lname)

    doc = """
    .. -- WARNING -- WARNING -- WARNING
       This document is automatically generated by
       awslimitchecker/docs/build_generated_docs.py.
       Please edit that script, or the template it points to.

    .. _limits:

    Supported Limits
    ================

    .. _limits.trusted_advisor:

    Trusted Advisor Data
    ---------------------

    {ta_info}

    .. _limits.checks:

    Current Checks
    ---------------

    The section below lists every limit that this version of awslimitchecker knows
    how to check, and its hard-coded default value (per AWS documentation). Limits
    marked with :sup:`(TA)` are comfirmed as being updated by Trusted Advisor.

    {limit_info}

    """
    doc = dedent(doc)
    doc = doc.format(ta_info=ta_info, limit_info=limit_info)
    fname = os.path.join(my_dir, 'source', 'limits.rst')
    logger.info("Writing {f}".format(f=fname))
    with open(fname, 'w') as fh:
        fh.write(doc)

def build_runner_examples():
    logger.info("Beginning build of runner examples")
    # read in the template file
    with open(os.path.join(my_dir, 'source', 'cli_usage.rst.template'), 'r') as fh:
        tmpl = fh.read()
    # examples to run
    examples = {
        'help': ['awslimitchecker', '--help'],
        'list_limits': ['awslimitchecker', '-l'],
        'list_defaults': ['awslimitchecker', '--list-defaults'],
        'skip_ta': ['awslimitchecker', '-l', '--skip-ta'],
        'show_usage': ['awslimitchecker', '-u'],
        'list_services': ['awslimitchecker', '-s'],
        'limit_overrides': [
            'awslimitchecker',
            '-L',
            '"EC2/EC2-Classic Elastic IPs"=100',
            '--limit="EC2/EC2-VPC Elastic IPs"=200',
            '-l',
        ],
        'check_thresholds': ['awslimitchecker', '--no-color'],
        'check_thresholds_custom': ['awslimitchecker', '-W', '97',
                                    '--critical=98', '--no-color'],
        'iam_policy': ['awslimitchecker', '--iam-policy'],
    }
    results = {}
    logger.info("Activating venv...")
    activate_path = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'activate_this.py')
    # run the commands
    for name, command in examples.items():
        cmd_str = ' '.join(command)
        logger.info("Running: {s}".format(s=cmd_str))
        try:
            output = subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            output = e.output
        results[name] = format_cmd_output(cmd_str, output, name)
    tmpl = tmpl.format(**results)

    # write out the final .rst
    with open(os.path.join(my_dir, 'source', 'cli_usage.rst'), 'w') as fh:
        fh.write(tmpl)
    logger.critical("WARNING - some output may need to be fixed to provide good examples")

def format_cmd_output(cmd, output, name):
    """format command output for docs"""
    formatted = '.. code-block:: console\n\n'
    formatted += '   (venv)$ {c}\n'.format(c=cmd)
    lines = output.split("\n")
    if name != 'help':
        for idx, line in enumerate(lines):
            if len(line) > 100:
                lines[idx] = line[:100] + ' (...)'
        if len(lines) > 12:
            lines = lines[:5] + ['(...)'] + lines[-5:]
    for line in lines:
        if line.strip() == '':
            continue
        formatted += '   ' + line + "\n"
    formatted += '\n'
    return formatted

def build_docs():
    """
    Trigger rebuild of all documentation that is dynamically generated
    from awslimitchecker.
    """
    if os.environ.get('CI', None) is not None:
        print("Not building dynamic docs in CI environment")
        raise SystemExit(0)
    logger.info("Beginning build of dynamically-generated docs")
    logger.info("Instantiating AwsLimitChecker")
    c = AwsLimitChecker()
    build_iam_policy(c)
    build_limits(c)
    build_runner_examples()

if __name__ == "__main__":
    build_docs()
