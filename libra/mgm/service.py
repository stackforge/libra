
from libra.openstack.common import log
from libra.common import options
from libra.common import service
from libra.common.gearman_.service import WorkerService
from libra.mgm.controllers.root import PoolMgmController


LOG = log.getLogger(__name__)


class PoolManagerService(WorkerService):
    ctrl = PoolMgmController

    def list(self, data):
        return {}


def main():
    options.add_common_opts()
    service.prepare_service()
    svc = PoolManagerService(options.CONF.host, name='libra_pool_mgm')
    launcher = service.ThreadLauncher()
    launcher.launch_service(svc, threads=options.CONF.mgm.threads)
    launcher.wait()
    svc.start()
