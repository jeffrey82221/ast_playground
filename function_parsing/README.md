# Install 

pip install -r requirements.txt 


# Run 

python run_ast.py 


# Result 

```
1 Parsing of Function in example.py
Function Name: simple_function
Arg 0 x
Arg 1 y
Arg 2 c
Default value: 12
Unparsed Function:
 

def simple_function(x, y, c=12):
    x = (x + 1)
    y = (c + x)
    y = (y * 2)
    return (x + y)

2 Parsing of Class Method in example.py
Class Name Demo
Function Name: simple_function
Arg 0 self
Arg 1 x
Arg 2 y
Arg 3 c
Default value: 12
Unparsed Function:
 

def simple_function(self, x, y, c=12):
    x = (x + 1)
    y = (c + x)
    y = (y * 2)
    return (x + y)

3 Parsing of Class Method Here!
Class Name UDFClass
Function Name: run_all
Arg 0 self
Arg 1 x
Arg 2 y
Arg 3 c
Default value: 12
Unparsed Function:
 

def run_all(self, x, y, c=12):
    x = (x + 1)
    y = (c + x)
    y = (y * 2)
    return (x + y)
```
