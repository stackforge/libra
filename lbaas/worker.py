import argparse
import json
import logging
import socket
from json_gearman import JSONGearmanWorker

from lbaas.faults import BadRequest


def lbaas_task(worker, job):
    """ Main Gearman worker task.  """

    # Turn string into JSON object
    data = json.loads(job.data)

    lb_name = data['name']
    logging.info("LB name: %s" % lb_name)

    if 'nodes' not in data:
        return BadRequest("Missing 'nodes' element").to_json()

    for lb_node in data['nodes']:
        port, address, status = None, None, None

        if 'port' in lb_node:
            port = lb_node['port']
        else:
            return BadRequest("Missing 'port' element.").to_json()

        if 'address' in lb_node:
            address = lb_node['address']
        else:
            return BadRequest("Missing 'address' element.").to_json()

        if 'status' in lb_node:
            status = lb_node['status']

        logging.info("LB node: %s:%s - %s" % (address, port, status))
        lb_node['status'] = 'ACTIVE'

    # Return the same JSON object, but with status fields set.
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',
                        help='enable debug output',
                        action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    my_ip = socket.gethostbyname(socket.gethostname())
    task_name = "lbaas-%s" % my_ip
    logging.debug("Registering task %s" % task_name)

    worker = JSONGearmanWorker(['localhost:4730'])
    worker.set_client_id(my_ip)
    worker.register_task(task_name, lbaas_task)

    try:
        worker.work()
    except KeyboardInterrupt:
        logging.debug("Quitting")
    except Exception as e:
        logging.critical("Exception: %s, %s" % (e.__class__, e))

    return 0
