import sqlalchemy, sys
print('version:', getattr(sqlalchemy, '__version__', 'n/a'))
print('file:', getattr(sqlalchemy, '__file__', 'n/a'))
print('sys.path:')
for p in sys.path:
    print(p)
