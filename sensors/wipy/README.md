
Use Atom to get repl to access wipy

To reset the filesystem
```
import os, machine
os.fsformat('/flash') OR os.mkfs('/flash')
machine.reset()
```
