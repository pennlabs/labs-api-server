from penn import Transit, Directory, Dining, Registrar, Map
from os import getenv

din = Dining(getenv("DIN_USERNAME"), getenv("DIN_PASSWORD"))
reg = Registrar(getenv("REG_USERNAME"), getenv("REG_PASSWORD"))
penn_dir = Directory(getenv("DIR_USERNAME"), getenv("DIR_PASSWORD"))
map_search = Map(getenv("NEM_USERNAME"), getenv("NEM_PASSWORD"))
transit = Transit(getenv("TRANSIT_USERNAME"), getenv("TRANSIT_PASSWORD"))
