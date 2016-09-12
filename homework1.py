############################################################
# HOMEWORK 1
#
# Team members: Andrew Deaver, Kathryn Hite
#
# Emails: andrew.deaver@students.olin.edu, kathryn.hite@students.olin.edu
#
# Remarks: Woohoo!!Wootwoot!Whipeeeeeeee!!
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

    def eval (self):
        return VInteger(self._integer)


class EBoolean (Exp):
    # Boolean literal

    def __init__ (self,b):
        self._boolean = b

    def __str__ (self):
        return "EBoolean({})".format(self._boolean)

    def eval (self):
        return VBoolean(self._boolean)


class EPlus (Exp):
    # Addition operation

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "EPlus({},{})".format(self._exp1,self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()

        if v1.type == "integer" and v2.type == "integer":
            return VInteger(v1.value + v2.value)

        if v1.type == "vector" and v2.type == "vector":
            # We're assuming the vectors are of equal length for now
            if v1.length > 0:
                if v1.get(0).eval().type == "integer" and v2.get(0).eval().type == "integer":
                    return VVector([EInteger(v1.get(n).eval().value + v2.get(n).eval().value) for n in range(v1.length)])
                if v1.get(0).eval().type == "rational" and v2.get(0).eval().type == "rational":
                    l = []
                    for n in range(v1.length):
                        val1 = v1.get(n).eval()
                        val2 = v2.get(n).eval()
                        num = EInteger(val1.numer * val2.denom + val2.numer * val1.denom)
                        den = EInteger(val1.denom * val2.denom)
                        l.append(EDiv(num, den))
                    return VVector(l)
                if (v1.get(0).eval().type == "rational" and v2.get(0).eval().type == "integer") or (v1.get(0).eval().type == "integer" and v2.get(0).eval().type == "rational"):
                    if(v1.get(0).eval().type == "rational"):
                        vec1 = v1
                        vec2 = VVector([EDiv(EInteger(v2.get(0).eval().value), EInteger(1)) for n in range(v2.length)])
                    else:
                        vec1 = VVector([EDiv(EInteger(v1.get(0).eval().value), EInteger(1)) for n in range(v1.length)])
                        vec2 = v2

                    l = []
                    for n in range(vec1.length):
                        val1 = vec1.get(n).eval()
                        val2 = vec2.get(n).eval()
                        num = EInteger(val1.numer * val2.denom + val2.numer * val1.denom)
                        den = EInteger(val1.denom * val2.denom)
                        l.append(EDiv(num, den))
                    return VVector(l)
            else:
                return VVector([])

        if v1.type == "rational" and v2.type == "rational":
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1*d2 + n2*d1), EInteger(d1*d2))

        if v1.type == "integer" and v2.type == "rational":
            v1 = EDiv(EInteger(v1.value), EInteger(1)).eval()
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1*d2 + n2*d1), EInteger(d1*d2))

        if v1.type == "rational" and v2.type == "integer":
            v2 = EDiv(EInteger(v1.value), EInteger(1)).eval()
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1*d2 + n2*d1), EInteger(d1*d2))

        raise Exception ("Runtime error: trying to add non-numbers")


class EMinus (Exp):
    # Subtraction operation

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "EMinus({},{})".format(self._exp1,self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()

        if v1.type == "integer" and v2.type == "integer":
            return VInteger(v1.value - v2.value)

        if v1.type == "vector" and v2.type == "vector":
            # We're assuming the vectors are of equal length for now
            if v1.length > 0:
                if v1.get(0).eval().type == "integer" and v2.get(0).eval().type == "integer":
                    return VVector([EInteger(v1.get(n).eval().value - v2.get(n).eval().value) for n in range(v1.length)])
                if v1.get(0).eval().type == "rational" and v2.get(0).eval().type == "rational":
                    l = []
                    for n in range(v1.length):
                        val1 = v1.get(n).eval()
                        val2 = v2.get(n).eval()
                        num = EInteger(val1.numer * val2.denom - val2.numer * val1.denom)
                        den = EInteger(val1.denom * val2.denom)
                        l.append(EDiv(num, den))
                    return VVector(l)
                if (v1.get(0).eval().type == "rational" and v2.get(0).eval().type == "integer") or (v1.get(0).eval().type == "integer" and v2.get(0).eval().type == "rational"):
                    if(v1.get(0).eval().type == "rational"):
                        vec1 = v1
                        vec2 = VVector([EDiv(EInteger(v2.get(0).eval().value), EInteger(1)) for n in range(v2.length)])
                    else:
                        vec1 = VVector([EDiv(EInteger(v1.get(0).eval().value), EInteger(1)) for n in range(v1.length)])
                        vec2 = v2
                    l = []
                    for n in range(vec1.length):
                        val1 = vec1.get(n).eval()
                        val2 = vec2.get(n).eval()
                        num = EInteger(val1.numer * val2.denom - val2.numer * val1.denom)
                        den = EInteger(val1.denom * val2.denom)
                        l.append(EDiv(num, den))
                    return VVector(l)
            else:
                return VVector([])

        if v1.type == "rational" and v2.type == "rational":
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1*d2 - n2*d1), EInteger(d1*d2))

        if v1.type == "integer" and v2.type == "rational":
            v1 = EDiv(EInteger(v1.value), EInteger(1)).eval()
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1*d2 - n2*d1), EInteger(d1*d2))

        if v1.type == "rational" and v2.type == "integer":
            v2 = EDiv(EInteger(v1.value), EInteger(1)).eval()
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1*d2 - n2*d1), EInteger(d1*d2))

        raise Exception ("Runtime error: trying to subtract non-numbers")


class ETimes (Exp):
    # Multiplication operation

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "ETimes({},{})".format(self._exp1,self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()

        if v1.type == "integer" and v2.type == "integer":
            return VInteger(v1.value * v2.value)

        if v1.type == "vector" and v2.type == "vector":
            # We're assuming the vectors are of equal length for now
            if v1.length > 0:
                if v1.get(0).eval().type == "integer" and v2.get(0).eval().type == "integer":
                    return VInteger(sum([v1.get(n).eval().value * v2.get(n).eval().value for n in range(v1.length)]))
                if v1.get(0).eval().type == "rational" and v2.get(0).eval().type == "rational":
                    current = EInteger(0)
                    for n in range(v1.length):
                        val1 = v1.get(n).eval()
                        val2 = v2.get(n).eval()
                        num = EInteger(val1.numer * val2.numer)
                        den = EInteger(val1.denom * val2.denom)
                        add = EPlus(current, EDiv(num, den)).eval()
                        current = EDiv(add.numer, add.denom)
                    return current
                if (v1.get(0).eval().type == "rational" and v2.get(0).eval().type == "integer") or (v1.get(0).eval().type == "integer" and v2.get(0).eval().type == "rational"):
                    if(v1.get(0).eval().type == "rational"):
                        vec1 = v1
                        vec2 = VVector([EDiv(EInteger(v2.get(0).eval().value), EInteger(1)) for n in range(v2.length)])
                    else:
                        vec1 = VVector([EDiv(EInteger(v1.get(0).eval().value), EInteger(1)) for n in range(v1.length)])
                        vec2 = v2
 
                    current = EInteger(0)
                    for n in range(vec1.length):
                        val1 = vec1.get(n).eval()
                        val2 = vec2.get(n).eval()
                        num = EInteger(val1.numer * val2.numer)
                        den = EInteger(val1.denom * val2.denom)
                        add = EPlus(current, EDiv(num, den)).eval()
                        current = EDiv(add.numer, add.denom)
                    return current
            else:
                return VInteger(0)

        if v1.type == "rational" and v2.type == "rational":
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1 * n2), EInteger(d1 * d2))

        if v1.type == "integer" and v2.type == "rational":
            v1 = EDiv(EInteger(v1.value), EInteger(1)).eval()
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1 * n2), EInteger(d1 * d2))

        if v1.type == "rational" and v2.type == "integer":
            v2 = EDiv(EInteger(v1.value), EInteger(1)).eval()
            n1 = v1.numer
            n2 = v2.numer
            d1 = v1.denom
            d2 = v2.denom
            return VRational(EInteger(n1 * n2), EInteger(d1 * d2))

        raise Exception ("Runtime error: trying to multiply non-numbers")


class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self):
        v = self._cond.eval()
        if v.type != "boolean":
            raise Exception ("Runtime error: condition not a Boolean")
        if v.value:
            return self._then.eval()
        else:
            return self._else.eval()

class EIsZero (Exp):
    # Zero test expression

    def __init__ (self,e1):
        self._exp1 = e1

    def __str__ (self):
        return "EIsZero({})".format(self._exp1)

    def eval (self):
        v = self._exp1.eval()
        if v.type != "integer":
            raise Exception ("Runtime error: non-integer input")
        if v.value == 0:
            return VBoolean(True)
        else:
            return VBoolean(False)

class EAnd (Exp):
    # And test expression

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "EAnd({},{})".format(self._exp1, self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()

        if v1.type == "boolean" and v2.type == "boolean":
            return VBoolean(v1.value and v2.value)
        elif v1.type == "vector" and v2.type == "vector":
            if v1.length > 0:
                if v1.get(0).eval().type == "boolean" and v2.get(0).eval().type == "boolean":
                    return VVector([EBoolean(v1.get(n).eval().value and v2.get(n).eval().value for n in range(v1.length))])
                else:
                    raise Exception("Runtime error: list of non-boolean types")
            else:
                return VVector([])
        else:
            raise Exception("Runtime error: at least one input was not boolean")

class EOr (Exp):
    # Or test expression

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "EOr({},{})".format(self._exp1, self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()

        if v1.type == "boolean" and v2.type == "boolean":
            return VBoolean(v1.value or v2.value)
        elif v1.type == "vector" and v2.type == "vector":
            if v1.length > 0:
                if v1.get(0).eval().type == "boolean" and v2.get(0).eval().type == "boolean":
                    return VVector([EBoolean(v1.get(n).eval().value or v2.get(n).eval().value for n in range(v1.length))])
                else:
                    raise Exception("Runtime error: list of non-boolean types")
            else:
                return VVector([])
        else:
            raise Exception("Runtime error: at least one input was not boolean")

class ENot (Exp):
    # And test expression

    def __init__ (self,e):
        self._exp = e

    def __str__ (self):
        return "ENot({})".format(self._exp)

    def eval (self):
        v = self._exp.eval()

        if v.type == "boolean":
            return VBoolean(not v.value)
        elif v.type == "vector":
            if v.length > 0:
                if v.get(0).eval().type == "boolean":
                    return VVector([EBoolean(not v.get(n).eval().value for n in range(v.length))])
                else:
                    raise Exception("Runtime error: list of non-boolean types")
            else:
                return VVector([])
        else:
            raise Exception("Runtime error: input was not boolean")

class EVector (Exp):
    # Vector expression

    def __init__ (self, v):
        self._vector = v

    def __str__ (self):
        return "EVector({})".format(self._vector)

    def eval (self):
        v = self._vector

        # Check that all elements are of same type
        if len(v) > 1:
            t = type(v[0])
            for elem in v:
                if type(elem) != t:
                    raise Exception("Runtime error: list elements need to be of same type") 

        if type(v) == type([]):
            return VVector(v)
        else:
            raise Exception("Runtime error: input was not a list")

class EDiv (Exp):
    # Division expression

    def __init__ (self, e1, e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return ("EDiv({},{})").format(self._exp1, self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()

        if v1.type == "integer" and v2.type == "integer":
            return VRational(v1.value, v2.value)

        raise Exception ("Runtime error: Trying to divide non-integer values")



#
# Values
#

class Value (object):
    pass


class VInteger (Value):
    # Value representation of Integers
    def __init__ (self,i):
        self.value = i
        self.type = "integer"

class VBoolean (Value):
    # Value representation of Booleans
    def __init__ (self,b):
        self.value = b
        self.type = "boolean"

class VVector (Value):
    # Value representation of Vectors
    def __init__ (self, v):
        self.value = v
        self.type = "vector"
        self.length = len(v)

    def get (self, n):
        if n < 0 or n >= self.length:
            raise Exception("Runtime error: index out of bounds")
        else:
            return self.value[n]

class VRational (Value):
    # Value representation of Rational numbers
    def __init__ (self, n, d):
        self.numer = n
        self.denom = d
        self.type = "rational"