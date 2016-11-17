############################################################
# HOMEWORK 5
#
# Team members: Andrew Deaver, Kathryn Hite
#
# Emails: Andrew.Deaver@students.olin.edu, Kathryn.Hite@students.olin.edu
#
# Remarks: 
#



import sys, os

#
# Expressions
#

class Exp (object):
    pass


class EValue (Exp):
    # Value literal (could presumably replace EInteger and EBoolean)
    def __init__ (self,v):
        self._value = v
    
    def __str__ (self):
        return "EValue({})".format(self._value)

    def eval (self,env):
        return self._value

    
class EPrimCall (Exp):
    # Call an underlying Python primitive, passing in Values
    #
    # simplifying the prim call
    # it takes an explicit function as first argument

    def __init__ (self,prim,es):
        self._prim = prim
        self._exps = es

    def __str__ (self):
        return "EPrimCall(<prim>,[{}])".format(",".join([ str(e) for e in self._exps]))

    def eval (self,env):
        vs = [ e.eval(env) for e in self._exps ]
        return apply(self._prim,vs)


class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self,env):
        v = self._cond.eval(env)
        if v.type != "boolean":
            raise Exception ("Runtime error: condition not a Boolean")
        if v.value:
            return self._then.eval(env)
        else:
            return self._else.eval(env)


class EId (Exp):
    # identifier

    def __init__ (self,id):
        self._id = id

    def __str__ (self):
        return "EId({})".format(self._id)

    def eval (self,env):
        for (id,v) in env:
            if self._id == id:
                return v
        raise Exception("Runtime error: unknown identifier {}".format(self._id))


class ECall (Exp):
    # Call a defined function in the function dictionary
    # can be pass several arguments, but only handles one

    def __init__ (self,fun,exps):
        self._fun = fun
        self._exps = exps

    def __str__ (self):
        return "ECall({},{})".format(str(self._fun),str([str(exp) for exp in self._exps]))

    def eval (self,env):
        f = self._fun.eval(env)
        if f.type != "function":
            raise Exception("Runtime error: trying to call a non-function")
        args = [exp.eval(env) for exp in self._exps]
        new_env = [(f.params[i],args[i]) for i in range(len(args))] + f.env
        return f.body.eval(new_env)

class EFunction (Exp):
    # Creates an anonymous function

    def __init__ (self,params,body,name=""):
        self._params = params
        self._body = body
        self._func_name = name

    def __str__ (self):
        return "EFunction({},{})".format(str(self._params),str(self._body))

    def eval (self,env):
        n_closure = VClosure(self._params,self._body,env)
        if(self._func_name != ""):
            n_closure.env.insert(0, tuple([self._func_name, n_closure]))
        return n_closure

class EArray (Exp):

    def __init__ (self, array):
        self._array = array

    def __str__ (self):
        return "EArray({})".format(self._array)

    def eval(self, env):
        vals = [v.eval(env) for v in self._array]
        return VArray(vals, env)

class ERecord (Exp):

    def __init__(self, record):
        self._record = record

    def __str__(self):
        return "ERecord({})".format(self._record)

    def eval(self, env):
        dic = {key:val.eval(env) for key, val in self._record}
        return VRecord(dic)
#
# Values
#

class Value (object):
    pass


class VInteger (Value):
    # Value representation of integers
    
    def __init__ (self,i):
        self.value = i
        self.type = "integer"

    def __str__ (self):
        return str(self.value)

    
class VBoolean (Value):
    # Value representation of Booleans
    
    def __init__ (self,b):
        self.value = b
        self.type = "boolean"

    def __str__ (self):
        return "true" if self.value else "false"

    
class VClosure (Value):
    
    def __init__ (self,params,body,env):           
        self.params = params
        self.body = body
        self.env = env
        self.type = "function"

    def __str__ (self):
        return "<function [{}] {}>".format(self.params,str(self.body))

class VArray(Value):

    def __init__(self, array, env):
        self.type = "array"
        self.value = array

        self._methods = []
        self._methods.insert(0, ("index", EFunction("i", EPrimCall(oper_index, [EId("self"), EId("i")]))))
        self._methods.insert(0, ("length", EFunction([], EPrimCall(oper_length, [EId("self")]))))
        self._methods.insert(0, ("map", EFunction("f", EPrimCall(oper_map, [EId("self"), EId("f")]))))

        self.env = []
        self.env.insert(0, ("self", self))
        self.env += [(id, e.eval(self.env + env)) for (id, e) in self._methods]

    def __str__(self):
        return "<array {}>".format([str(val) for val in self.value])

class VRecord(Value):

    def __init__(self, record):
        self.type = "record"
        self.value = record

    def __str__(self):
        return "<record {}>".format([str(key) + " : " + str(self.value[key]) for key in self.value])
# Primitive operations

# Primitive operations

def oper_plus (v1,v2): 
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value + v2.value)
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_minus (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value - v2.value)
    raise Exception ("Runtime error: trying to subtract non-numbers")

def oper_times (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value * v2.value)
    raise Exception ("Runtime error: trying to multiply non-numbers")

def oper_equal (v1,v2):
    if v1.type == v2.type:
        return VBoolean(v1.value == v2.value)
    raise Exception ("Runtime error: trying to compare value of different types")

def oper_greater_than (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value > v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value > v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_less_than (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value < v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value < v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_greater_or_equal (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value >= v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value >= v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_less_or_equal (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value <= v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value <= v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_not_equal (v1,v2):
    if v1.type == v2.type:
        return VBoolean(v1.value != v2.value)
    raise Exception ("Runtime error: trying to compare value of different types")

def oper_not(v1):
    if v1.type == "boolean":
        return VBoolean(not v1.value)
    raise Exception("Runtime error: trying to not a non-boolean")

def oper_zero (v1):
    if v1.type == "integer":
        return VBoolean(v1.value==0)
    raise Exception ("Runtime error: type error in zero?")

def oper_index(obj, index):
    if(obj.content.type == "array" and index.type == "integer"):
        if(index.value < len(obj.content.value) and index.value >= 0):
            return obj.content.value[index.value]
        raise Exception ("Array index out of bounds")
    raise Exception ("Trying to find index of non-array")

def oper_length(obj):
    if(obj.content.type == "array"):
        return VInteger(len(obj.content.value))

def oper_map(obj, func):
    if(obj.content.type == "array" and func.type == "function"):
        init_array = [func.body.eval(zip(func.params,[val]) + func.env) for val in obj.content.value]
        return VArray(VInteger(len(init_array)), obj.content.env, init_array)


# this initial environment works with Q1 when you've completed it

def initial_env ():
    env = []
    env.insert(0,
        ("+",
         VClosure(["x","y"],EPrimCall(oper_plus,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("-",
         VClosure(["x","y"],EPrimCall(oper_minus,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("*",
         VClosure(["x","y"],EPrimCall(oper_times,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("==",
         VClosure(["x","y"],EPrimCall(oper_equal,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        (">",
         VClosure(["x","y"],EPrimCall(oper_greater_than,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("<",
         VClosure(["x","y"],EPrimCall(oper_less_than,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        (">=",
         VClosure(["x","y"],EPrimCall(oper_greater_or_equal,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("<=",
         VClosure(["x","y"],EPrimCall(oper_less_or_equal,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("<>",
         VClosure(["x","y"],EPrimCall(oper_not_equal,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("*",
         VClosure(["x","y"],EPrimCall(oper_times,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("zero?",
         VClosure(["x"],EPrimCall(oper_zero,
                                  [EId("x")]),
                  env)))
    env.insert(0,
        ("square",
         VClosure(["x"],ECall(EId("*"),[EId("x"),EId("x")]),
                  env)))
    env.insert(0,
        ("=",
         VClosure(["x","y"],ECall(EId("zero?"),
                                  [ECall(EId("-"),[EId("x"),EId("y")])]),
                  env)))
    env.insert(0,
        ("+1",
         VClosure(["x"],ECall(EId("+"),[EId("x"),EValue(VInteger(1))]),
                  env)))
    return env



##
## PARSER
##
# cf http://pyparsing.wikispaces.com/

from pyparsing import Word, Literal, ZeroOrMore, OneOrMore, Keyword, Forward, alphas, alphanums, Optional, MatchFirst, delimitedList


def letUnimplementedError ():
    raise Exception ("ERROR: let functionality not implemented yet")

def parse_natural (input):
    # parse a natural string into an element of the abstract representation

    # <expr> ::= <integer>
    #          true
    #          false
    #          <identifier>
    #          ( expr )
    #          <expr> ? <expr> : <expr>
    #          let ( <bindings> ) <expr>
    #          <expr> + <expr>
    #          <expr> * <expr>
    #          <expr> - <expr>
    #          <name> ( <expr-seq> )

    # <bindings> ::= <name> = <expr> , <bindings>
    #              <name> = <expr>

    # <expr-seq> ::= <expr> , <expr-seq>
    #              <expr>    

    RESERVE_WORDS = ["let"]

    idChars = alphas+"_+*-?!=<>"

    pIDENTIFIER = ~MatchFirst(map(Keyword, RESERVE_WORDS)) + Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(str(result[0])))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pINTEGER = Word("-0123456789","0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pBASICEXPR = Forward()
    pEXPROPR = Forward()
    pBODY = Forward()
    pEXPR = Forward()

    pBINDING = pNAME + Keyword("=") + pBASICEXPR
    pBINDING.setParseAction(lambda result: (result[0], result[2]))

    pBINDINGS = delimitedList(pBINDING) 
    pBINDINGS.setParseAction(lambda result: [result])

    pBASICEXPR << (pINTEGER + pEXPROPR | pBOOLEAN + pEXPROPR  | pINTEGER | pBOOLEAN | pIDENTIFIER + pEXPROPR | pIDENTIFIER)
    pBASICEXPR.setParseAction(append_left)

    pEXPRSEQ = delimitedList(pBASICEXPR)
    pEXPRSEQ.setParseAction(lambda result: [result])

    pENTRY = pNAME + ":" + pBASICEXPR
    pENTRY.setParseAction(lambda result: (result[0], result[2]))

    pENTRY_LIST = delimitedList(pENTRY)
    pENTRY_LIST.setParseAction(lambda result: [result])

    pADD = Keyword("+") + pBASICEXPR
    pADD.setParseAction(lambda result: EPrimCall(oper_plus, [result[1]]))

    pTIMES  = Keyword("*") + pBASICEXPR
    pTIMES.setParseAction(lambda result: EPrimCall(oper_times, [result[1]]))

    pMINUS  = Keyword("-") + pBASICEXPR
    pMINUS.setParseAction(lambda result: EPrimCall(oper_minus, [result[1]]))

    pEQUALS = Keyword("==") + pBASICEXPR
    pEQUALS.setParseAction(lambda result: EPrimCall(oper_equal, [result[1]]))

    pNOT_EQUALS = Keyword("<>") + pBASICEXPR
    pNOT_EQUALS.setParseAction(lambda result: EPrimCall(oper_not_equal, [result[1]]))

    pLESS_THAN = Keyword("<") + pBASICEXPR
    pLESS_THAN.setParseAction(lambda result: EPrimCall(oper_less_than, [result[1]]))

    pLESS_THAN_EQUALS = Keyword("<=") + pBASICEXPR
    pLESS_THAN_EQUALS.setParseAction(lambda result: EPrimCall(oper_less_or_equal, [result[1]]))

    pGREATER_THAN = Keyword(">") + pBASICEXPR
    pGREATER_THAN.setParseAction(lambda result: EPrimCall(oper_greater_than, [result[1]]))

    pGREATER_THAN_EQUALS = Keyword(">=") + pBASICEXPR
    pGREATER_THAN_EQUALS.setParseAction(lambda result: EPrimCall(oper_greater_or_equal, [result[1]]))

    pAND = Keyword("and") + pBASICEXPR
    pAND.setParseAction(lambda result: EIf(None, result[1], EValue(VBoolean(False))))

    pOR = Keyword("or") + pBASICEXPR
    pOR.setParseAction(lambda result: EIf(None, EValue(VBoolean(True)), result[1]))

    pIF = Keyword("?") + pBASICEXPR + ":" + pBASICEXPR
    pIF.setParseAction(lambda result: EIf(None, result[1], result[3]))

    pLET = Keyword("let") + "(" + pBINDINGS + ")" + pBASICEXPR
    pLET.setParseAction(lambda result: ECall(EFunction([b[0] for b in result[2]], result[4]), [b[1] for b in result[2]]))

    pFUN = Keyword("fun") + "(" + delimitedList(pNAME) + ")" + pBODY
    pFUN.setParseAction(lambda result: EFunction(result[2], result[4]))

    pFUN_RECURS = Keyword("fun") + pNAME + "(" + delimitedList(pNAME) + ")" + pBODY
    pFUN_RECURS.setParseAction(lambda result: EFunction(result[3], result[5], name=result[1]))

    pARRAY = Keyword("[") + pEXPRSEQ + Keyword("]")
    pARRAY.setParseAction(lambda result: EArray(result[1]))

    pRECORD = Keyword("{") + pENTRY_LIST + Keyword("}")
    pRECORD.setParseAction(lambda result: ERecord(result[1]))

    pNOT = Keyword("not") + pBASICEXPR
    pNOT.setParseAction(lambda result: EPrimCall("not", [result[1]]))

    pEXPROPR << (pTIMES | pADD | pMINUS | pIF | pEQUALS | pNOT_EQUALS | pLESS_THAN | pLESS_THAN_EQUALS | pGREATER_THAN | pGREATER_THAN_EQUALS)

    pEXPR << (pLET | pNOT | pARRAY | pRECORD | pFUN | pFUN_RECURS | pBASICEXPR)
    result = pEXPR.parseString(input)[0]
    return result    # the first element of the result is the expression

## natural shell helper functions

def append_left(result):
    if(len(result) == 2):
        if type(result[1]) == EPrimCall:
            result[1]._exps.append(result[0])
            result[1]._exps.reverse()
            return result[1]
        if type(result[1]) == EIf:
            result[1]._cond = result[0] 
            return result[1]
    return result[0]


def parse (input):
    # parse a string into an element of the abstract representation

    # Grammar:
    #
    # <expr> ::= <integer>
    #            true
    #            false
    #            <identifier>
    #            ( if <expr> <expr> <expr> )
    #            ( let ( ( <name> <expr> ) ) <expr )
    #            (function ( <name> ) <expr> )
    #            ( <expr> <expr> )
    #
    # <definition> ::= ( defun <name> ( <name> ) <expr> )
    #


    idChars = alphas+"_+*-~/?!=<>"

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(result[0]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pNAMES = OneOrMore(pNAME)
    pNAMES.setParseAction(lambda result: [result])

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pEXPR = Forward()

    pEXPRS = OneOrMore(pEXPR)
    pEXPRS.setParseAction(lambda result: [result])

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    pBINDING = "(" + pNAME + pEXPR + ")"
    pBINDING.setParseAction(lambda result: (result[1],result[2]))

    pBINDINGS = OneOrMore(pBINDING)
    pBINDINGS.setParseAction(lambda result: [ result ])

    pLET = "(" + Keyword("let") + "(" + pBINDINGS + ")" + pEXPR + ")"
    pLET.setParseAction(lambda result: ECall(EFunction([b[0] for b in result[3]], result[5]), [b[1] for b in result[3]]))

    pCALL = "(" + pEXPR + pEXPRS + ")"
    pCALL.setParseAction(lambda result: ECall(result[1],result[2]))

    pFUN = "(" + Keyword("function") + "(" + pNAMES + ")" + pEXPR + ")"
    pFUN.setParseAction(lambda result: EFunction(result[3],result[5], name=""))

    pFUN_RECURS = "(" + Keyword("function") + pNAME + "(" + pNAMES + ")" + pEXPR + ")"
    pFUN_RECURS.setParseAction(lambda result: EFunction(result[4],result[6], name=result[2]))

    pEXPR << (pINTEGER | pBOOLEAN | pIDENTIFIER | pIF | pLET | pFUN | pFUN_RECURS | pCALL)
    # can't attach a parse action to pEXPR because of recursion, so let's duplicate the parser
    pTOPEXPR = pEXPR.copy()
    pTOPEXPR.setParseAction(lambda result: {"result":"expression","expr":result[0]})

    pDEFUN = "(" + Keyword("defun") + pNAME + "(" + pNAMES + ")" + pEXPR + ")"
    pDEFUN.setParseAction(lambda result: {"result":"function",
                                         "name":result[2],
                                         "params":result[4],
                                         "body":result[6]})
    pTOP = (pDEFUN | pTOPEXPR)

    result = pTOP.parseString(input)[0]
    return result    # the first element of the result is the expression


def shell ():
    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Homework 5 - Func Language"
    print "#quit to quit"
    env = []

    ## UNCOMMENT THIS LINE WHEN YOU COMPLETE Q1 IF YOU WANT TO TRY
    ## EXAMPLES
    env = initial_env()
    while True:
        inp = raw_input("func> ")

        if inp == "#quit":
            return

        # try:
        result = parse_natural(inp)

        print result.eval(env)

        # if result["result"] == "expression":
        #     exp = result["expr"]
        #     print "Abstract representation:", exp
        #     v = exp.eval(env)
        #     print v

        # elif result["result"] == "function":
        #     # the top-level environment is special, it is shared
        #     # amongst all the top-level closures so that all top-level
        #     # functions can refer to each other
        #     env.insert(0,(result["name"],VClosure(result["params"],result["body"],env)))
        #     print "Function {} added to top-level environment".format(result["name"])

        # except Exception as e:
        #     print "Exception: {}".format(e)
        #     exc_type, exc_obj, exc_tb = sys.exc_info()
        #     fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #     print(exc_type, fname, exc_tb.tb_lineno)


        
# increase stack size to let us call recursive functions quasi comfortably
sys.setrecursionlimit(10000)



def initial_env_curry ():
    env = []
    env.insert(0,
        ("+",
         VClosure(["x"],EFunction("y",EPrimCall(oper_plus,
                                              [EId("x"),EId("y")])),
                  env)))
    env.insert(0,
        ("-",
         VClosure(["x"],EFunction("y",EPrimCall(oper_minus,
                                              [EId("x"),EId("y")])),
                  env)))
    env.insert(0,
        ("*",
         VClosure(["x"],EFunction("y",EPrimCall(oper_times,
                                              [EId("x"),EId("y")])),
                  env)))
    env.insert(0,
        ("zero?",
         VClosure(["x"],EPrimCall(oper_zero,
                                         [EId("x")]),
                           env)))
    env.insert(0,
        ("square",
         VClosure(["x"],ECall(ECall(EId("*"),[EId("x")]),
                            [EId("x")]),
                  env)))
    env.insert(0,
        ("=",
         VClosure(["x"],EFunction("y",ECall(EId("zero?"),
                                          [ECall(ECall(EId("-"),[EId("x")]),
                                                 [EId("y")])])),
                  env)))
    env.insert(0,
        ("+1",
         VClosure(["x"],ECall(ECall(EId("+"),[EId("x")]),
                            [EValue(VInteger(1))]),
                  env)))
    return env


def parse_curry (input):
    # parse a string into an element of the abstract representation

    # Grammar:
    #
    # <expr> ::= <integer>
    #            true
    #            false
    #            <identifier>
    #            ( if <expr> <expr> <expr> )
    #            ( let ( ( <name> <expr> ) ) <expr )
    #            (function ( <name> ) <expr> )
    #            ( <expr> <expr> )
    #
    # <definition> ::= ( defun <name> ( <name> ) <expr> )
    #


    idChars = alphas+"_+*-~/?!=<>"

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(result[0]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pNAMES = OneOrMore(pNAME)
    pNAMES.setParseAction(lambda result: [result])

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pEXPR = Forward()

    pEXPRS = OneOrMore(pEXPR)
    pEXPRS.setParseAction(lambda result: [result])

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    pBINDING = "(" + pNAME + pEXPR + ")"
    pBINDING.setParseAction(lambda result: (result[1],result[2]))

    pBINDINGS = OneOrMore(pBINDING)
    pBINDINGS.setParseAction(lambda result: [ result ])

    pLET = "(" + Keyword("let") + "(" + pBINDINGS + ")" + pEXPR + ")"
    pLET.setParseAction(lambda result: ECall(EFunction([b[0] for b in result[3]], result[5]), [b[1] for b in result[3]]))

    pCALL = "(" + pEXPR + pEXPRS + ")"
    pCALL.setParseAction(lambda result: curry_parse_call(result[1],result[2]))

    pFUN = "(" + Keyword("function") + "(" + pNAMES + ")" + pEXPR + ")"
    pFUN.setParseAction(lambda result: curry_parse_fun(result[3],result[5]))

    pEXPR << (pINTEGER | pBOOLEAN | pIDENTIFIER | pIF | pLET | pFUN | pCALL)
    # can't attach a parse action to pEXPR because of recursion, so let's duplicate the parser
    pTOPEXPR = pEXPR.copy()
    pTOPEXPR.setParseAction(lambda result: {"result":"expression","expr":result[0]})

    pDEFUN = "(" + Keyword("defun") + pNAME + "(" + pNAMES + ")" + pEXPR + ")"
    pDEFUN.setParseAction(lambda result: {"result":"function",
                                         "name":result[2],
                                         "params":result[4],
                                         "body":result[6]})
    pTOP = (pDEFUN | pTOPEXPR)

    result = pTOP.parseString(input)[0]
    return result    # the first element of the result is the expression


def curry_parse_call(first, next):
    if(len(next) == 1):
        return ECall(first, next)
    else:
        return ECall(curry_parse_call(first, next[:len(next)-1]), [next[len(next)-1]])

def curry_parse_fun(exprs, func):
    if(len(exprs) == 1):
        return EFunction(exprs, func)
    else:
        return EFunction(exprs[0], curry_parse_fun(exprs[1:], func))

def curry_create_closure(params, body, env, depth):
    if depth == 1:
        return VClosure([params[0]], curry_create_closure(params[1:], body, env, depth+1), env)
    else:
        if len(params) <= 1:
            return EFunction(params, body)
        else:
            return EFunction([params[0]], curry_create_closure(params[1:], body, env, depth+1))

def shell_curry ():

    print "Homework 5 - Func Language"
    print "#quit to quit"
    env = initial_env_curry()
    
    while True:
        inp = raw_input("func/curry> ")

        if inp == "#quit":
            return

        # try:
        result = parse_curry(inp)

        if result["result"] == "expression":
            exp = result["expr"]
            print "Abstract representation:", exp
            v = exp.eval(env)
            print v

        elif result["result"] == "function":
            # the top-level environment is special, it is shared
            # amongst all the top-level closures so that all top-level
            # functions can refer to each other
            env.insert(0,(result["name"],curry_create_closure(result["params"], result["body"], env, 1)))
            print "Function {} added to top-level environment".format(result["name"])

        # except Exception as e:
        #     print "Exception: {}".format(e)

