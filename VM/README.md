## EC2 Provisioning (Create, Setup, Delete)
1) Finding out Amazon Linux AMI ID. Note that the AMI ID is specific to the region for which you have configured your aws account. You will need to search for appropriate Amazon Linux Name in the _get_ami_id() method. You can find the name of the AMI from the AWS console and use that in your search code.
2) Get security group id of the 'default' security group.
3) Create a new security group for HTTP traffic.
4) Authorize the HTTP security group to receive traffic from anywhere as source ('0.0.0.0/0') 5) Parse instance id from instance create response
6) Get information about the created instance. You should print the Public DNS name for the instance and its Public IP address. See the Output section for details.
7) Terminate the created instance
