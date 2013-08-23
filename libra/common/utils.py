from stevedore.extension import ExtensionManager


def get_namespace_names(namespace):
    """
    Helper utility to get the names of the entrypoints in a namespace
    """
    em = ExtensionManager(namespace)
    return em.names()