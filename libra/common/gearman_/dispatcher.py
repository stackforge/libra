from libra.openstack.common import log


LOG = log.getLogger(__name__)


# TODO: Use oslo's rpc dispatcher mechanism instead ?
class Dispatcher(object):
    def __init__(self, manager):
        self.manager = manager

    def dispatch(self, worker, job):
        LOG.debug('Received data: %s', job.data)
        action = job.data['action'].lower()
        #try:
        #    func = getattr(self.manager, action)
        #    response = func(job.data)
        #except AttributeError:
        #    pass
        try:
            ctrl = self.manager.ctrl(LOG, job.data)
            response = ctrl.run()
        except AttributeError:
            LOG.error('Unable to find action %s', action)
            return
        LOG.debug('Response %s', response)
        return response
