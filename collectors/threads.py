"""Fail closed until Meta permissions and public-data retention are verified."""
def fetch_topics():
    raise RuntimeError('Threads collector is not authorized or implemented. Keep ENABLE_THREADS=false.')
