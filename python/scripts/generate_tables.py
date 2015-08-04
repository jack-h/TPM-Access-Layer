import xml.etree.ElementTree as et
import sys
import os

# Generate skeleton HTML code
html = """
<html>
<head>
<style>
table, th, td {
    border: 2px solid black;
    border-collapse:collapse;
}
th, td {
    padding: 8px;
}

th {
    text-align: left;
    background-color: #006699;
    color: white;
}

</style>
</head>
<body>%s</body>
</html>
"""

def generate_tables(filepath):
    """ Generate HTML tables from XML file
    :param filepath: Filepath to XML file """

    # Check if filepath exists
    if not os.path.exists(filepath):
        print "Invalid XML filepath %s" % filepath
        return

    # Parse XML file
    tree = et.parse(filepath)
    root = tree.getroot()

    # Loop over devices
    for device in root:

        # Loop over components:
        for component in device:

            # Include a "header" per component
            body = "<table><tr><th>Address</th><th>Description</th><th>Mask</th><th>Permission</th></tr>"
            print component.tag, component.attrib
            
            # Loop over registers
            for register in component:
                # Check that address exists
                if 'address' in register.attrib.keys():        
                    # Populate register 
                    body += "<tr>"
                    body += "<td>%s</td>" % register.attrib['address']
                    body += "<td>%s</td>" % register.attrib['description']
                    if 'mask' in register.attrib.keys():
                        body += "<td>%s</td>" % register.attrib['mask']     
                    else:
                        body += "<td>-</td>"
                    if 'permission' in register.attrib.keys():
                        body += "<td>%s</td>" % register.attrib['permission']
                    else:
                        body += "<td>-</td>"
                    body += "<tr>"

                    print register.tag, register.attrib

                # Loop over bits
                # Generate table per bit registet
                for bit in register:

                    print bit.tag, bit.attrib
        
            # End of table
            body += "</table>"

    # All done
    return html % body


if __name__ == "__main__":

#    if len(sys.argv) <= 1:
#        print "Xml file required as argument"

    # generate_tables(sys.argv[1])
    a = generate_tables("/home/lessju/Code/TPM-Access-Layer/python/scripts/xml_file.xml")
    f = open("output.html", 'w')
    f.write(a)
    f.close()
