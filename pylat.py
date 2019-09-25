"""
pyLevel ACI Toolbox
PyLACIT
ACI toolbox


"""

class Plat(object):
    """
    class for interacting with ACI at highlevel
    methods are preconfigured for specific tasks
    see **TBD** for low(er) level interface
    """
    from getpass import getpass
    import requests
    from lxml import etree
    def __init__(self, apic, **kwargs):
        """
        :param apic: sets apic ip or hostname for fabric interaction
        :param username: sets username upon initialization
        :param password: sets password upon initialization
        """
        #
        try:
          self.username = kwargs['username']
        except KeyError:
          self.username = input("Enter username to interface with ACI: ")
        try:
          self.password = kwargs['password']
        except KeyError:
          self.password = getpass("Enter password for %s: " % self.username)
        