from penn import directory, dining, registrar, Map
from os import getenv

din = dining.Dining(getenv("DIN_USERNAME"), getenv("DIN_PASSWORD"))
reg = registrar.Registrar(getenv("REG_USERNAME"), getenv("REG_PASSWORD"))
penn_dir = directory.Directory(getenv("DIR_USERNAME"), getenv("DIR_PASSWORD"))
map_search = Map(getenv("NEM_USERNAME"), getenv("NEM_PASSWORD"))
