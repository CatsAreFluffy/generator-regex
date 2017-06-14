'''This is a generator based regex module.'''
def charclass(x):
    '''Defines a character class. Also used for single characters.'''
    def charclass_gen(string):
        '''A generator for matching charclasses.'''
        for i in x:
            if len(string)>0 and string[0]==i:
                yield i
    return charclass_gen
def dot_gen(string):
    '''Matches any character except newlines.'''
    if len(string)>0 and string[0]!="\n":
        yield string[0]
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
        yield from pair(contents,quantifier(contents,0,-1))(string)
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
    raise NotImplementedError("I don't feel like it")

for i in sequence(charclass("a"),quantifier(charclass("bc"),0,-1),charclass("c"))("acccccc"):
    print(i)
