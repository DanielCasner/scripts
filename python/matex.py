#!/usr/bin/python
"""
This script generates latex code for matrix equations based from input in a
MATLAB style syntax.

Options:
-h             Prints out this help text
-f filename    Take input from the file specified
-o filename    Write output to file specified, the file will be truncated.
               If this option is not specified, output goes to standard out.
-a matrix      Treats all arguments after the -a as the input
If neither '-f' nor '-a' is specified, input is expected from standard in and
is terminated with a blank line.

Matrix Syntax:
The matrix syntax is basically the same as MATLAB. Rows are split by either
semicolons (;) or new lines. Columns can only be separated by whitespace,
however, not by commas.
"""
__author__ = "Daniel Casner <daniel@danielcasner.org>"
__version__ = 1.0

import re, sys

matrixExp = re.compile(r'(\[.*?\])', re.DOTALL | re.MULTILINE)
latexMatOpen  = r' \left[ \begin{array}'
latexMatClose = r' \end{array} \right]' + '\n'
latexRowSep = r'\\'
latexColSep = r'&'

def colsTag(numCols):
    "Returns the LaTeX column specification"
    retval = '{'
    while numCols > 0:
        retval += 'c'
        numCols -= 1
    retval += '} '
    return retval

def formMat(mat):
    """Accepts a MATLAB style matrix (including the square brackets) and
    returns the Latex equivalent."""
    # Get rid of the square brackets and split on semicolons
    splits = mat.group()[1:-1].split(';') 
    rows = []
    for s in splits: # And split lines on new lines
        rows.extend(s.split('\n'))
    # Now rows has the text for each row
    numCols = 0
    for i in range(len(rows)):
        rows[i] = rows[i].split() # Split on any white space
        if numCols == 0: # First time through
            numCols = len(rows[i])
        elif numCols != len(rows[i]):
            sys.stderr.write('Uneven number of columns in matix!\n')
            sys.exit(1)
    # We now have a nice list of lists of cells, just what we need
    # Start generating latex code
    matrix = latexMatOpen + colsTag(numCols)
    for row in rows:
        matrix += latexColSep.join(row) + latexRowSep
    matrix += latexMatClose
    return matrix
    

def process(input, outStream):
    """This method takes the MATLAB style input text and returns Latex code.
    Really we just call the formMat function on everything which looks like
    a matrix."""
    outStream.write(matrixExp.sub(formMat, input))


##### Program entry point #####
if __name__ == '__main__':
    if '-h' in sys.argv:
        print __doc__
        sys.exit(0)
    
    inputCode = ""
    outStream = sys.stdout
    if '-o' in sys.argv:
        try:
            outfile = sys.argv[sys.argv.index('-o') + 1]
        except:
            sys.stderr.write('Invalid arguments, try -h\n')
            sys.exit(1)
        try:
            outStream = open(outFile, 'w')
        except:
            sys.stderr.write('Could not open output file for writing\n')
            sys.exit(1)
    if '-f' in sys.argv:
        try:
            infile = sys.argv[sys.argv.index('-f') + 1]
        except:
            sys.stderr.write('Invalid arguments, try -h\n')
            sys.exit(1)
        try:
            inputCode = open(infile, 'r').read()
        except:
            sys.stderr.write('Could not open input file!\n')
            sys.exit(1)
    elif '-a' in sys.argv:
        try:
            inputCode = ' '.join(sys.argv[(sys.argv.index('-a') + 1):])
        except:
            sys.stderr.write('Invalid arguments, try -h\n')
            sys.exit(1)
    else:
        line = raw_input()
        while line:
            inputCode += line
            line = raw_input()
        
        
    process(inputCode, outStream)
    outStream.close()