
class Entity:

    def __init__(self, type, txt, start, end):
        self.value = txt
        self.start=start
        self.idx = -1
        self.type=type
        self.end=end
    def tojson(self):
        return {"value": self.value, "type": self.type, "start": self.start, "end": self.end}


class Entities(list):

    def addEntity(self, entity):
        if self.containsType('Employee') and entity.type=='Employee':
            entity.type='Name'

        self.append(entity)

    def print(self):
        print('--------------')
        for t in self:
            print(t.type+" :   "+ t.value)
    def containsEntity(self, entity):
        for t in self:
            if t.type==entity.type and t.value==entity.value:
                return True
        return False

    def containsType(self, type):
        for t in self:
            if t.type==type:
                return True
        return False

    def getValue(self, type):
        for t in self:
            if t.type == type:
                return t.value
        return None

    def toJson(self):
        return [e.tojson() for e in self]