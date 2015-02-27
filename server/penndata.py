from penn import Transit, Directory, Dining, Registrar, Map
from os import getenv

din = Dining(getenv("DIN_USERNAME"), getenv("DIN_PASSWORD"))
reg = Registrar(getenv("REG_USERNAME"), getenv("REG_PASSWORD"))
penn_dir = Directory(getenv("DIR_USERNAME"), getenv("DIR_PASSWORD"))
map_search = Map(getenv("NEM_USERNAME"), getenv("NEM_PASSWORD"))
transit = Transit(getenv("TRANSIT_USERNAME"), getenv("TRANSIT_PASSWORD"))

depts = {
  "AAMW" : "Art & Arch of Med. World",
  "ACCT" : "Accounting",
  "AFRC" : "Africana Studies",
  "AFST" : "African Studies Program",
  "ALAN" : "Asian Languages",
  "AMCS" : "Applied Math & Computatnl Sci.",
  "ANAT" : "Anatomy",
  "ANCH" : "Ancient History",
  "ANEL" : "Ancient Near East Languages",
  "ANTH" : "Anthropology",
  "ARAB" : "Arabic",
  "ARCH" : "Architecture",
  "ARTH" : "Art History",
  "ASAM" : "Asian American Studies",
  "ASTR" : "Astronomy",
  "BCHE" : "Biochemistry (Undergrads)",
  "BE" : "Bioengineering",
  "BENG" : "Bengali",
  "BEPP" : "Business Econ & Public Policy",
  "BFMD" : "Benjamin Franklin Seminars-Med",
  "BIBB" : "Biological Basis of Behavior",
  "BIOE" : "Bioethics",
  "BIOL" : "Biology",
  "BIOM" : "Biomedical Studies",
  "BMB" : "Biochemistry & Molecular Biophy",
  "BSTA" : "Biostatistics",
  "CAMB" : "Cell and Molecular Biology",
  "CBE" : "Chemical & Biomolecular Engr",
  "CHEM" : "Chemistry",
  "CHIN" : "Chinese",
  "CINE" : "Cinema Studies",
  "CIS" : "Computer and Information Sci",
  "CIT" : "Computer and Information Tech",
  "CLST" : "Classical Studies",
  "COGS" : "Cognitive Science",
  "COLL" : "College",
  "COML" : "Comparative Literature",
  "COMM" : "Communications",
  "CPLN" : "City Planning",
  "CRIM" : "Criminology",
  "DEMG" : "Demography",
  "DORT" : "Orthodontics",
  "DOSP" : "Oral Surgery and Pharmacology",
  "DPED" : "Pediatric Dentistry",
  "DRST" : "Restorative Dentistry",
  "DTCH" : "Dutch",
  "DYNM" : "Organizational Dynamics",
  "EALC" : "East Asian Languages & Civilztn",
  "EAS" : "Engineering & Applied Science",
  "ECON" : "Economics",
  "EDUC" : "Education",
  "EEUR" : "East European",
  "ENGL" : "English",
  "ENGR" : "Engineering",
  "ENM" : "Engineering Mathematics",
  "ENVS" : "Environmental Studies",
  "EPID" : "Epidemiology",
  "ESE" : "Electric & Systems Engineering",
  "FNAR" : "Fine Arts",
  "FNCE" : "Finance",
  "FOLK" : "Folklore",
  "FREN" : "French",
  "FRSM" : "Non-Sas Freshman Seminar",
  "GAFL" : "Government Administration",
  "GAS" : "Graduate Arts & Sciences",
  "GCB" : "Genomics & Comp. Biology",
  "GEOL" : "Geology",
  "GREK" : "Greek",
  "GRMN" : "Germanic Languages",
  "GSWS" : "Gender,Sexuality & Women's Stud",
  "GUJR" : "Gujarati",
  "HCMG" : "Health Care Management",
  "HEBR" : "Hebrew",
  "HIND" : "Hindi",
  "HIST" : "History",
  "HPR" : "Health Policy Research",
  "HSOC" : "Health & Societies",
  "HSPV" : "Historic Preservation",
  "HSSC" : "History & Sociology of Science",
  "IMUN" : "Immunology",
  "INTG" : "Integrated Studies",
  "INTL" : "International Programs",
  "INTR" : "International Relations",
  "IPD" : "Integrated Product Design",
  "ITAL" : "Italian",
  "JPAN" : "Japanese",
  "JWST" : "Jewish Studies Program",
  "KORN" : "Korean",
  "LALS" : "Latin American & Latino Studies",
  "LARP" : "Landscape Arch & Regional Plan",
  "LATN" : "Latin",
  "LAW" : "Law",
  "LGIC" : "Logic, Information and Comp.",
  "LGST" : "Legal Studies & Business Ethics",
  "LING" : "Linguistics",
  "LSMP" : "Life Sciences Management Prog",
  "MAPP" : "Master of Applied Positive Psyc",
  "MATH" : "Mathematics",
  "MEAM" : "Mech Engr and Applied Mech",
  "MED" : "Medical",
  "MGEC" : "Management of Economics",
  "MGMT" : "Management",
  "MKTG" : "Marketing",
  "MLA" : "Master of Liberal Arts Program",
  "MLYM" : "Malayalam",
  "MMP" : "Master of Medical Physics",
  "MSCI" : "Military Science",
  "MSE" : "Materials Science and Engineer",
  "MSSP" : "Social Policy",
  "MTR" : "Mstr Sci Transltl Research",
  "MUSA" : "Master of Urban Spatial Analyt",
  "MUSC" : "Music",
  "NANO" : "Nanotechnology",
  "NELC" : "Near Eastern Languages & Civlzt",
  "NETS" : "Networked and Social Systems",
  "NGG" : "Neuroscience",
  "NPLD" : "Nonprofit Leadership",
  "NSCI" : "Naval Science",
  "NURS" : "Nursing",
  "OPIM" : "Operations and Information Mgmt",
  "PERS" : "Persian",
  "PHIL" : "Philosophy",
  "PHRM" : "Pharmacology",
  "PHYS" : "Physics",
  "PPE" : "Philosophy, Politics, Economics",
  "PRTG" : "Portuguese",
  "PSCI" : "Political Science",
  "PSYC" : "Psychology",
  "PUBH" : "Public Health Studies",
  "PUNJ" : "Punjabi",
  "REAL" : "Real Estate",
  "RELS" : "Religious Studies",
  "ROML" : "Romance Languages",
  "RUSS" : "Russian",
  "SAST" : "South Asia Studies",
  "SCND" : "Scandinavian",
  "SKRT" : "Sanskrit",
  "SLAV" : "Slavic",
  "SOCI" : "Sociology",
  "SPAN" : "Spanish",
  "STAT" : "Statistics",
  "STSC" : "Science, Technology & Society",
  "SWRK" : "Social Work",
  "TAML" : "Tamil",
  "TCOM" : "Telecommunications & Networking",
  "TELU" : "Telugu",
  "THAR" : "Theatre Arts",
  "TURK" : "Turkish",
  "URBS" : "Urban Studies",
  "URDU" : "Urdu",
  "VCSN" : "Clinical Studies - Nbc Elect",
  "VCSP" : "Clinical Studies - Phila Elect",
  "VIPR" : "Viper",
  "VISR" : "Vet School Ind Study & Research",
  "VLST" : "Visual Studies",
  "VMED" : "Csp/Csn Medicine Courses",
  "WH" : "Wharton Undergraduate",
  "WHCP" : "Wharton Communication Pgm",
  "WHG" : "Wharton Graduate",
  "WRIT" : "Writing Program",
  "YDSH" : "Yiddish"
}