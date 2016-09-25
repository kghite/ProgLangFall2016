############################################################
# HOMEWORK 2
#
# Team members: Andrew Deaver, Katie Hite
#
# Emails: Andrew.Deaver@students.olin.edu, Kathryn.Hite@students.olin.edu
#
# Remarks:
#



#
# Expressions
#

class Exp (object):
    pass



class EInteger (Exp):
    # Integer literal

    def __init__ (self,i):
        self._integer = i

    def __str__ (self):
        return "EInteger({})".format(self._integer)

    def eval (self,prim_dict, fun_dict):
        return VInteger(self._integer)

    def substitute (self,id,new_e):
        return self


class EBoolean (Exp):
    # Boolean literal

    def __init__ (self,b):
        self._boolean = b

    def __str__ (self):
        return "EBoolean({})".format(self._boolean)

    def eval (self,prim_dict, fun_dict):
        return VBoolean(self._boolean)

    def substitute (self,id,new_e):
        return self


class EPrimCall (Exp):

    def __init__ (self,name,es):
        self._name = name
        self._exps = es

    def __str__ (self):
        return "EPrimCall({},[{}])".format(self._name,",".join([ str(e) for e in self._exps]))

    def eval (self,prim_dict, fun_dict):
        vs = [ e.eval(prim_dict, fun_dict) for e in self._exps ]
        return apply(prim_dict[self._name],vs)

    def substitute (self,id,new_e):
        new_es = [ e.substitute(id,new_e) for e in self._exps]
        return EPrimCall(self._name,new_es)

class ECall (Exp):

    def __init__(self, name, es):
        self._name = name
        self._exps = es

    def __str__ (self):
        return "ECall({},[{}])".format(self._name,",".join([ str(e) for e in self._exps]))

    def eval (self,prim_dict, fun_dict):
        func = fun_dict[self._name]
        if(len(func["params"]) == len(self._exps)):
            if(len(func["params"]) >= 1):
                new_e = func["body"].substitute(EId(func["params"][0]), self._exps[0].eval(prim_dict, fun_dict))
                for i in range(1, len(func["params"])):
                    new_e = new_e.substitute(EId(func["params"][i]), self._exps[i].eval(prim_dict, fun_dict))
                return new_e.eval(prim_dict, fun_dict)
            return VInteger(5)
            #return func["body"].eval(prim_dict, fun_dict)
        else:
            raise Exception ("Runtime error: parameter length mismatch")

    def substitute (self, id, new_e):
        new_es = [ e.substitute(id,new_e) for e in self._exps]
        return ECall(self._name,new_es)

class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self,prim_dict, fun_dict):
        v = self._cond.eval(prim_dict, fun_dict)
        if v.type != "boolean":
            raise Exception ("Runtime error: condition not a Boolean")
        if v.value:
            return self._then.eval(prim_dict, fun_dict)
        else:
            return self._else.eval(prim_dict, fun_dict)

    def substitute (self,id,new_e):
        return EIf(self._cond.substitute(id,new_e),
                   self._then.substitute(id,new_e),
                   self._else.substitute(id,new_e))


class ELet (Exp):
    # local binding

    def __init__ (self,bindings,e2):
        self._bindings = bindings
        self._e2 = e2

    def __str__ (self):
        return "ELet([{}],{})".format(self._bindings,self._e2)

    def eval (self,prim_dict, fun_dict):
        if(len(self._bindings) > 0):
            new_e2 = self._e2.substitute(self._bindings[0][0],self._bindings[0][1])
            for i in range(1, len(self._bindings)):
                new_e2 = new_e2.substitute(self._bindings[i][0],self._bindings[i][1])
            return new_e2.eval(prim_dict, fun_dict)
        return self._e2.eval(prim_dict, fun_dict)

    def substitute (self,id,new_e):
        encountered = False

        for i in range(len(self._bindings)):
            self._bindings[i] = (self._bindings[i][0], self._bindings[i][1].substitute(id, new_e))
            
            if self._bindings[i][0]._id == id._id:
                encountered = True

        if not encountered:
            self._bindings.append((id, new_e))

        return self

class ELetS (Exp):
    # local binding

    def __init__ (self,bindings,e2):
        self._bindings = bindings
        self._e2 = e2

    def __str__ (self):
        return "ELetS([{}],{})".format(self._bindings,self._e2)

    def eval (self,prim_dict, fun_dict):
        n_let = None 
        for i in range(len(self._bindings)-1, -1, -1):
            n_bindings = [self._bindings[i]]
            if i == len(self._bindings)-1:
                n_let = ELet(n_bindings, self._e2)
            else:
                n_let = ELet(n_bindings, n_let)
        return n_let.eval(prim_dict, fun_dict)

    def substitute (self,id,new_e):
        self._bindings[0] = (self._bindings[0][0], self._bindings[0][1].substitute(id, new_e))
        return self

class ELetV (Exp):
    # local binding

    def __init__ (self,id,e1,e2):
        self._id = id
        self._e1 = e1
        self._e2 = e2

    def __str__ (self):
        return "ELet({},{},{})".format(self._id, self._e1,self._e2)

    def eval (self,prim_dict, fun_dict):
        v = self._e1.eval(prim_dict, fun_dict)
        self._e2.substitute(self._id, v)
        return self._e2.eval(prim_dict, fun_dict)

    def substitute (self,id,new_e):
        if id == self._id:
            return ELetV(self._id,
                        self._e1.substitute(id,new_e),
                        self._e2)
        return ELetV(self._id,
                    self._e1.substitute(id,new_e),
                    self._e2.substitute(id,new_e))


class EId (Exp):
    # identifier

    def __init__ (self,id):
        self._id = id
        self._val = VNull()

    def __str__ (self):
        if type(self._val) == VNull:
            return "EId({})".format(self._id)
        return self._val.__str__()

    def eval (self,prim_dict, fun_dict):
        if self._val.__class__.__bases__[0] == Exp:
            self._val = self._val.eval(prim_dict, fun_dict)
        return self._val

    def substitute (self,id,new_e):
        if id._id == self._id:
            self._val = new_e
        return self

class ENull (Exp):

    def __str__ (self):
        return "ENull"

    def eval (self, prim_dict, fun_dict):
        return VNull()

    def substitute(self):
        return ENull()
    
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

class VBoolean (Value):
    # Value representation of Booleans
    def __init__ (self,b):
        self.value = b
        self.type = "boolean"

class VNull (Value):

    def __init__ (self):
        self.type = "null"



# Primitive operations

def oper_plus (v1,v2): 
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value + v2.value)
    elif v1.type == "null" or v2.type == "null":
        return VInteger(lift(v1) + lift(v2))
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_minus (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value - v2.value)
    elif v1.type == "null" or v2.type == "null":
        return VInteger(lift(v1) - lift(v2))
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_times (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value * v2.value)
    elif v1.type == "null" or v2.type == "null":
        return VInteger(lift(v1) * lift(v2))
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_zero (v1):
       if v1.type == "integer":
           return VBoolean(v1.value==0)
       raise Exception ("Runtime error: type error in zero?")

# Initial primitives dictionary

INITIAL_PRIM_DICT = {
    "+": oper_plus,
    "*": oper_times,
    "-": oper_minus,
    "zero?": oper_zero
}

FUN_DICT = {
      "square": {"params":["x"],
                 "body":EPrimCall("*",[EId("x"),EId("x")])},
      "=": {"params":["x","y"],
            "body":EPrimCall("zero?",[EPrimCall("-",[EId("x"),EId("y")])])},
      "+1": {"params":["x"],
             "body":EPrimCall("+",[EId("x"),EInteger(1)])},
      "sum_from_to": {"params":["s","e"],
                      "body":EIf(ECall("=",[EId("s"),EId("e")]),
                                 EId("s"),
                                 EPrimCall("+",[EId("s"),
                                                ECall("sum_from_to",[ECall("+1",[EId("s")]),
                                                                     EId("e")])]))}
    }

# helper functions
def lift(value):
    if(value.type == "integer"):
        return value.value
    else:
        return 0