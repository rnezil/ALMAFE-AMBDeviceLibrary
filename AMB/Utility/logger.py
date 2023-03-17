import logging

def getLogger() -> logging.Logger:
    try:
        # check for and return static singleton:
        return getLogger.logger
    except:
        # create, configure, and return static singleton:
        getLogger.logger = logging.getLogger('ALMAFE-AMBDeviceLibrary')
        getLogger.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        ch.setFormatter(formatter)
        getLogger.logger.addHandler(ch)
        return getLogger.logger
