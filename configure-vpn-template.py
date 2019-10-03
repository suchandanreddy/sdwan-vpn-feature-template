import requests
import sys
import json
import os
import click
import pprint
import time
import yaml
from jinja2 import Template


from requests.packages.urllib3.exceptions import InsecureRequestWarning

vmanage_host = os.environ.get("vmanage_host")
vmanage_port = os.environ.get("vmanage_port")
username = os.environ.get("username")
password = os.environ.get("password")
device_template_name = os.environ.get("device_template_name")


if vmanage_host is None or vmanage_port is None or username is None or password is None or device_template_name is None :
    print("For Windows Workstation, vManage details must be set via environment variables using below commands")
    print("set vmanage_host=198.18.1.10")
    print("set vmanage_port=443")
    print("set username=admin")
    print("set password=admin")
    print("set device_template_name=DC-vEdges")
    print("For MAC OSX Workstation, vManage details must be set via environment variables using below commands")
    print("export vmanage_host=198.18.1.10")
    print("export vmanage_port=443")
    print("export username=admin")
    print("export password=admin")
    print("export device_template_name=DC-vEdges")
    exit()

requests.packages.urllib3.disable_warnings()

class rest_api_lib:
    def __init__(self, vmanage_host,vmanage_port, username, password):
        self.vmanage_host = vmanage_host
        self.vmanage_port = vmanage_port
        self.session = {}
        self.login(self.vmanage_host, username, password)

    def login(self, vmanage_host, username, password):

        """Login to vmanage"""

        base_url = 'https://%s:%s/'%(self.vmanage_host, self.vmanage_port)

        login_action = '/j_security_check'

        #Format data for loginForm
        login_data = {'j_username' : username, 'j_password' : password}

        #Url for posting login data
        login_url = base_url + login_action
        url = base_url + login_url

        sess = requests.session()

        #If the vmanage has a certificate signed by a trusted authority change verify to True

        login_response = sess.post(url=login_url, data=login_data, verify=False)


        if b'<html>' in login_response.content:
            print ("Login Failed")
            sys.exit(0)

        self.session[vmanage_host] = sess

    def get_request(self, mount_point):
        """GET request"""
        url = "https://%s:%s/dataservice/%s"%(self.vmanage_host, self.vmanage_port, mount_point)

        response = self.session[self.vmanage_host].get(url, verify=False)

        return response

    def post_request(self, mount_point, payload, headers={'Content-type': 'application/json', 'Accept': 'application/json'}):
        """POST request"""
        url = "https://%s:%s/dataservice/%s"%(self.vmanage_host, self.vmanage_port, mount_point)

        response = self.session[self.vmanage_host].post(url=url, data=payload, headers=headers, verify=False)
        return response
    
    def put_request(self, mount_point, payload, headers={'Content-type': 'application/json', 'Accept': 'application/json'}):
        """POST request"""
        url = "https://%s:%s/dataservice/%s"%(self.vmanage_host, self.vmanage_port, mount_point)
        payload = json.dumps(payload)

        response = self.session[self.vmanage_host].put(url=url, data=payload, headers=headers, verify=False)
        return response


#Create session with vmanage

vmanage_session = rest_api_lib(vmanage_host, vmanage_port, username, password)

@click.group()
def cli():
    """Command line tool for deploying templates to CISCO SDWAN.
    """
    pass

@click.command()
@click.option("--input_yaml", help="ID of the  to detach")
def create_service_vpn(input_yaml):
    """create Service VPN feature template with Cisco SDWAN.
        Provide all template parameters and their values as arguments.
        Example command:
          ./vmanage_apis.py create-template --input_yaml=banner.yaml
    """
    click.secho("Creating feature template based on yaml file details\n")

    print("Loading Network Configuration Details from YAML File")
    with open(input_yaml) as f:
        config = yaml.safe_load(f.read())

    # Service VPN and OSPF Configuration

    with open("vpn-feature-template.j2") as f:
        service_vpn = Template(f.read())

    with open("vpn-interface-template.j2") as f:
        vpn_interface = Template(f.read())

    with open("ospf-template.j2") as f:
        ospf_config = Template(f.read())

    #Fetching list of device templates

    template_id_response = vmanage_session.get_request("template/device")

    if template_id_response.status_code == 200:
        items = template_id_response.json()['data']
        template_found=0
        print("\nFetching Template uuid of %s"%device_template_name)
        for item in items:
            if item['templateName'] == device_template_name:
                device_template_id = item['templateId']
                template_found=1
                break
        if template_found==0:
            print("\nDevice Template is not found")
            exit()
    else:
        print("\nError fetching list of templates")
        exit()

    #Fetching feature templates associated with Device template. 

    print("\nFetching feature templates associated with %s device template"%device_template_name)

    template_response = vmanage_session.get_request("template/device/object/%s"%(device_template_id))

    if template_response.status_code == 200:
        feature_template_ids=template_response.json()
    else:
        print("\nError fetching feature template ids")
        exit()
    
    #Creating Service VPN Template

    print("\nCreating Service VPN Template")

    service_vpn_payload = service_vpn.render(config=config)

    response = vmanage_session.post_request('template/feature/', service_vpn_payload)
    if response.status_code == 200:
        print("\nCreated service vpn template ID: ", response.json())
        service_vpn_template_id = response.json()['templateId']
    else:
        print("\nFailed creating service vpn template, error: ",response.text)

    #Creating VPN Interface Template

    print("\nCreating VPN Interface Template")

    vpn_interface_payload = vpn_interface.render(config=config)

    response = vmanage_session.post_request('template/feature/', vpn_interface_payload)
    if response.status_code == 200:
        print("\nCreated service vpn interface template ID: ", response.json())
        vpn_interface_template_id = response.json()['templateId']
    else:
        print("\nFailed creating service vpn interface template, error: ",response.text)
    
    #Creating OSPF Template

    print("\nCreating OSPF Template")

    ospf_config_payload = ospf_config.render(config=config)

    response = vmanage_session.post_request('template/feature/', ospf_config_payload)
    if response.status_code == 200:
        print("\nCreated OSPF feature template ID: ", response.json())
        ospf_template_id = response.json()['templateId']
    else:
        print("\nFailed creating OSPF feature template, error: ",response.text)

    #Edit Device Template

    service_vpn_templates = {
                "templateId": service_vpn_template_id,
                "templateType": "vpn-vedge",
                "subTemplates": [
                    {
                    "templateId": ospf_template_id,
                    "templateType": "ospf"
                    },
                    {
                    "templateId": vpn_interface_template_id,
                    "templateType": "vpn-vedge-interface"
                    }
                ]
                }

    #Temporary fix because vManage needs templates to be in specific order. 
    feature_template_ids["generalTemplates"].insert(9,service_vpn_templates)

    payload = {
               "templateId":device_template_id,"templateName":device_template_name,
               "templateDescription":feature_template_ids["templateDescription"],
               "deviceType":feature_template_ids["deviceType"],
               "configType":"template","factoryDefault":False,
               "policyId":feature_template_ids["policyId"],
               "featureTemplateUidRange":[],"connectionPreferenceRequired":True,
               "connectionPreference":True,"policyRequired":True,
               "generalTemplates":feature_template_ids["generalTemplates"],
               }

    device_template_edit_res = vmanage_session.put_request("template/device/%s"%device_template_id,payload)

    if device_template_edit_res.status_code == 200:
        items = device_template_edit_res.json()['data']['attachedDevices']
        device_uuid = list()
        for i in range(len(items)):
            device_uuid.append(items[i]['uuid'])
        template_pushid = device_template_edit_res.json()['data']['processId']
    else:
        print("\nError editing device template\n")
        print(device_template_edit_res.text)

    print("\nDevice uuid: %s"%device_uuid)

    # Fetching Device csv values

    print("\nFetching device csv values")

    payload = {"templateId":device_template_id,
               "deviceIds":device_uuid,
               "isEdited":True,"isMasterEdited":True}
    payload = json.dumps(payload)
    device_csv_res = vmanage_session.post_request("template/device/config/input/",payload)

    if device_csv_res.status_code == 200:
        device_csv_values = device_csv_res.json()['data']
    else:
        print("\nError getting device csv values\n")
        print(device_csv_res.text)

    # Attaching new Device template

    print("\nAttaching new device template")

    payload = {"deviceTemplateList":[{"templateId":device_template_id,
               "device":device_csv_values,
               "isEdited":True,"isMasterEdited":False}]}
    payload = json.dumps(payload)


    attach_template_res = vmanage_session.post_request("template/device/config/attachfeature",payload)

    if attach_template_res.status_code == 200:
        attach_template_pushid = attach_template_res.json()['id']
    else:
        print("\nattaching device template failed\n")
        print(attach_template_res.text)
        exit()

    # Fetch the status of template push

    while(1):
        template_status_res = vmanage_session.get_request("device/action/status/%s"%attach_template_pushid)
        if template_status_res.status_code == 200:
            if template_status_res.json()['summary']['status'] == "done":
                print("\nTemplate push status is done")
                break
            else:
                continue
        else:
            print("\nFetching template push status failed\n")
            print(template_status_res.text)
            exit()

cli.add_command(create_service_vpn)

if __name__ == "__main__":
    cli()