############################################################
# HOMEWORK 5
#
# Team members: Andrew Deaver, Kathryn Hite
#
# Emails: Andrew.Deaver@students.olin.edu, Kathryn.Hite@students.olin.edu
#
# Remarks: 
#



import sys, os, traceback

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
        if f.type == "ref":
            f = f.content

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

class EString(Exp):

    def __init__(self, string):
        self._string = string

    def __str__(self):
        return "EString({})".format(self._string)

    def eval(self, env):
        return VString(self._string)

class EFor (Exp):

    def __init__ (self, init, cond, incr, stat):
        self._init = init
        self._cond = cond
        self._incr = incr
        self._stat = stat

    def __str__ (self):
        return "EFor({},{})".format(str(self._init), str(self._cond), str(self._incr), str(self._stat))

    def eval (self, env):
        if len(self._init) > 0:
            env.insert(0, (self._init[0][0], VRefCell(self._init[0][1].eval(env))))
        e = EWhile(self._cond, EDo([self._stat, self._incr]))
        e.eval(env)
        return VNone()

class EDo (Exp):

    def __init__ (self,exps):
        self._exps = exps

    def __str__ (self):
        return "EDo([{}])".format(",".join(str(e) for e in self._exps))

    def eval (self,env):
        # default return value for do when no arguments
        v = VNone()
        for e in self._exps:
            v = e.eval(env)
        return v

class EWhile (Exp):

    def __init__ (self,cond,exp):
        self._cond = cond
        self._exp = exp

    def __str__ (self):
        return "EWhile({},{})".format(str(self._cond),str(self._exp))

    def eval (self,env):
        c = self._cond.eval(env)
        if c.type != "boolean":
            raise Exception ("Runtime error: while condition not a Boolean")
        while c.value:
            self._exp.eval(env)
            c = self._cond.eval(env)
            if c.type != "boolean":
                raise Exception ("Runtime error: while condition not a Boolean")
        return VNone()

class ELet (Exp):
    # local binding
    # allow multiple bindings
    # eager (call-by-avlue)

    def __init__ (self,bindings,e2):
        self._bindings = bindings
        self._e2 = e2

    def __str__ (self):
        return "ELet([{}],{})".format(",".join([ "({},{})".format(id,str(exp)) for (id,exp) in self._bindings ]),self._e2)

    def eval (self,env):
        new_env = [ (id,e.eval(env)) for (id,e) in self._bindings] + env
        return self._e2.eval(new_env)

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

class VNone (Value):

    def __init__ (self):
        self.type = "none"

    def __str__ (self):
        return "none"
    
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

class VString(Value):
    def __init__(self, string):
        self.type = "string"
        self.value = string

    def __str__(self):
        return "<string {}>".format(self.value)

class VRecord(Value):

    def __init__(self, record):
        self.type = "record"
        self.value = record

    def __str__(self):
        return "<record {}>".format([str(key) + " : " + str(self.value[key]) for key in self.value])

class VRefCell (Value):

    def __init__ (self,initial):
        self.content = initial
        self.type = "ref"

    def __str__ (self):
        return "<ref {}>".format(str(self.content))

# Primitive operations

# Primitive operations

def oper_plus (v1,v2): 
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value + v2.value)
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_minus (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value - v2.value)
    raise Exception ("Runtime error: trying to subtract non-numbers")

def oper_times (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value * v2.value)
    raise Exception ("Runtime error: trying to multiply non-numbers")

def oper_equal (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == v2.type:
        return VBoolean(v1.value == v2.value)
    raise Exception ("Runtime error: trying to compare value of different types")

def oper_greater_than (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value > v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value > v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_less_than (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value < v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value < v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_greater_or_equal (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value >= v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value >= v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_less_or_equal (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value <= v2.value)
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value <= v2.value)
    raise Exception ("Runtime error: trying to compare non-numbers")

def oper_not_equal (v1,v2):
    if v1.type == "ref":
        v1 = v1.content
    if v2.type == "ref":
        v2 = v2.content

    if v1.type == v2.type:
        return VBoolean(v1.value != v2.value)
    raise Exception ("Runtime error: trying to compare value of different types")

def oper_not(v1):
    if v1.type == "ref":
        v1 = v1.content

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


def oper_update (v1,v2):
    if v1.type == "ref":
        v1.content = v2
        return VNone()
    raise Exception ("Runtime error: updating a non-reference value")
 
def oper_print (v1):
    if v1.type == "ref":
        v1 = v1.content

    print v1
    return VNone()

def oper_update_array(v1, i, v2):
    if v1.type == "ref" and v1.content.type == "array":
        if(i.type == "integer"):
            if(i.value < len(v1.content.value) and i.value >= 0):
                v1.content.value[i.value] = v2
                return VNone()
            raise Exception ("Runtime error: invalid array index")
        raise Exception("Runtime error: not a valid index")
    if v1.type == "ref" and v1.content.type == "record":
        if(str(i.value) in v1.content.value.keys()):
            v1.content.value[str(i.value)] = v2
            return VNone()
        raise Exception ("Runtime error: invalid key")
    raise Exception ("Runtime error: updating a non-reference value or updating non-array")

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

from pyparsing import Word, Literal, ZeroOrMore, OneOrMore, Keyword, Forward, alphas, alphanums, Optional, MatchFirst, delimitedList, NoMatch


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

    pNAMES = delimitedList(pNAME)
    pNAMES.setParseAction(lambda result: [result])

    pINTEGER = Word("-0123456789","0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pBASICEXPR = Forward()
    pEXPROPR = Forward()
    pSTMT_BLOCK = Forward()
    pEXPR = Forward()
    pSTMT = Forward()

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

    pFUN = Keyword("fun") + "(" + pNAMES + ")" + pSTMT_BLOCK
    pFUN.setParseAction(lambda result: EFunction(result[2], result[4]))

    pFUN_RECURS = Keyword("fun") + pNAME + "(" + pNAMES + ")" + pSTMT_BLOCK
    pFUN_RECURS.setParseAction(lambda result: EFunction(result[3], result[5], name=result[1]))

    pFUN_CALL = pIDENTIFIER + "(" + pEXPRSEQ + ")"
    pFUN_CALL.setParseAction(lambda result: ECall(result[0], result[2]))

    pARRAY = Keyword("[") + pEXPRSEQ + Keyword("]")
    pARRAY.setParseAction(lambda result: EArray(result[1]))

    pRECORD = Keyword("{") + pENTRY_LIST + Keyword("}")
    pRECORD.setParseAction(lambda result: ERecord(result[1]))

    pNOT = Keyword("not") + pBASICEXPR
    pNOT.setParseAction(lambda result: EPrimCall("not", [result[1]]))

    pEXPROPR << (pTIMES | pADD | pMINUS | pIF | pEQUALS | pNOT_EQUALS | pLESS_THAN_EQUALS | pGREATER_THAN_EQUALS | pLESS_THAN | pGREATER_THAN)

    pDECL_VAR = "var" + pNAME + "=" + pEXPR + ";"
    pDECL_VAR.setParseAction(lambda result: (result[1],result[3]))

    # hack to get pDECL to match only PDECL_VAR (but still leave room
    # to add to pDECL later)
    pDECL = ( pDECL_VAR | NoMatch() )

    pDECLS = ZeroOrMore(pDECL)
    pDECLS.setParseAction(lambda result: [result])

    pDECL_OPT = Optional(pDECL)
    pDECL_OPT.setParseAction(lambda result: [result])

    pSTMT_IF_1 = "if" + pEXPR + pSTMT + "else" + pSTMT
    pSTMT_IF_1.setParseAction(lambda result: EIf(result[1],result[2],result[4]))

    pSTMT_IF_2 = "if" + pEXPR + pSTMT
    pSTMT_IF_2.setParseAction(lambda result: EIf(result[1],result[2],EValue(VBoolean(True))))
   
    pSTMT_WHILE = "while" + pEXPR + pSTMT
    pSTMT_WHILE.setParseAction(lambda result: EWhile(result[1],result[2]))

    pSTMT_PRINT = "print" + pEXPR + ";"
    pSTMT_PRINT.setParseAction(lambda result: EPrimCall(oper_print,[result[1]]));

    pSTMT_UPDATE = pNAME + "=" + pEXPR + ";"
    pSTMT_UPDATE.setParseAction(lambda result: EPrimCall(oper_update,[EId(result[0]),result[2]]))

    pSTMT_UPDATE_ARRAY = pNAME + "[" + pEXPR + "]" + Keyword("=") + pEXPR + ";"
    pSTMT_UPDATE_ARRAY.setParseAction(lambda result: EPrimCall(oper_update_array, [EId(result[0]), result[2], result[5]]))

    pSTMT_UPDATE_RECORD = pNAME + "{" + pNAME + "}" + Keyword("=") + pEXPR + ";"
    pSTMT_UPDATE_RECORD.setParseAction(lambda result: EPrimCall(oper_update_array, [EId(result[0]), EString(result[2]), result[5]]))

    pFOR = Keyword("for") + "(" + pDECL_OPT + pEXPR + ";" + pSTMT_UPDATE + ")" + pSTMT
    pFOR.setParseAction(lambda result: EFor(result[2], result[3], result[5], result[7]))

    pSTMTS = ZeroOrMore(pSTMT)
    pSTMTS.setParseAction(lambda result: [result])

    def mkBlock (decls,stmts):
        bindings = [ (n,ERefCell(expr)) for (n,expr) in decls ]
        return ELet(bindings,EDo(stmts))
        
    pSTMT_BLOCK << "{" + pDECLS + pSTMTS + "}"
    pSTMT_BLOCK.setParseAction(lambda result: mkBlock(result[1],result[2]))

    pSTMT << ( pSTMT_IF_1 | pSTMT_IF_2 | pSTMT_WHILE | pSTMT_PRINT | pSTMT_UPDATE | pSTMT_UPDATE_RECORD | pSTMT_UPDATE_ARRAY | pSTMT_BLOCK | pFOR)

    pEXPR << (pLET | pNOT | pARRAY | pRECORD | pFUN | pFUN_RECURS | pFUN_CALL | pBASICEXPR)

    pTOP_STMT = pSTMT.copy()
    pTOP_STMT.setParseAction(lambda result: {"result":"statement",
                                             "stmt":result[0]})

    pTOP_DECL = pDECL.copy()
    pTOP_DECL.setParseAction(lambda result: {"result":"declaration",
                                             "decl":result[0]})

    pTOP = (pTOP_DECL | pTOP_STMT )

    result = pTOP.parseString(input)[0]
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
        inp = raw_input("shell> ")

        try:
            result = parse_natural(inp)

            if result["result"] == "statement":
                stmt = result["stmt"]
                # print "Abstract representation:", exp
                v = stmt.eval(env)

            elif result["result"] == "abstract":
                print result["stmt"]

            elif result["result"] == "quit":
                return

            elif result["result"] == "declaration":
                (name,expr) = result["decl"]
                v = expr.eval(env)
                env.insert(0,(name,VRefCell(v)))
                print "{} defined".format(name)
                
                
        except Exception as e:
            print "Exception: {}".format(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            traceback.print_exc()


        
# increase stack size to let us call recursive functions quasi comfortably
sys.setrecursionlimit(10000)