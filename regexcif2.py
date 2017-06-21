'''This is a generator based regex module.'''
class RegexState:
    '''An internal state for the regex engine.'''
    def __init__(self,string,index=0,captured=None,capturing=None):
        '''Create a new internal state. Implicitly opens group 0.'''
        self.string=string
        self.index=index
        if capturing is not None:
            self.capturing=capturing
        else:
            self.capturing={0:index}
        if captured is not None:
            self.captured=captured
        else:
            self.captured={}
    def __len__(self):
        '''Returns remaining string length.'''
        return len(self.string)-self.index
    def __getitem__(self,key):
        '''Indexes into the string relative to the position.'''
        if isinstance(key,slice):
            if key.start is not None:
                start=key.start+self.index
            else:
                start=self.index
            if key.stop is not None:
                stop=key.stop+self.index
            else:
                stop=len(self.string)-self.index
            return self.string[start:stop:key.step]
        else:
            return self.string[self.index+key]
    def __str__(self):
        '''Returns a string representation for human use.'''
        temp=""
        for i in self.captured:
            temp+=str(i)+":"+self.getcapture(i)+", "
        return temp[:-2]
    def startcapture(self,capturename):
        '''Open a capture.'''
        self.capturing[capturename]=self.index
        return self
    def endcapture(self,capturename):
        '''Close a capture.'''
        self.captured[capturename]=(self.capturing[capturename],self.index)
        del self.capturing[capturename]
        return self
    def getcapture(self,capturename):
        '''Get a capture as a string.'''
        return self.string[slice(*self.captured[capturename])]
    def goto(self,newpos):
        '''Go to a position.'''
        self.index=newpos
        return self
    def advance(self,offset):
        '''Advance the current position.'''
        self.index+=offset
        return self
    def copy(self):
        '''Return a deepcopy of this object.'''
        return RegexState(self.string,self.index,self.captured.copy(),self.capturing.copy())
    def debug(self,x=""):
        '''Prints debug info.'''
        print(self.string,self.index,self.capturing,self.captured,x)
        return self
def echo(x):
    '''Prints and returns its input. For debugging.'''
    print(x)
    return x
def regex(x):
    '''A wrapper for internal regex generators.'''
    def regex_gen(string):
        for i in range(len(string)):
            for j in x(RegexState(string,i)):
                yield j.endcapture(0)
    return regex_gen
def charclass(x):
    '''Defines a character class. Also used for single characters.'''
    def charclass_gen(string):
        '''A generator for matching charclasses.'''
        if len(string)>0 and string[0] in x:
            yield string.advance(1)
    return charclass_gen
def inv_charclass(x):
    '''Defines an inverted character class. Also used for `.`.'''
    def inv_charclass_gen(string):
        '''A generator for matching inverted charclasses.'''
        if len(string)>0 and string[0] not in x:
            yield string.advance(1)
def dot_gen(string):
    '''Matches any character except newlines.'''
    yield from inv_charclass("\n")(string)
def quantifier(contents,minmatches,maxmatches):
    '''Defines a quantifier. Use maxmatches=-1 for unlimited matches.'''
    def required_block(string):
        '''Subcomponent of a quantifier. Used when a submatch is required.'''
        yield from pair(contents,quantifier(contents,minmatches-1,maxmatches-1))(string.copy())
    def optional_block(string):
        '''Subcomponent of a quantifier. Used when a submatch is optional.'''
        yield from optional(pair(contents,quantifier(contents,0,maxmatches-1)))(string.copy())
    def nesting_block(string):
        '''Subcomponent of a quantifier. Used when the quantifier is unbounded.'''
        yield from pair(contents,nesting_block)(string.copy())
        yield string
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
        yield from contents(string.copy())
        yield string
    def optional_gen_lazy(string):
        '''Lazily matches an optional section.'''
        yield string
        yield from contents(string.copy())
    if lazy:
        return optional_gen_lazy
    else:
        return optional_gen
def anchor(pos):
    '''Defines an anchor.'''
    def anchor_gen(string):
        if string.index==(pos if pos>=0 else pos+len(string.string)+1):
            yield string
    return anchor_gen
def alternation(*contents):
    '''Defines an alternation.'''
    def alternation_gen(string):
        '''Matches an alternation.'''
        for i in contents:
            yield from i(string.copy())
    return alternation_gen
def capture(name,*contents):
    '''Defines a capturing group.'''
    def capture_gen(string):
        for i in sequence(*contents)(string.copy().startcapture(name)):
            yield i.endcapture(name)
            i.startcapture(name)
    return capture_gen
def backref(name):
    '''Defines a backreference.'''
    def backref_gen(string):
        '''Matches a backreference.'''
        a=string.string[slice(*string.captured[name])]
        b=string[0:len(a)]
        if a==b:
            yield string.advance(len(a))
    return backref_gen
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
def zerowidth(*contents):
    '''Defines a zero width assertion.'''
    def zerowidth_gen(string):
        x=string.index
        yield from (i.goto(x) for i in sequence(*contents)(string))
    return zerowidth_gen
def nothing_gen(string):
    '''Matches the empty string.'''
    yield string
def pair(content1,content2):
    '''Joins two components.'''
    def pair_gen(string):
        '''Matches two components.'''
        yield from (j for i in content1(string.copy()) for j in content2(i))
    return pair_gen
def compile_regex(string):
    '''Compile a regular expression.'''
    inter=[regex,[sequence]]
    ptr=0
    captures=0
    index=[1]
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
                index.insert(0,1) #I forgot what this does
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
        elif string[ptr]=="+":
            if isinstance(getpos()[-1],list):
                getpos()[-1]=[quantifier,getpos()[-1][:],1,-1]
            else:
                getpos()[-1]=[quantifier,getpos()[-1],1,-1]
            ptr+=1
        elif string[ptr]=="?":
            if isinstance(getpos()[-1],list):
                getpos()[-1]=[optional,getpos()[-1][:]]
            else:
                getpos()[-1]=[optional,getpos()[-1]]
            ptr+=1
            if len(string)>ptr and string[ptr]=="?":
                getpos[-1].append(True)
                ptr+=1
        elif string[ptr]==".":
            getpos().append([inv_charclass,"\n"])
            ptr+=1
        elif string[ptr]=="^":
            getpos().append([anchor,0])
            ptr+=1
        elif string[ptr]=="$":
            getpos().append([anchor,-1])
            ptr+=1
        elif string[ptr]=="(":
            if string[ptr+1]=="?":
                if string[ptr+2]==":":
                    getpos().append([sequence])
                    index.append(len(getpos())-1)
                    ptr+=2
                elif string[ptr+2]=="=":
                    getpos().append([zerowidth])
                    index.append(len(getpos())-1)
                    ptr+=2
                else:
                    raise ValueError("Invalid group type")
            else:
                captures+=1
                getpos().append([capture,captures])
                index.append(len(getpos())-1)
            ptr+=1
        elif string[ptr]==")":
            index.pop()
            ptr+=1
        elif string[ptr]=="\\":
            ptr+=1
            if string[ptr] in "1234567890":
                temp=""
                while len(string)>ptr and string[ptr] in "1234567890":
                    temp+=string[ptr]
                    ptr+=1
                getpos().append([backref,int(temp)])
            else:
                getpos().append([charclass,string[ptr]])
                ptr+=1
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
    #print(*inter[1],sep="\n") #print list form
    print(lformat(inter)) #print generator form
    return unquote(inter)

for i in compile_regex(r"{[0123456789]+,?[0123456789]*}")("{9,} {,} {9} {,5} {} {1,2}"):
    print(i)
