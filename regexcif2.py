'''This is a generator based regex module.'''
def charclass(x):
    '''Defines a character class. Also used for single characters.'''
    def charclass_gen(string):
        '''A generator for matching charclasses.'''
        if len(string)>0 and string[0] in x:
            yield string[0]
    return charclass_gen
def inv_charclass(x):
    '''Defines an inverted character class. Also used for `.`.'''
    def inv_charclass_gen(string):
        '''A generator for matching inverted charclasses.'''
        if len(string)>0 and string[0] not in x:
            yield string[0]
def dot_gen(string):
    '''Matches any character except newlines.'''
    yield from inv_charclass("\n")(string)
def quantifier(contents,minmatches,maxmatches):
    '''Defines a quantifier. Use maxmatches=-1 for unlimited matches.'''
    def required_block(string):
        '''Subcomponent of a quantifier. Used when a submatch is required.'''
        yield from pair(contents,quantifier(contents,minmatches-1,maxmatches-1))(string)
    def optional_block(string):
        '''Subcomponent of a quantifier. Used when a submatch is optional.'''
        yield from optional(pair(contents,quantifier(contents,0,maxmatches-1)))(string)
    def nesting_block(string):
        '''Subcomponent of a quantifier. Used when the quantifier is unbounded.'''
        yield from pair(contents,nesting_block)(string)
        yield ""
    if minmatches>0:
        return required_block
    elif maxmatches<0:
        return nesting_block
    elif maxmatches>0:
        return optional_block
    else:
        return nothing_gen
def optional(contents,lazy=False):
    '''Defines an optional section.'''
    def optional_gen(string):
        '''Greedily matches an optional section.'''
        yield from contents(string)
        yield ""
    def optional_gen_lazy(string):
        '''Lazily matches an optional section.'''
        yield ""
        yield from contents(string)
    if lazy:
        return optional_gen_lazy
    else:
        return optional_gen
def alternation(*contents):
    '''Defines an alternation.'''
    def alternation_gen(string):
        '''Matches an alternation.'''
        for i in contents:
            yield from i(string)
    return alternation_gen
def sequence(*contents):
    '''Joins components.'''
    def sequence_gen(string):
        '''Matches a sequence of components.'''
        yield from pair(contents[0],sequence(*contents[1:]))(string)
    if len(contents)==0:
        return nothing_gen
    elif len(contents)==1:
        return contents[0]
    else:
        return sequence_gen
def nothing_gen(string):
    '''Matches the empty string.'''
    yield ""
def pair(content1,content2):
    '''Joins two components.'''
    def pair_gen(string):
        '''Matches two components.'''
        yield from (i+j for i in content1(string) for j in content2(string[len(i):]))
    return pair_gen
def compile_regex(string):
    '''Compile a regular expression. Supports characters, charclasses, and alternations.'''
    inter=[sequence]
    ptr=0
    index=[]
    def getpos():
        '''Return the current operating list.'''
        temp=inter
        for i in index:
            temp=temp[i]
        return temp
    while ptr<len(string):
        if string[ptr]=="[":
            temp=[] #chars in charclass
            invert=string[ptr+1]=="^"
            ptr+=1
            while string[ptr]!="]":
                temp.append(string[ptr])
                ptr+=1
            ptr+=1
            if invert:
                getpos().append([inv_charclass,"".join(temp)])
            else:
                getpos().append([charclass,"".join(temp)])
        elif string[ptr]=="|":
            if getpos()[0]!=alternation:
                temp=getpos()
                temp[:]=[alternation,temp[:]]
                index.insert(0,0)
            index.pop()
            getpos().append([sequence])
            index.append(len(getpos())-1)
            ptr+=1
        elif string[ptr]=="*":
            if isinstance(getpos()[-1],list):
                getpos()[-1]=[quantifier,getpos()[-1][:],0,-1]
            else:
                getpos()[-1]=[quantifier,getpos()[-1],0,-1]
            ptr+=1
        elif string[ptr]=="(":
            if string[ptr+1]=="?":
                if string[ptr+2]==":":
                    getpos().append([sequence])
                    index.append(len(getpos())-1)
                    ptr+=2
                else:
                    raise ValueError("Invalid group type")
            else:
                raise ValueError("Capturing groups are not supported")
            ptr+=1
        elif string[ptr]==")":
            index.pop()
            ptr+=1
        elif string[ptr]=="\\":
            getpos().append([charclass,string[ptr+1]])
            ptr+=2
        else:
            getpos().append([charclass,string[ptr]])
            ptr+=1
    def unquote(x):
        '''Convert list format into generators.'''
        if isinstance(x,list):
            return x[0](*[unquote(i) for i in x[1:]])
        else:
            return x
    def lformat(x):
        '''Convert list format to readable string.'''
        if isinstance(x,list):
            return lformat(x[0])+"("+",".join([lformat(i) for i in x[1:]])+")"
        elif isinstance(x,int):
            return str(x)
        elif isinstance(x,str):
            return repr(x)
        else:
            return str(x).split()[1]
    #print(*inter,sep="\n") #print list form
    #print(lformat(inter)) #print generator form
    return unquote(inter)

for i in compile_regex("(?:[ac]b)*")("abcbcbabc"):
    print(i)
