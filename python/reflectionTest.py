import inspect
import sys

class FirmwareModule(object):
    def __init__(self):
        pass

    def performChecks(self):    
        pass

class Addition(FirmwareModule):
    def __init__(self):
        pass

    def add(self, *args, **kwarg):
        return sum([val for val in args[0]])
                    

class Multiplication(FirmwareModule):
    def __init__(self):
        pass

    def multiply(self, *args, **kwargs):
        mul = 1
        for val in args[0]:
            mul = mul * val
        return mul

    def performChecks(self):    
        pass


class Driver(object):

    def __init__(self):

        # Get list of subclasses for FirmwareModule
        self._availableModules = [cls.__name__ for cls in sys.modules[self.__module__].FirmwareModule.__subclasses__()]

    def loadModule(self, module):
        # Check if module is available
        if module not in self._availableModules:
            print "Module %s is not available" % module
        else:
            # Get list of class methods
            methods = inspect.getmembers(eval(module), predicate=inspect.ismethod)
            
            # Remove unwanted methods from list
            methods = [a for a, b in methods if a not in ['__init__', 'performChecks']]

            # Create module instances
            m = globals()[module]()
            self.__dict__[module] = globals()[module]()

            # Import module function into this class
            for method in methods:
                # Create function which class module method
                f = lambda *args, **kwargs : getattr(m, method)(args, kwargs)
                # Create class method and assign method
                setattr(self, method, f)
                
    def performChecks(self):
        for m in self._availableModules:
            getattr(self, m, 'performChecks')()

# Glory
driver = Driver()
driver.loadModule('Multiplication')
driver.loadModule('Addition')
print "Addition: ", driver.add(1,2,3,4,5,6)
print "Multiplication: ", driver.multiply(1,2,3,4,5,6)
driver.performChecks()
