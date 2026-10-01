from google.cloud import compute_v1


PROJECT_ID = "lab-5-510121"
ZONE = "us-west1-b"
VM_NAME = "flask-vm"
MACHINE_TYPE = "f1-micro"

STARTUP_SCRIPT = """#!/bin/bash

apt-get update
apt-get install -y python3 python3-pip git

cd /root

git clone https://github.com/cu-csci-4253-datacenter/flask-tutorial

cd flask-tutorial

pip3 install .

flask --app flaskr init-db

nohup flask --app flaskr run -h 0.0.0.0 > /var/log/flask.log 2>&1 &
"""

def create_firewall_rule():
    firewall_client = compute_v1.FirewallsClient()

    firewall_rule = compute_v1.Firewall(
        name="allow-5000",
        allowed=[
            compute_v1.Allowed(
                I_p_protocol="tcp",
                ports=["5000"],
            )
        ],
        source_ranges=["0.0.0.0/0"],
        target_tags=["allow-5000"],
    )

    print("Creating firewall rule...")

    operation = firewall_client.insert(
        project=PROJECT_ID,
        firewall_resource=firewall_rule,
    )

    operation.result()

    print("Firewall rule created!")

def create_vm():
    metadata = compute_v1.Metadata(
        items=[
            compute_v1.Items(
                key="startup-script",
                value=STARTUP_SCRIPT,
            )
        ]
    )

    instance_client = compute_v1.InstancesClient()

    machine_type = (
        f"zones/{ZONE}/machineTypes/{MACHINE_TYPE}"
    )

    source_image = (
        "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
    )

    disk = compute_v1.AttachedDisk(
        boot=True,
        auto_delete=True,
        initialize_params=compute_v1.AttachedDiskInitializeParams(
            source_image=source_image,
        ),
    )

    network_interface = compute_v1.NetworkInterface(
        name="default",
        access_configs=[
            compute_v1.AccessConfig(
                name="External NAT",
                type_="ONE_TO_ONE_NAT",
            )
        ],
    )

    instance = compute_v1.Instance(
        name=VM_NAME,
        machine_type=machine_type,
        disks=[disk],
        network_interfaces=[network_interface],
        metadata=metadata,
    )

    print(f"Creating VM {VM_NAME}...")

    operation = instance_client.insert(
        project=PROJECT_ID,
        zone=ZONE,
        instance_resource=instance,
    )

    print("Waiting for VM creation...")
    operation.result()

    print("VM created!")

def add_network_tag():
    instance_client = compute_v1.InstancesClient()

    instance = instance_client.get(
        project=PROJECT_ID,
        zone=ZONE,
        instance=VM_NAME,
    )

    tags = compute_v1.Tags(
        items=["allow-5000"],
        fingerprint=instance.tags.fingerprint,
    )

    print("Adding network tag...")

    operation = instance_client.set_tags(
        project=PROJECT_ID,
        zone=ZONE,
        instance=VM_NAME,
        tags_resource=tags,
    )

    operation.result()

    print("Network tag added!")

def get_external_ip():
    instance_client = compute_v1.InstancesClient()

    instance = instance_client.get(
        project=PROJECT_ID,
        zone=ZONE,
        instance=VM_NAME,
    )

    for interface in instance.network_interfaces:
        for access_config in interface.access_configs:
            if access_config.nat_i_p:
                print("Flask URL:")
                print(f"http://{access_config.nat_i_p}:5000")
                return

    print("No external IP found.")

if __name__ == "__main__":
    create_vm()
    create_firewall_rule()
    add_network_tag()
    get_external_ip()
