#!/usr/bin/env python
"""
_Root_

The root object for a webtools application. It loads all the different views and
starts an appropriately configured CherryPy instance. Views are loaded 
dynamically and can be turned on/off via configuration file.

"""

__revision__ = "$Id: Root.py,v 1.19 2009/02/16 14:45:02 metson Exp $"
__version__ = "$Revision: 1.19 $"

# CherryPy
from cherrypy import quickstart, expose, server, log
from cherrypy import config as cpconfig
# configuration and arguments
#FIXME
from WMCore.Configuration import Configuration
from WMCore.Configuration import loadConfigurationFile
from optparse import OptionParser
# Factory to load pages dynamically
from WMCore.WMFactory import WMFactory
# Database access and DAO 
from WMCore.Database.DBCore import DBInterface
from WMCore.Database.DBFactory import DBFactory
from WMCore.DAOFactory import DAOFactory
# Logging
import WMCore.WMLogging
import logging 
from WMCore.DataStructs.WMObject import WMObject
from WMCore.WebTools.Welcome import Welcome

class Root(WMObject):
    def __init__(self, config):
        self.config = config
        self.config = config.section_("Webtools")
        self.appconfig = config.section_(self.config.application)
        self.app = self.config.application
        self.homepage = None
        
    def configureCherryPy(self):
        #Configure CherryPy
        try:
            cpconfig.update ({"server.environment": self.config.environment})
        except:
            cpconfig.update ({"server.environment": 'production'})
        try:
            cpconfig.update ({"server.socket_port": int(self.config.port)})
        except:
            cpconfig.update ({"server.socket_port": 8080})
        try:
            cpconfig.update ({'tools.expires.secs': int(self.config.expires)})
        except:
            cpconfig.update ({'tools.expires.secs': 300})
        try:
            cpconfig.update ({'log.screen': bool(self.config.log_screen)})
        except:
            cpconfig.update ({'log.screen': True})
        try:
            cpconfig.update ({'log.access_file': self.config.access_log_file})
        except:
            cpconfig.update ({'log.access_file': None})
        try:
            cpconfig.update ({'log.error_file': int(self.config.error_log_file)})
        except:
            cpconfig.update ({'log.error_file': None})

        cpconfig.update ({
                          'tools.expires.on': True,
                          'tools.response_headers.on':True,
                          'tools.etags.on':True,
                          'tools.etags.autotags':True,
                          'tools.encode.on': True,
                          'tools.gzip.on': True
                          })
        #cpconfig.update ({'request.show_tracebacks': False})
        #cpconfig.update ({'request.error_response': self.handle_error})
        #cpconfig.update ({'tools.proxy.on': True})
        #cpconfig.update ({'proxy.tool.base': '%s:%s' % (socket.gethostname(), opts.port)})
        log("loading config: %s" % cpconfig, 
                                   context=self.app, 
                                   severity=logging.DEBUG, 
                                   traceback=False)

    def loadPages(self):
        factory = WMFactory('webtools_factory')
        
        globalconf = self.appconfig.dictionary_()
        del globalconf['views'] 
        if 'index' in globalconf.keys():
            del globalconf['index']
         
        for view in self.appconfig.views.active:
            #Iterate through each view's configuration and instantiate the class
            config = Configuration()
            component = config.component_(view._internal_name)
            component.application = self.config.application
            for k in globalconf.keys():
                # Add the global config to the view
                component.__setattr__(k, globalconf[k])
            
            dict = view.dictionary_()
            for k in dict.keys():
                component.__setattr__(k, dict[k])
            # component now contains the full configuration (global + view)  
            # use this throughout 
            log("loading %s" % component._internal_name, context=self.app, 
                severity=logging.INFO, traceback=False)
            
            log("configuration for %s: %s" % (component._internal_name, 
                                    component), 
                                    context=self.app, 
                                    severity=logging.INFO, traceback=False)
                                
            log("Loading %s" % (component._internal_name), 
                                    context=self.app,
                                    severity=logging.DEBUG, 
                                    traceback=False)
            # Load the object
            obj = factory.loadObject(component.object, component)
            # Attach the object to cherrypy's root, at the name of the component 
            eval(compile("self.%s = obj" % component._internal_name, 
                            '<string>', 'single'))        
            log("%s available on %s/%s" % (component._internal_name, 
                                           server.base(), 
                                           component._internal_name), 
                                           context=self.app, 
                                           severity=logging.INFO, 
                                           traceback=False)
        
        if hasattr(self.appconfig.views, 'maintenance'):
            for i in self.appconfig.views.maintenance:
                #TODO: Show a maintenance page
                pass

        # now make the index page
        if hasattr(self.appconfig, 'index'):
            self.homepage = getattr(self, self.appconfig.index)
        else:
            log("No index defined for %s - instantiating default Welcome page" 
                                             % (self.app), 
                                           context=self.app, 
                                           severity=logging.INFO, 
                                           traceback=False)
            namesAndDocstrings = []
            # make a default Welcome
            for view in self.appconfig.views.active:
               viewName = view._internal_name
               viewObj = getattr(self, viewName)
               docstring = viewObj.__doc__
               namesAndDocstrings.append((viewName, docstring))
            self.homepage = Welcome(namesAndDocstrings)
    
    @expose
    def index(self):
        return self.homepage.index() 
    
    @expose
    def default(self, *args, **kwargs):
        return self.homepage.default(args, kwargs)

if __name__ == "__main__":
    config = __file__.rsplit('/', 1)[0] + '/DefaultConfig.py'
    parser = OptionParser()
    parser.add_option("-i", "--ini", dest="inifile", default=config,
                      help="write the configuration to FILE", metavar="FILE")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Be more verbose")
    opts, args = parser.parse_args()
    cfg = loadConfigurationFile(opts.inifile)
    root = Root(cfg)
    root.configureCherryPy()
    root.loadPages()
    quickstart(root)
