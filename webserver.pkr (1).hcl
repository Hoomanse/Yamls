packer {
    required_plugins {
      amazon = {
      version = ">= 0.0.1"
      source = "github.com/hashicorp/amazon"
      }
    }
}

source "amazon-ebs" "webserver" {
    ami_name = "Webserver-packer-project {{timestamp}}"
    ami_virtualization_type = "hvm"
    source_ami = "ami-0c2b8ca1dad447f8a"
    ebs_optimized = true
    instance_type = "t2.micro"
    region = "us-east-1"
    shutdown_behavior = "terminate"
    ssh_username = "ec2-user"
    ssh_timeout = "1h"
    tags = {
      description = "webserver"
    }
  
    launch_block_device_mappings {
      device_name = "/dev/xvda"
      volume_size = "8"
      volume_type = "gp3"
      delete_on_termination = true
    }
}
  
build {
    sources = ["source.amazon-ebs.webserver"]

    provisioner "shell" {
        inline = [
            "sudo yum update -y",
            "sudo amazon-linux-extras install ansible2 -y",
            "sudo amazon-linux-extras enable nginx1"
        ]
    }

    provisioner "ansible-local" {
        playbook_file = "webserver-playbook.yml"
    }
}
