import sys, traceback
print('PYTHONPATH:')
for p in sys.path:
    print(' ', p)
try:
    import sqlalchemy
    print('\nImported sqlalchemy from', getattr(sqlalchemy, '__file__', 'builtin'))
    import inspect
    print('sqlalchemy attrs sample:', list(sqlalchemy.__dict__.keys())[:10])
except Exception:
    print('\nImport error:')
    traceback.print_exc()
