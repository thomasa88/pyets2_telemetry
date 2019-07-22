import traceback

# Log exception and keep it short
def log_exception(logger, e):
    exceptiondata = traceback.format_exc().splitlines()
    logger.error("%s: %s" % (type(e).__name__, e))
    logger.error("\n".join(exceptiondata[-3:-1]))
