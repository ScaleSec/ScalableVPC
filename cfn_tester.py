#!/usr/bin/env python

'''
This script tests a cloudformation template by attempting launches
with all possible combinations of parameters provided by a user.
'''

import boto3
import sys
import time
import json
from datetime import datetime

# variables
region='us-east-1'
vpc_limit=5

# connect to AWS region
session = boto3.session.Session(
	region_name=region
)

# create an EC2 connection
ec2 = boto3.client('ec2')

# count VPCs in this region
vpcs = ec2.describe_vpcs()

# how many VPCs exist?
VPCS=[]
for vpc in vpcs['Vpcs']:
	VPCS.append(vpc['VpcId'])
vpc_count=len(VPCS)

# this is how many VPCs we can add
vpc_max = vpc_limit - vpc_count

# stop if we can't proceed
if vpc_max < 1:
	print "Too many VPCs in this region."
	sys.exit(0)

# injest the template to test

template_file = open('ScalableVPC2.yml')

cfn_template_body = template_file.read()
template_file.close()

# create a cloudformation connection
cloudformation = boto3.client('cloudformation')

'''
We have a variable grid of subnets, from 1x1 to 3x3.
We'll use a matrix of lettered AZs and numbered tiers
to identify tests:

| tier 0 | a0 | b0 | c0 |
| tier 1 | a1 | b1 | c1 |
| tier 2 | a2 | b2 | c2 |
         |AZ-a|AZ-b|AZ-c|

For each test we'll add a parameter value.
'''
def build_params (a0,b0,c0,a1,b1,c1,a2,b2,c2):
	global parameters # this sucks
	parameters = json.dumps([
	    {
	      "ParameterKey": "PubSubAz1Cidr",
	      "ParameterValue": a0
	    },
	    {
	      "ParameterKey": "PubSubAz2Cidr",
	      "ParameterValue": b0
	    },
	    {
	      "ParameterKey": "PubSubAz3Cidr",
	      "ParameterValue": c0
	    },
	    {
	      "ParameterKey": "PrivSubTier1Az1Cidr",
	      "ParameterValue": a1
	    },
	    {
	      "ParameterKey": "PrivSubTier1Az2Cidr",
	      "ParameterValue": b1
	    },
	    {
	      "ParameterKey": "PrivSubTier1Az3Cidr",
	      "ParameterValue": c1
	    },
	    {
	      "ParameterKey": "PrivSubTier2Az1Cidr",
	      "ParameterValue": a2
	    },
	    {
	      "ParameterKey": "PrivSubTier2Az2Cidr",
	      "ParameterValue": b2
	    },
	    {
	      "ParameterKey": "PrivSubTier2Az3Cidr",
	      "ParameterValue": c2
	    }
	  ])
	return parameters

def create_stack(stack_name,cfn_template_body,parameters):
	try:
		response = cloudformation.create_stack(
			StackName=stack_name,
			TemplateBody=cfn_template_body,
			Parameters=json.loads(parameters),
			Capabilities=[
				'CAPABILITY_NAMED_IAM',
			],
			DisableRollback=False

		)
	except Exception, e:
		print "Error: \"%s\"" % (str(e))
		pass

def does_stack_exist (stack_name):
	global stack_exists # this sucks
	try:
		response = cloudformation.describe_stacks(
			StackName=stack_name
		)
	except:
		print "Stack %s not found." % (stack_name)
		stack_exists = False
		pass
	else:
		stack_exists = True
		for stack in response['Stacks']:
			print "Stack found with name \"%s\" with status: %s" % (stack_name,stack['StackStatus'])

def wait_on_stack_operation (stack_name,desired_stack_states):
	if does_stack_exist (stack_name) == None:
		try:
			response = cloudformation.describe_stacks(
				StackName=stack_name
			)
		except Exception, e:
			print "Error: \"%s\"" % (str(e))
			pass
		else:
			print "Waiting for %s phase to complete." % (desired_stack_states)
			while True:
					response = cloudformation.describe_stacks(
						StackName=stack_name
					)
					for stack in response['Stacks']:
						stack_status = stack['StackStatus']
					for desired_stack_state in desired_stack_states:
						if stack_status == desired_stack_state:
							break
						#print "Waiting for stack operation... %s" % (stack_status)
						time.sleep(15)
					return response

class DateTimeEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, datetime):
			return o.isoformat()

			return json.JSONEncoder.default(self, o)

def record_stack_resources (stack_name):
	try:
		response = cloudformation.list_stack_resources(
			StackName=stack_name
		)
		stack_resources = json.dumps(response['StackResourceSummaries'], cls=DateTimeEncoder, indent=2)
		print stack_resources
	except Exception, e:
		print "Error: \"%s\"" % (str(e))
		pass

def delete_stack(stack_name):
	response = cloudformation.delete_stack(
		StackName=stack_name
	)
	return

def test_procedure (test_number,parameters):
	print "\n*** STARTING TEST %s ***" % (test_number)
	stack_name = "cfn-unit-test-%s" % (test_number)

	# make sure a stack with this name doesn't already exist
	does_stack_exist(stack_name)

	if stack_exists == False:
		create_stack(stack_name,cfn_template_body,parameters)
		wait_on_stack_operation(stack_name,'CREATE_COMPLETE')
		record_stack_resources(stack_name)
		delete_stack(stack_name)
		wait_on_stack_operation(stack_name,'DELETE_IN_PROGRESS')
	else:
		record_stack_resources(stack_name)
		delete_stack(stack_name)
		wait_on_stack_operation(stack_name,'DELETE_IN_PROGRESS')

	print "*** ENDING TEST %s ***\n" % (test_number)


def main():

	test_number=0
	build_params(
		'',
		'',
		'',
		'',
		'',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=1
	build_params(
		'10.0.32.0/20',
		'',
		'',
		'',
		'',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=2
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'',
		'',
		'',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=3
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'10.0.160.0/20',
		'',
		'',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=4
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'10.0.160.0/20',
		'10.0.0.0/19',
		'',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=5
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'10.0.160.0/20',
		'10.0.0.0/19',
		'10.0.64.0/19',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=6
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'10.0.160.0/20',
		'10.0.0.0/19',
		'10.0.64.0/19',
		'10.0.128.0/19',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=7
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'10.0.160.0/20',
		'10.0.0.0/19',
		'10.0.64.0/19',
		'10.0.128.0/19',
		'10.0.48.0/21',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=8
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'10.0.160.0/20',
		'10.0.0.0/19',
		'10.0.64.0/19',
		'10.0.128.0/19',
		'10.0.48.0/21',
		'10.0.112.0/21',
		''
	)
	test_procedure(test_number,parameters)

	test_number=9
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'10.0.160.0/20',
		'10.0.0.0/19',
		'10.0.64.0/19',
		'10.0.128.0/19',
		'10.0.48.0/21',
		'10.0.112.0/21',
		'10.0.176.0/21'
	)
	test_procedure(test_number,parameters)

	test_number=10
	build_params(
		'10.0.32.0/20',
		'',
		'10.0.160.0/20',
		'',
		'',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=11
	build_params(
		'10.0.32.0/20',
		'',
		'',
		'10.0.0.0/19',
		'',
		'',
		'10.0.48.0/21',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=12
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'',
		'10.0.0.0/19',
		'10.0.64.0/19',
		'',
		'10.0.48.0/21',
		'10.0.112.0/21',
		''
	)
	test_procedure(test_number,parameters)

	test_number=13
	build_params(
		'10.0.32.0/20',
		'10.0.96.0/20',
		'',
		'10.0.0.0/19',
		'10.0.64.0/19',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=14
	build_params(
		'10.0.32.0/20',
		'',
		'',
		'',
		'10.0.64.0/19',
		'',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=15
	build_params(
		'10.0.32.0/20',
		'',
		'',
		'',
		'',
		'10.0.128.0/19',
		'',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=16
	build_params(
		'10.0.32.0/20',
		'',
		'',
		'',
		'',
		'',
		'10.0.48.0/21',
		'',
		''
	)
	test_procedure(test_number,parameters)

	test_number=17
	build_params(
		'10.0.32.0/20',
		'',
		'',
		'',
		'',
		'',
		'',
		'',
		'10.0.176.0/21'
	)
	test_procedure(test_number,parameters)

main()
