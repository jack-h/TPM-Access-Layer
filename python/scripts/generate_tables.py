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

# Skeleton code for bit register page
bit_html = html

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

    body = ""
    bit_body = ""
    table = """<table><tr>
               <th><center>ID</center></th><th><center>Address</center></th>
               <th><center>Description</center></th><th><center>Mask</center></th>
               <th><center>Permission</center></th></tr>"""

    # Loop over devices
    for device in root:

        if len(root) > 1:
            body += "<p>Device: %s</p>%s" % (device.tag, body)
        else:
            body += table

        # Loop over components:
        for component in device:

            # Include a "header" per component
            body += '<tr><th colspan="5"><center>Component %s</center></th></tr>' % component.attrib['id']

            # Loop over registers
            for register in component:
                # Check whether register contains bit components
                if len(list(register)) > 0:
                    # Create bit table
                    bit_body += '<a name="%s"></a>' % register.attrib['id']
                    bit_body += table
                    bit_body += '<tr><th colspan="5"><center>Register %s</center></th></tr>' % register.attrib['id']

                    for bit in register:
                        print bit.attrib
                        bit_body += "<tr>"
                        bit_body += "<td>%s</td>" % bit.attrib['id']
                        bit_body += "<td>-</td>"
                        bit_body += "<td>%s</td>" % bit.attrib['description']

                        if 'mask' in bit.attrib.keys():
                            bit_body += "<td>%s</td>" % bit.attrib['mask']     
                        else:
                            bit_body += "<td>-</td>"

                        if 'permission' in bit.attrib.keys():
                            bit_body += "<td>%s</td>" % bit.attrib['permission']
                        else:
                            bit_body += "<td>-</td>"
                    bit_body += "<br/><br/></table>"

                # Populate register 
                body += "<tr>"
                if len(list(register)) > 0:
                    body += "<td><a href=bit_table.html#%s/>%s</td>" % (register.attrib['id'], register.attrib['id'])
                else:
                    body += "<td>%s</td>" % register.attrib['id']
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

                # Loop over bits
                for bit in register:
                    pass
        
            # End of table
        body += "</table>"

    # Write html file
    with open("table.html", "w") as f:
        f.write(html % body)

    # Write bit html file
    with open("bit_table.html", "w") as f:
        f.write(html % bit_body)

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
