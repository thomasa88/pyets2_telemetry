import logging
import traceback

# Log exception and keep it short
def log_exception(e):
    exceptiondata = traceback.format_exc().splitlines()
    logging.error("%s: %s" % (type(e).__name__, e))
    logging.error("\n".join(exceptiondata[-3:-1]))
