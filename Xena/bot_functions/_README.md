If you add a new function in this folder, be sure to add an import for it to `__init__.py`.
Otherwise it's an extra level of reference outside of this folder.


## GOOD ##
- With reference in `__init__.py`
```python
#bot_functions/__init__.py
from bot_functions.file_name import function_name

#main.py
import bot_functions

def main():
    await bot_functions.function_name()
```

## BAD ##
- Without reference in `__init__.py`
```python
#main.py
import bot_functions

def main():
    await bot_functions.file_name.function_name()
```
- OR
```python
#main.py
from bot_functions import file_name

def main():
    await file_name.function_name()
```