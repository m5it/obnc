import re

###
def rmatch(m,s):
    ret=0
    p=re.compile( m )
    if p.match( s ):
        ret=1
    return ret
    
###
def encode(text):
    return text.encode("ascii")
