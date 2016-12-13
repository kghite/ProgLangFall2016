############################################################
# Simple imperative language
# C-like surface syntac
# with S-expression syntax for expressions
# (no recursive closures)
#

import sys, os, traceback
import numpy as np

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

    def __init__ (self,fun,exps):
        self._fun = fun
        self._args = exps

    def __str__ (self):
        return "ECall({},[{}])".format(str(self._fun),",".join(str(e) for e in self._args))

    def eval (self,env):
        f = self._fun.eval(env)
        if f.type != "function":
            raise Exception("Runtime error: trying to call a non-function")
        args = [ e.eval(env) for e in self._args]
        if len(args) != len(f.params):
            raise Exception("Runtime error: argument # mismatch in call")
        new_env = zip(f.params,args) + f.env
        return f.body.eval(new_env)


class EFunction (Exp):
    # Creates an anonymous function

    def __init__ (self,params,body):
        self._params = params
        self._body = body

    def __str__ (self):
        return "EFunction([{}],{})".format(",".join(self._params),str(self._body))

    def eval (self,env):
        return VClosure(self._params,self._body,env)


class ERefCell (Exp):
    # this could (should) be turned into a primitive
    # operation.  (WHY?)

    def __init__ (self,initialExp):
        self._initial = initialExp

    def __str__ (self):
        return "ERefCell({})".format(str(self._initial))

    def eval (self,env):
        v = self._initial.eval(env)
        return VRefCell(v)

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


class EFor (Exp):

    def __init__ (self, init, cond, incr, stat):
        self._init = init
        self._cond = cond
        self._incr = incr
        self._stat = stat

    def __str__ (self):
        return "EFor({},{})".format(str(self._init), str(self._cond), str(self._incr), str(self._exp))

    def eval (self, env):
        if len(self._init) > 0:
            env.insert(0, (self._init[0][0], VRefCell(self._init[0][1].eval(env))))
        e = EWhile(self._cond, EDo([self._stat, self._incr]))
        e.eval(env)
        return VNone()

class EArray (Exp):

    def __init__ (self, exp):
        self._exp = exp

    def __str__ (self):
        return "EArray({})".format(self._exp)

    def eval(self, env):
        v = self._exp.eval(env)

        if(v.type != "numeric"):
            raise Exception ("Cannot create an array of non-integer length")

        return VArray(v.value, env)

class EWith (Exp):

    def __init__ (self, ref, exp):
        self._ref = ref
        self._exp = exp

    def __str__ (self):
        return "EWith({}, {})".format(self._ref, self._exp)

    def eval(self, env):
        obj = self._ref.eval(env).content

        if(obj.type != "array"):
            raise Exception ("Cannot apply operation to a non-array")

        return self._exp.eval(obj.env + env)

class ENormal (Exp):

    def __init__(self, mean, std):
        self._mu = mean
        self._sigma = std

    def __str__(self):
        return "ENormal({}, {})".format(self._mu, self._sigma)

    def eval(self, env):
        mu = self._mu.eval(env)
        sigma = self._sigma.eval(env)

        if(mu.type != "numeric" or sigma.type != "numeric" and p.type != "numeric"):
            raise Exception ("Cannot create normal distribution from non-numeric values")

        return VDistribution("normal", np.random.normal(mu.value, sigma.value, 1000))


class EFlip (Exp):

    def __init__(self, success):
        self._p = success

    def __str__(self):
        return "EFlip({})".format(self._p)

    def eval(self, env):
        p = self._p.eval(env)

        if(p.type != "numeric" and p.type != "numeric"):
            raise Exception ("Cannot create a binomial distribution from a non-numeric value")

        return VDistribution("binomial", np.random.binomial(1, p.value/100.0, 1000))


class ESample (Exp):

    def __init__(self, distribution, x=None):
        self._dist = distribution
        self._x = x

    def __str__ (self):
        return "ESample({})".format(self.distribution, self._x)

    def eval(self, env):
        dist = self._dist.eval(env)
        x = None if self._x == None else self._x.eval(env)

        if x == None:
            if dist.distribution == "normal":
                return VNumeric(dist.value[np.random.randint(0, len(dist.value))])

            if dist.distribution == "binomial":
                if dist.value[np.random.randint(0, len(dist.value))] == 1:
                    return VBoolean(True)
                return VBoolean(False)
        else:
            if dist.distribution == "normal":
                if(x.type != "numeric" and x.type != "numeric"):
                    raise Exception ("Cannot get value for a normal distribution with non-integer")

                sigma = np.std(dist.value)
                mu = np.mean(dist.value)
                return VNumeric(1/(sigma * np.sqrt(2 * np.pi)) * np.exp( - (x.value - mu)**2 / (2 * sigma**2)))

            if dist.distribution == "binomial":
                if(x.type != "boolean"):
                    raise Exception ("Cannot get value for a binomial distribution with non-boolean")

                prob = sum(dist.value)/float(len(dist.value))

                if(x.value):
                    return VNumeric(prob)
                else:
                    return VNumeric(1 - prob)
#
# Values
#

class Value (object):
    pass


class VNumeric (Value):
    # Value representation of integers
    
    def __init__ (self,i):
        self.value = i
        self.type = "numeric"

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
        return "<function [{}] {}>".format(",".join(self.params),str(self.body))

    
class VRefCell (Value):

    def __init__ (self,initial):
        self.content = initial
        self.type = "ref"

    def __str__ (self):
        return "<ref {}>".format(str(self.content))


class VNone (Value):

    def __init__ (self):
        self.type = "none"

    def __str__ (self):
        return "none"

class VString (Value):

    def __init__(self, val):
        self.value = val
        self.type = "string"

    def __str__ (self):
        return self.value

    def length(self):
        return VNumeric(len(self.value))

    def substring(self, begin, end):
        if (end > len(self.value)-1 or begin < 0):
            print begin
            print end
            print len(self.value)
            raise Exception ("String slicing exception: Substring indices out of bounds")
        if (end < begin):
            raise Exception ("End index must be larger than begin index")
        return VString(self.value[begin:end])

    def concat(self, add):
        return VString(self.value + add.value)

    def startswith(self, compare):
        if(compare.type != "string"):
            raise Exception("Value Error: Cannot compare string with " + compare.type)
        return VBoolean(self.value.startswith(compare.value))

    def endswith(self, compare):
        if(compare.type != "string"):
            raise Exception("Value Error: Cannot compare string with " + compare.type)
        return VBoolean(self.value.endswith(compare.value))
        
    def lower(self):
        return VString(self.value.lower())

    def upper(self):
        return VString(self.value.upper())

class VArray(Value):

    def __init__(self, initial_size, env, array=None):
        self.type = "array"
        if(array is not None):
            self.value = array
        else:
            self.value = [VNone()] * initial_size

        self._methods = []
        self._methods.insert(0, ("index", EFunction("i", EPrimCall(oper_index, [EId("self"), EId("i")]))))
        self._methods.insert(0, ("length", EFunction([], EPrimCall(oper_length, [EId("self")]))))
        self._methods.insert(0, ("map", EFunction("f", EPrimCall(oper_map, [EId("self"), EId("f")]))))

        self.env = []
        self.env.insert(0, ("self", VRefCell(self)))
        self.env += [(id, VRefCell(e.eval(self.env + env))) for (id, e) in self._methods]

    def __str__(self):
        return "<array {}>".format([str(val) for val in self.value])


class VDistribution (Value):

    def __init__(self, d_type, array):
        self.type = "distribution"
        self.distribution = d_type
        self.value = array

        # if(self.distribution == "binomial"):
        #     print sum(array)/float(len(array))
        # else:
        #     print array

    def __str__(self):
        return "<distribution {}>".format(self.distribution)



# Primitive operations

def oper_plus (v1,v2): 
    if v1.type == "numeric" and v2.type == "numeric":
        return VNumeric(v1.value + v2.value)
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_minus (v1,v2):
    if v1.type == "numeric" and v2.type == "numeric":
        return VNumeric(v1.value - v2.value)
    raise Exception ("Runtime error: trying to subtract non-numbers")

def oper_times (v1,v2):
    if v1.type == "numeric" and v2.type == "numeric":
        return VNumeric(v1.value * v2.value)
    raise Exception ("Runtime error: trying to multiply non-numbers")

def oper_zero (v1):
    if v1.type == "numeric":
        return VBoolean(v1.value==0)
    raise Exception ("Runtime error: type error in zero?")

def oper_lessthan (v1, v2):
    if v1.type == "numeric" and v2.type == "numeric":
        if v1.value < v2.value:
            return VBoolean(True)
        else:
            return VBoolean(False)
    raise Exception("Runtime error: trying to compare non-integers")

def oper_greaterthan (v1, v2):
    if v1.type == "numeric" and v2.type == "numeric":
        if v1.value > v2.value:
            return VBoolean(True)
        else:
            return VBoolean(False)
    raise Exception("Runtime error: trying to compare non-integers")

def oper_equalto (v1, v2):
    if v1.type == "numeric" and v2.type == "numeric":
        if v1.value == v2.value:
            return VBoolean(True)
        else:
            return VBoolean(False)
    raise Exception("Runtime error: trying to compare non-integers")

def oper_deref (v1):
    if v1.type == "ref":
        return v1.content
    raise Exception ("Runtime error: dereferencing a non-reference value")

def oper_update (v1,v2):
    if v1.type == "ref":
        v1.content = v2
        return VNone()
    raise Exception ("Runtime error: updating a non-reference value")
 
def oper_print (v1):
    print v1
    return VNone()

def oper_update_array(v1, i, v2):
    if v1.type == "ref" and v1.content.type == "array":
        if(i.type == "numeric"):
            if(i.value < len(v1.content.value) and i.value >= 0):
                v1.content.value[i.value] = v2
                return VNone()
            raise Exception ("Runtime error: invalid array index")
        raise Exception("Runtime error: not a valid index")
    raise Exception ("Runtime error: updating a non-reference value or updating non-array")

def oper_index(obj, index):
    if(obj.content.type == "array" and index.type == "numeric"):
        if(index.value < len(obj.content.value) and index.value >= 0):
            return obj.content.value[index.value]
        raise Exception ("Array index out of bounds")
    raise Exception ("Trying to find index of non-array")

def oper_length(obj):
    if(obj.content.type == "array"):
        return VNumeric(len(obj.content.value))

def oper_map(obj, func):
    if(obj.content.type == "array" and func.type == "function"):
        init_array = [func.body.eval(zip(func.params,[val]) + func.env) for val in obj.content.value]
        return VArray(VNumeric(len(init_array)), obj.content.env, init_array)

def oper_str_length(v1):
    if v1.type != "string":
        raise Exception("Runtime error: attempting string operation on non-string")
    print v1.length()
    return v1.length()

def oper_substring(v1, begin, end):
    if v1.type != "string":
        raise Exception("Runtime error: attempting string operation on non-string")
    print v1.substring(begin, end)
    return v1.substring(begin, end)

def oper_concat(v1, add):
    if v1.type != "string":
        raise Exception("Runtime error: attempting string operation on non-string")
    print v1.concat(add)
    return v1.concat(add)

def oper_startswith(v1, compare):
    if v1.type != "string":
        raise Exception("Runtime error: attempting string operation on non-string")
    print v1.startswith(compare)
    return v1.startswith(compare)

def oper_endswith(v1, compare):
    if v1.type != "string":
        raise Exception("Runtime error: attempting string operation on non-string")
    print v1.endswith(compare)
    return v1.endswith(compare)

def oper_lower(v1):
    if v1.type != "string":
        raise Exception("Runtime error: attempting string operation on non-string")
    print v1.lower()
    return v1.lower()

def oper_upper(v1):
    if v1.type != "string":
        raise Exception("Runtime error: attempting string operation on non-string")
    print v1.upper()
    return v1.upper()


############################################################
# IMPERATIVE SURFACE SYNTAX
#



##
## PARSER
##
# cf http://pyparsing.wikispaces.com/

from pyparsing import Word, Literal, ZeroOrMore, OneOrMore, oneOf, Keyword, Forward, alphas, alphanums, NoMatch, Optional, White


def initial_env_imp ():
    # A sneaky way to allow functions to refer to functions that are not
    # yet defined at top level, or recursive functions
    env = []
    env.insert(0,
               ("+",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_plus,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
               ("-",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_minus,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
               ("*",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_times,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
               ("zero?",
                VRefCell(VClosure(["x"],
                                  EPrimCall(oper_zero,[EId("x")]),
                                  env))))
    env.insert(0,
                ("<",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_lessthan,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
                (">",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_greaterthan,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
                ("=",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_equalto,[EId("x"),EId("y")]),
                                  env))))

    return env




def parse_imp (input):
    # parse a string into an element of the abstract representation

    # Grammar:
    #
    # <expr> ::= <integer>
    #            true
    #            false
    #            <identifier>
    #            ( if <expr> <expr> <expr> )
    #            ( function ( <name ... ) <expr> )    
    #            ( <expr> <expr> ... )
    #
    # <decl> ::= var name = expr ; 
    #
    # <stmt> ::= if <expr> <stmt> else <stmt>
    #            while <expr> <stmt>
    #            name <- <expr> ;
    #            print <expr> ;
    #            <block>
    #
    # <block> ::= { <decl> ... <stmt> ... }
    #
    # <toplevel> ::= <decl>
    #                <stmt>
    #


    idChars = alphas+"_+*-?!=<>"

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    #### NOTE THE DIFFERENCE
    pIDENTIFIER.setParseAction(lambda result: EPrimCall(oper_deref,[EId(result[0])]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pCHARS = oneOf(list(alphas)).leaveWhitespace()
    pCHARS.setParseAction(lambda result: result)

    pNAMES = ZeroOrMore(pNAME)
    pNAMES.setParseAction(lambda result: [result])

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VNumeric(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pESC_ESC = Keyword("~") + "~"
    pESC_ESC.setParseAction(lambda result: result[1])

    pESC_STR = Keyword("~") + '"'
    pESC_STR.setParseAction(lambda result: result[1])

    pSTRING_CONTENT = ZeroOrMore(pESC_STR | pESC_ESC | pCHARS | White(' ', max=1)).leaveWhitespace()
    pSTRING_CONTENT.setParseAction(lambda result: [result])

    pSTRING = '\"' + pSTRING_CONTENT + '\"'
    pSTRING.setParseAction(lambda result: EValue(VString("".join(printR([result[1]])))))

    pEXPR = Forward()

    pEXPRS = ZeroOrMore(pEXPR)
    pEXPRS.setParseAction(lambda result: [result])

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    def mkFunBody (params,body):
        bindings = [ (p,ERefCell(EId(p))) for p in params ]
        return ELet(bindings,body)

    pFUN = "(" + Keyword("function") + "(" + pNAMES + ")" + pEXPR + ")"
    pFUN.setParseAction(lambda result: EFunction(result[3],mkFunBody(result[3],result[5])))

    pCALL = "(" + pEXPR + pEXPRS + ")"
    pCALL.setParseAction(lambda result: ECall(result[1],result[2]))

    pARRAY = "(" + Keyword("new-array") + pEXPR + ")"
    pARRAY.setParseAction(lambda result: EArray(result[2]))

    pWITH = "(" + Keyword("with") + pNAME + pEXPR + ")"
    pWITH.setParseAction(lambda result: EWith(EId(result[2]), result[3]))

    pNORMAL = "(" + Keyword("normal") + pEXPR + pEXPR + ")"
    pNORMAL.setParseAction(lambda result: ENormal(result[2], result[3]))

    pFLIP = "(" + Keyword("flip") + pEXPR + ")"
    pFLIP.setParseAction(lambda result: EFlip(result[2]))

    pDISTRIBUTION = (pNORMAL | pFLIP)
    pDISTRIBUTION.setParseAction(lambda result: result)

    pSAMPLE_NO_PARAM = "(" + Keyword("sample") + pDISTRIBUTION + ")"
    pSAMPLE_NO_PARAM.setParseAction(lambda result: ESample(result[2]))

    pSAMPLE_PARAM = "(" + Keyword("sample") + pDISTRIBUTION + pEXPR + ")"
    pSAMPLE_PARAM.setParseAction(lambda result: ESample(result[2], result[3]))

    pSAMPLE = (pSAMPLE_NO_PARAM | pSAMPLE_PARAM)
    pSAMPLE.setParseAction(lambda result: result)

    pEXPR << (pINTEGER | pBOOLEAN | pSTRING | pIDENTIFIER | pWITH | pIF | pFUN | pARRAY | pDISTRIBUTION | pSAMPLE | pCALL)

    pSTMT = Forward()

    pPROD = Keyword("procedure") + pNAME + "(" + pNAMES + ")" + pSTMT
    pPROD.setParseAction(lambda result: (result[1], EFunction(result[3],mkFunBody(result[3], result[5]))))

    pDECL_VAR = "var" + pNAME + "=" + pEXPR + ";"
    pDECL_VAR.setParseAction(lambda result: (result[1],result[3]))

    # hack to get pDECL to match only PDECL_VAR (but still leave room
    # to add to pDECL later)
    pDECL = ( pDECL_VAR | pPROD | NoMatch() )

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

    pSTMT_UPDATE = pNAME + "<-" + pEXPR + ";"
    pSTMT_UPDATE.setParseAction(lambda result: EPrimCall(oper_update,[EId(result[0]),result[2]]))

    pSTMT_UPDATE_ARRAY = pNAME + "[" + pEXPR + "]" + Keyword("<-") + pEXPR + ";"
    pSTMT_UPDATE_ARRAY.setParseAction(lambda result: EPrimCall(oper_update_array, [EId(result[0]), result[2], result[5]]))

    pFOR = Keyword("for") + "(" + pDECL_OPT + pEXPR + ";" + pSTMT_UPDATE + ")" + pSTMT
    pFOR.setParseAction(lambda result: EFor(result[2], result[3], result[5], result[7]))

    pPROD_CALL = pNAME + "(" + pEXPRS + ")" + Keyword(";")
    pPROD_CALL.setParseAction(lambda result: ECall(result[0], result[2]))

    pSTMTS = ZeroOrMore(pSTMT)
    pSTMTS.setParseAction(lambda result: [result])

    def mkBlock (decls,stmts):
        bindings = [ (n,ERefCell(expr)) for (n,expr) in decls ]
        return ELet(bindings,EDo(stmts))
        
    pSTMT_BLOCK = "{" + pDECLS + pSTMTS + "}"
    pSTMT_BLOCK.setParseAction(lambda result: mkBlock(result[1],result[2]))

    pSTRING_OPERS = Keyword("len") | Keyword("substring") | Keyword("concat") | Keyword("startswith") | Keyword("endswith") | Keyword("lower") | Keyword("upper")
    pSTRING_OPERS.setParseAction(lambda result: result)

    pSTRING_OPER = pSTRING_OPERS + pEXPR + pEXPRS + ";"
    pSTRING_OPER.setParseAction(lambda result: string_operation(result[0], result[1], result[2]))

    pSTMT << ( pSTRING_OPER | pSTMT_IF_1 | pSTMT_IF_2 | pSTMT_WHILE | pSTMT_PRINT | pSTMT_UPDATE | pSTMT_UPDATE_ARRAY | pSTMT_BLOCK | pFOR | pPROD_CALL)

    # can't attach a parse action to pSTMT because of recursion, so let's duplicate the parser
    pTOP_STMT = pSTMT.copy()
    pTOP_STMT.setParseAction(lambda result: {"result":"statement",
                                             "stmt":result[0]})

    pTOP_DECL = pDECL.copy()
    pTOP_DECL.setParseAction(lambda result: {"result":"declaration",
                                             "decl":result[0]})

    pABSTRACT = "#abs" + pSTMT
    pABSTRACT.setParseAction(lambda result: {"result":"abstract",
                                             "stmt":result[1]})

    pQUIT = Keyword("#quit")
    pQUIT.setParseAction(lambda result: {"result":"quit"})
    
    pTOP = (pQUIT | pABSTRACT | pTOP_DECL | pTOP_STMT )

    result = pTOP.parseString(input)[0]
    return result    # the first element of the result is the expression

def printR(result):
    #print result
    return result[0]

def string_operation(operation, name, exprs):
    prim_args = [name]
    prim_args.extend(exprs)

    if operation == "len":
        return EPrimCall(oper_str_length, [name])
    elif operation == "substring":
        print prim_args
        return EPrimCall(oper_substring, prim_args)
    elif operation == "concat":
        return EPrimCall(oper_concat, prim_args)
    elif operation == "startswith":
        return EPrimCall(oper_startswith, prim_args)
    elif operation == "endswith":
        return EPrimCall(oper_endswith, prim_args)
    elif operation == "lower":
        return EPrimCall(oper_lower, [name])
    elif operation == "upper":
        return EPrimCall(oper_upper, [name])

def shell_imp ():
    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Homework 6 - Imp Language"
    print "#quit to quit, #abs to see abstract representation"
    env = initial_env_imp()

        
    while True:
        inp = raw_input("imp> ")

        try:
            result = parse_imp(inp)

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