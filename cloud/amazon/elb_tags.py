#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
module: elb_tags
short_description: allows manipulation of ELB tags
description:
    - Module allows for adding and removing tags from ELBs
version_added: 2.1
author: "Fernando Jose Pando (@oldmanlinux)"
options:
  elb_name:
    description:
      - Name of the elb of which to modify tags
    required: true
    default: null
    aliases: []
  tags:
    description:
      - list of dictionaries of tags
    required: true
  state:
    description:
      - add or remove tags
    required: true
extends_documentation_fragment: aws
requirements: [ "boto3" ]
'''

EXAMPLES = '''
    # Adds elb tag
    elb_tag:
        elb_name: foo
        tags: "{{ list_of_dicts }}"
        state: present
'''

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def check_if_tags_exist(result):
    tags_new = [ values for tags in result['tags']
                        for values in tags.values() ]
    tags_existing = [ values for tags in result['existing']
                             for values in tags.values() ]
    return set(tags_new).issubset(set(tags_existing))

def create_or_update_elb_tags(client, module, result):
    if check_if_tags_exist(result):
        module.exit_json(**result)
    try:
        result['msg'] = client.add_tags(
            LoadBalancerNames = [ result['elb_name'] ],
            Tags = result['tags']
        )
        result['changed'] = True
    except botocore.exceptions.ClientError:
        result['msg'] = 'Failed to create/update elb tags due to error: ' + \
                        traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def delete_elb_tags(client, module, result):
    try:
        result['msg'] = client.remove_tags(
            LoadBalancerNames = [ result['elb_name'] ],
            Tags = result['tags']
        )
        result['changed'] = True
    except botocore.exceptions.ClientError:
        result['msg'] = 'Failed to create/update elb tags due to error: ' + \
                        traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state = dict(default='present', choices=['present', 'absent']),
        elb_name = dict(type="str", required = True),
        tags = dict(type="list")
    ))

    module = AnsibleModule(
        argument_spec = argument_spec,
        supports_check_mode = True
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    client = boto3.client('elb')
    state = module.params.get('state')
    result = dict(
        elb_name = module.params.get('elb_name'),
        tags = sorted(module.params.get('tags')),
        region = module.params.get('region'),
        changed = False
    )
    result['existing'] = sorted(client.describe_tags(
        LoadBalancerNames = [result['elb_name']])['TagDescriptions'][0]['Tags'])

    if state == 'present':
        create_or_update_elb_tags(client, module, result)
    elif state == 'absent':
        delete_elb_tags(client, module, result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
