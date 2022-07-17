
class Dog:
    def __init__(self, breed, origin, tail):
        self.breed = breed
        self.origin = origin
        self.tail = tail

    def bark(self):
        if self.breed == 'Doberman':
            return "Bow"
        else:
            return "Bow Bow Bow"