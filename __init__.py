def classFactory(iface):
    from .plugin import MainPlugin
    return MainPlugin(iface)
    