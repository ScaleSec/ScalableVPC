# Scalable VPC Template
AWS CloudFormation template for creating a VPC of a specified size with security features.

Provides:
* Scales from one public subnet in one AZ to three layers of subnets across three AZs
	* "from 1x1 to 3x3"
* NAT Gateways created if Private Tiers are created
* VPC Flow Logs sent to CloudWatch Logs
* Private Amazon S3 access using a VPC Endpoint
* Optional Guardrail NACL to blacklist insecure services
	* FTP, Telnet, POP3, IMAP, SNMP v1 & v2 (from PCI DSS v3.0 requirement 1.1.6)
* Exports resource IDs for use by other automation
* Default CIDRs from: ["Practical VPC Design"](https://medium.com/aws-activate-startup-blog/practical-vpc-design-8412e1a18dcc)

## Architecture & Parameters:
![Architecture & Parameters](https://raw.githubusercontent.com/ScaleSec/ScalableVPC/master/images/architecture.png "Architectures & Parameters")

## Resource Creation Logic:
![Resource Creation Logic](https://raw.githubusercontent.com/ScaleSec/ScalableVPC/master/images/creation_logic.png "Resource Creation Logic")

## Subnet Condition Dependencies & Inheritance:
![Condition Dependencies & Inheritance](https://raw.githubusercontent.com/ScaleSec/ScalableVPC/master/images/conditions.png "Condition Dependencies & Inheritance")
