import xml.etree.ElementTree as ET

def update_url(file_path):
    url_list = ["https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-snapshot-aws-local",
                "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-thirdparty-local",
                "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-snapshot-aws-local",
                "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget.org"]
    with open(file_path) as file:
        x = ET.fromstring(file.read())
        print(x)
        for package in x:
            tag_name = package.tag
            if 'packagesource' in tag_name.lower():
                # package.findall('add')
                count = 0
                for p in package.findall('add'):
                    p.attrib['value'] =url_list[count]
                    count += 1
                    
        tree = ET.ElementTree(x)
        tree.write('to_replace_2.xml')



def target_xml(root):
    url = "https://artifactory.actimize.cloud/artifactory/api/nuget/nuget-release-aws-local"
    for package in root.iter():
            tag_name = package.tag
            
            if 'packagesource' in tag_name.lower():
                package.attrib['Include'] = url
                    
    
    tree = ET.ElementTree(root)
    tree.write("./target.xml", encoding = "utf-8", xml_declaration = True) 