#!/usr/bin/env python3

import time
import googleapiclient.discovery
import google.auth

credentials, project = google.auth.default()
compute = googleapiclient.discovery.build(
    'compute', 'v1', credentials=credentials
)

ZONE = 'us-west1-b'
DISK_NAME = 'flask-vm'
SNAPSHOT_NAME = 'base-snapshot-flask-vm'
MACHINE_TYPE = 'e2-medium'

def wait_for_operation(compute, project, zone, operation):
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation
        ).execute()

        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            return

        time.sleep(1)


def create_snapshot(compute, project, zone, disk_name, snapshot_name):
    print("Creating snapshot...")

    body = {
        'name': snapshot_name
    }

    operation = compute.disks().createSnapshot(
        project=project,
        zone=zone,
        disk=disk_name,
        body=body
    ).execute()

    wait_for_operation(
        compute,
        project,
        zone,
        operation['name']
    )

    print("Snapshot created:", snapshot_name)


def create_instance(compute, project, zone, instance_name, snapshot_name):
    machine_type = (
        'zones/{}/machineTypes/{}'.format(ZONE, MACHINE_TYPE)
    )

    source_snapshot = (
        'global/snapshots/{}'.format(snapshot_name)
    )

    config = {
        'name': instance_name,
        'machineType': machine_type,

        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceSnapshot': source_snapshot
                }
            }
        ],

        'networkInterfaces': [
            {
                'network': 'global/networks/default',
                'accessConfigs': [
                    {
                        'type': 'ONE_TO_ONE_NAT'
                    }
                ]
            }
        ],

        'tags': {
            'items': ['allow-5000']
        }
    }

    start = time.perf_counter()

    operation = compute.instances().insert(
        project=project,
        zone=zone,
        body=config
    ).execute()

    wait_for_operation(
        compute,
        project,
        zone,
        operation['name']
    )

    end = time.perf_counter()

    elapsed = end - start

    print("{} created in {:.2f} seconds".format(
        instance_name,
        elapsed
    ))

    return elapsed


def main():
    times = []

    for i in range(1, 4):
        instance_name = 'flask-vm-{}'.format(i)

        elapsed = create_instance(
            compute,
            project,
            ZONE,
            instance_name,
            SNAPSHOT_NAME
        )

        times.append((instance_name, elapsed))

    print("\nCreation times:")
    for name, elapsed in times:
        print("{}: {:.2f} seconds".format(name, elapsed))


if __name__ == '__main__':
    main()
