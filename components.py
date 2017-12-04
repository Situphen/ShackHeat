

class Material(object):
    """
        Represent a material with its thickness and its thermal conductivity
    """

    def __init__(self, thermal_conductivity=None, thickness=None):
        """
            :param thermal_conductivity: thermal conductivity in SI units, must be positive
            :param thickness: thickness in SI units, must be strictly positive
        """

        self.parent = None
        self.thermal_conductivity = thermal_conductivity
        self.thickness = thickness

    def calculate_thermal_conductivity_insulance(self):
        """
            Calculate the thermal conductivity insulance

            :returns: the thermal conductivity insulance in SI units
        """

        return self.thickness / self.thermal_conductivity

    def modify(self, variable, value):
        """
            Modify a variable of the material

            :param variable: the variable to modify
            :param value: the new value of the variable
        """

        self.__dict__[variable] = value


class MaterialCollection(object):
    """
        Represent a collection of overlaid material with the same surface

        Warning! It shouldn't be accessed directly
    """

    def __init__(self, materials=[]):
        """
            :param materials: list of Material objects
            :param surface: surface of the collection in SI units, must be strictly positive
        """

        self.parent = None
        self.surface = None

        self.materials = []
        for material in materials:
            self.add(material)

    def calculate_thermal_conductivity_insulance(self):
        """
            Calculate the thermal conductivity insulance

            :returns: thermal conductivity insulance in SI units
        """

        thermal_conductivity_insulance = 0
        for material in self.materials:
            thermal_conductivity_insulance += material.calculate_thermal_conductivity_insulance()
        return thermal_conductivity_insulance

    def calculate_thermal_insulance(self):
        """
            Calculate the thermal insulance (with conductivity and convection)

            :returns: thermal insulance in SI units
        """

        thermal_conductivity_insulance = self.calculate_thermal_conductivity_insulance()
        thermal_inside_convection_insulance = 1 / 10
        thermal_outside_convection_insulance = 1 / 80

        return thermal_conductivity_insulance + thermal_inside_convection_insulance + thermal_outside_convection_insulance

    def calculate_flux_surface(self, temperature_variation=0):
        """
            Calculate the thermal flux by surface unit

            :param temperature_variation: absolute difference between inside and outsite temperatures, must be strictly positive
            :returns: thermal flux by surface unit in SI units
        """

        return temperature_variation / self.calculate_thermal_insulance()

    def calculate_flux(self, temperature_variation=0):
        """
            Calculate the thermal flux

            :param temperature_variation: absolute difference between inside and outsite temperatures, must be strictly positive
            :returns: thermal flux in SI units
        """

        return self.calculate_flux_surface(temperature_variation) * self.surface

    def add(self, child):
        """
            Add a material to the collection

            :param child: a Material object
        """

        self.materials.append(child)
        child.parent = self

    def remove(self, child):
        """
            Remove a material from the collection

            :param child: a Material object
        """

        self.materials.remove(child)
        child.parent = None


class Opening(MaterialCollection):
    """
        Represent an opening, a material collection with the surface defined
    """

    def __init__(self, surface=None):
        super().__init__()
        self.surface = surface

    def modify(self, variable, value):
        """
            Modify a variable of the opening

            :param variable: the variable to modify
            :param value: the new value of the variable
        """

        self.__dict__[variable] = value


class Roof(MaterialCollection):
    """
        Represent the roof of a building
    """

    def calculate_flux(self, *args):
        self.surface = self.parent.width * self.parent.length

        return super().calculate_flux(args)


class Floor(MaterialCollection):
    """
        Represent the floor of a building
    """

    def calculate_thermal_insulance(self):
        thermal_conductivity_insulance = self.calculate_thermal_conductivity_insulance()
        thermal_inside_convection_insulance = 1 / 10
        return thermal_conductivity_insulance + thermal_inside_convection_insulance

    def calculate_flux(self, temperature_variation=0):
        self.surface = self.parent.width * self.parent.length

        return super().calculate_flux(temperature_variation)


class Wall(MaterialCollection):
    """
        Represent the wall of a building
    """
    pass


class Side(object):
    """
        Represent the side of a building which is the wall and all the openings
    """

    def __init__(self, height=None, wall=None, openings=[]):
        self.parent = None
        self.height = height

        self.wall = None
        if wall:
            self.add(wall)

        self.openings = []
        for opening in openings:
            self.add(opening)

    def calculate_flux(self, temperature_variation=0):
        """
            Calculate the thermal flux

            :param temperature_variation: absolute difference between inside and outsite temperatures, must be strictly positive
            :returns: thermal flux in SI units
        """

        openings_surfaces = [opening.surface for opening in self.openings]
        self.wall.surface = 2*self.height*(self.parent.width+self.parent.length) - sum(openings_surfaces)

        flux = 0
        flux += self.wall.calculate_flux(temperature_variation)
        for opening in self.openings:
            flux += opening.calculate_flux(temperature_variation)
        return flux

    def add(self, child):
        """
            Add the wall or an opening to the side

            :param child: a Wall or an Opening object
        """
        if isinstance(child, Wall):
            self.wall = child
            child.parent = self
        elif isinstance(child, Opening):
            self.openings.append(child)
            child.parent = self

    def remove(self, child):
        """
            Remove the wall or an opening from the side

            :param child: a Wall or an Opening object
        """
        if isinstance(child, Wall):
            self.wall = None
            child.parent = None
        elif isinstance(child, Opening):
            self.openings.remove(child)
            child.parent = None

    def modify(self, variable, value):
        """
            Modify a variable of the side

            :param variable: the variable to modify
            :param value: the new value of the variable
        """

        self.__dict__[variable] = value


class Building(object):
    """
        Represent a building with a roof, a floor and a side
    """

    def __init__(self, width=None, length=None, roof=None, side=None, floor=None):
        self.width = width
        self.length = length

        self.roof = None
        if roof:
            self.add(roof)

        self.side = None
        if side:
            self.add(side)

        self.floor = None
        if floor:
            self.add(floor)

    def calculate_flux(self, temperature_inside=20, temperature_outside=10, temperature_underground=15):
        """
            Calculate the thermal flux

            :param temperature_inside: temperature inside the building
            :param temperature_outside: temperature outside the building
            :param temperature_underground: temperature underground the building
            :returns: thermal flux in SI units
        """
        flux = 0

        temperature_between_in_and_out = abs(temperature_inside - temperature_outside)
        flux += self.roof.calculate_flux(temperature_between_in_and_out)
        flux += self.side.calculate_flux(temperature_between_in_and_out)

        temperature_between_in_and_underground = abs(temperature_inside - temperature_underground)
        flux += self.floor.calculate_flux(temperature_between_in_and_underground)

        return flux

    def add(self, child):
        """
            Add the roof, the side or the floor to the building

            :param child: a Roof, a Side or a Floor object
        """
        if isinstance(child, Roof):
            self.roof = child
            child.parent = self
        elif isinstance(child, Side):
            self.side = child
            child.parent = self
        elif isinstance(child, Floor):
            self.floor = child
            child.parent = self

    def remove(self, child):
        """
            Remove the roof, the side or the floor from the building

            :param child: a Roof, a Side or a Floor object
        """
        if isinstance(child, Roof):
            self.roof = None
            child.parent = None
        elif isinstance(child, Side):
            self.side = None
            child.parent = None
        elif isinstance(child, Floor):
            self.floor = None
            child.parent = None

    def modify(self, variable, value):
        """
            Modify a variable of the building

            :param variable: the variable to modify
            :param value: the new value of the variable
        """

        self.__dict__[variable] = value
