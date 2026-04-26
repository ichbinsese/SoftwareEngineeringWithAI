import xml.etree.ElementTree as ET

low_level_requirements = "Low Level Requirements Example.xml"
high_level_requirements = "High Level Requirements Example.xml"

header_string =       "# Software Requirement Specification\n"

high_level_string =   "## High Level Requirements\n"

low_level_string =    "## Low Level Requirements\n"

functional_string =   "### Functional\n"

non_functional_string="### Non Functional\n"

category_string =     "#### {Category}\n"

identifier_string =   "##### {ID} {Name}\n"

depends_on_string =  ("    Depends On:\n"
                      "        {Depends_On}\n")

refines_string =     ("    Refines:\n"
                      "        {Refines}\n")

content_string =     "{Content}\n"



srs = ""
srs += header_string

root = ET.parse(low_level_requirements).getroot()
for requirements in root:
    print(requirements.text)