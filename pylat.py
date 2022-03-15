#!env python3
"""
pyLevel ACI Toolbox
PyLACIT
ACI toolbox


"""
from lxml import etree
import requests

class Pylat(object):
    """
    class for interacting with ACI at highlevel
    methods are preconfigured for specific tasks
    see **TBD** for low(er) level interface
    """
    def __init__(self, apic, **kwargs):
        """
        :param apic: sets apic ip or hostname for fabric interaction
        :param username: sets username upon initialization
        :param password: sets password upon initialization
        :param cert: can be string of a path to a root CA cert chain so certs are
                     verified. If not defined, certs are not verified
        :param challengetok: True or False(default). When True, REST calls require
                             extra header.
        """
        import requests
        from getpass import getpass
        #
        self.rs = SessionOverride(self)
        self._refresh_interval_ratio = 0.9
        self._aci_dict = {
                          'aaaLogin': 'https://%s/api/aaaLogin.xml' % apic,
                          'aaaRefresh': 'https://%s/api/aaaRefresh.xml' % apic,
                          'aaaLogout': 'https://%s/api/aaaLogout.xml' % apic,
                         }
        self.apic = apic
        self.last_response = None
        self.get = self.rs.get
        self.post = self.rs.post
        self.delete = self.rs.delete
        try:
            self.username = kwargs['username']
        except KeyError:
            self.username = input("Enter username to interface with ACI: ")
        try:
            self.password = kwargs['password']
        except KeyError:
            self.password = getpass("Enter password for %s: " % self.username)
        try:
            ## may consider making /etc/ssl/certs/ca-certificates.crt default
            self.cert = kwargs['cert']
        except KeyError:
            print("Certificates not verified")
            self.cert = False
        try:
            self._challengetok = bool(kwargs['challengetok'])
        except KeyError:
            ## no challenge token desired
            self._challengetok = False
        
    #

    def login(self, session_keepalive=True):
        """
        login method to start session with APIC
        
        :param session_keepalive: when set to true (default), refreshes are sent @ 90%
                                  of timeout value to keep session alive
        """
        import time
        import threading
        aaaUser_data = '<aaaUser name="%s" pwd="%s" />' % (self.username, self.password)
        #
        if self._challengetok:
            self.last_response = self.rs.post(self._aci_dict['aaaLogin'] + '?gui-token-request=yes', data=aaaUser_data, verify=self.cert)
            resp = etree.fromstring(self.last_response.text.encode())
            self.rs.headers.update({'APIC-challenge': resp.find('.//aaaLogin').attrib['urlToken']})
        else:
            self.last_response = self.rs.post(self._aci_dict['aaaLogin'], data=aaaUser_data, verify=self.cert)
            resp = etree.fromstring(self.last_response.text.encode())
        self.timeout = int(resp.find('.//aaaLogin').attrib['refreshTimeoutSeconds'] )
        self.refresh_thread = threading.Timer(int(self.timeout * self._refresh_interval_ratio), self.refresh)
        self.refresh_thread.setDaemon(True)
        if session_keepalive:
            self.refresh_thread.start()
        else:
            ## keepalives off
            pass
    #

    def logout(self):
        self.last_response = self.rs.post(self._aci_dict['aaaLogout'], data='<aaaUser name="%s" />' % self.username, verify=self.cert)
        if self.refresh_thread.isAlive():
            self.refresh_thread.cancel()
        return None
    #

    def refresh(self):
        """
        refresh method
        restarts refresh timer if session_keepalive is on
        """
        import threading
        self.last_response = self.rs.get(self._aci_dict['aaaRefresh'])
        if self.refresh_thread.isAlive():
            self.refresh_thread.cancel()
            self.refresh_thread = threading.Timer(int(self.timeout * self._refresh_interval_ratio), self.refresh)
            self.refresh_thread.setDaemon(True)
            self.refresh_thread.start()
        else:
            pass
    #
    
    def __del__(self):
        """
        object finalizer, sends a logout message to APIC upon object garbage collection
        """
        self.logout()
        if self.refresh_thread.isAlive():
            self.refresh_thread.cancel()
        else:
            pass
    #

class SessionOverride(requests.Session):
    """
    subclass of requests session class so that http response is returned AND APIC last_response attribute is updated
    """
    def __init__(self, apic_object):
        """
        inistantiate object with reference to apic object
        """
        self.apic_object = apic_object
        super().__init__()
    #
##    def get(self, *args, **kwargs):
##        self.apic_object.last_response = super().get(*args, **kwargs)
##        return self.apic_object.last_response
##    #
##    def post(self, *args, **kwargs):
##        self.apic_object.last_response = super().post(*args, **kwargs)
##        return self.apic_object.last_response
##    #
##    def delete(self, *args, **kwargs):
##        self.apic_object.last_response = super().delete(*args, **kwargs)
##        return self.apic_object.last_response
    #
    def get(self, *args, **kwargs):
        from requests.exceptions import MissingSchema
        try:
            self.apic_object.last_response = super().get(*args, **kwargs)
        except MissingSchema:
            kwargs['url'] = 'https://' + self.apic_object.apic + '/' + kwargs.get('url', args[0])
            self.apic_object.last_response = super().get(**kwargs)
        return self.apic_object.last_response
    #
    def post(self, *args, **kwargs):
        from requests.exceptions import MissingSchema
        try:
            self.apic_object.last_response = super().post(*args, **kwargs)
        except MissingSchema:
            kwargs['url'] = 'https://' + self.apic_object.apic + '/' + kwargs.get('url', args[0])
            self.apic_object.last_response = super().post(**kwargs)
        return self.apic_object.last_response
    #
    def delete(self, *args, **kwargs):
        from requests.exceptions import MissingSchema
        try:
            self.apic_object.last_response = super().delete(*args, **kwargs)
        except MissingSchema:
            kwargs['url'] = 'https://' + self.apic_object.apic + '/' + kwargs.get('url', args[0])
            self.apic_object.last_response = super().delete(**kwargs)
        return self.apic_object.last_response
