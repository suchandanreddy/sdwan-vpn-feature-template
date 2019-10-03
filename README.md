#	Usecase-2: Configuration API's

## Objective 

-   How to use vManage REST APIs to create feature templates and attach it to respective device template to configure new VPN at a site.

## Resource URL Structure Components

https://<vmanage-ip:port>/dataservice/template/feature/

## Create Templates

Now let’s start using the python script to create the template by using below steps

  - Build payload to provide the variables needed to create template
  - Perform the POST operation by sending template variables in payload. 

We can use `.yaml` file to store all the required variables for configuring the template. For example, please see below file `site-service-vpn-config.yaml`

```
$ cat site-service-vpn-config.yaml 
vpn_template_name: 'DC-vEdge-VPN30'
ospf_template_name: 'DC-VPN30-OSPF'
vpn_interface_template_name: 'DC-VPN30-Interface-Template'
service_vpn_id: '30'
service_vpn_interface_id: 'loopback100'
interface_ip_address: '10.2.10.250/24'
ospf_router_id: '10.2.0.2'
vpn_default_gw: '10.1.10.1'
ospf_area_number: '0'

```

While building the templates, we can load the content from above `.yaml` file 

### Code Components

Please note that this is a FYI section which includes code snippets and structure of command `create-service-vpn` in CLI based python application script **configure-vpn-template.py**. 

Using POST request to URL "template/feature/" to create the template.

**Step-1:**

**Note:** Provide the yaml file to script using the option `--input_yaml`

<pre>
On windows command prompt, run command <b>python3 configure-vpn-template.py create-service-vpn --input_yaml site-service-vpn-config.yaml</b> <br>to create the VPN, Interface and OSPF feature templates based on the variables defined in site-service-vpn-config.yaml file.
</pre> 

**Sample Response**

```
$ python3 configure-vpn-template.py create-service-vpn --input_yaml site-service-vpn-config.yaml
Creating feature template based on yaml file details

Loading Network Configuration Details from YAML File

Fetching Template uuid of DC-vEdges

Fetching feature templates associated with DC-vEdges device template

Creating Service VPN Template

Created service vpn template ID:  {'templateId': 'c16da1f1-2022-460b-ae3a-f299b24b6d21'}

Creating VPN Interface Template

Created service vpn interface template ID:  {'templateId': '502a578b-1412-43fd-99f7-82b39e102cf5'}

Creating OSPF Template

Created OSPF feature template ID:  {'templateId': 'dae52e2d-8557-4bba-883b-9acd1b9c4b88'}

Device uuid: ['ebdc8bd9-17e5-4eb3-a5e0-f438403a83de', 'f21dbb35-30b3-47f4-93bb-d2b2fe092d35', '9e785ad7-558a-40c6-b0c0-fcc96e6d04ca', 'b3265c5c-3db6-4d25-9d3b-1f416b89adb0']

Fetching device csv values

Attaching new device template

Template push status is done
```

When template is created, the vManage returns the templateId which is used further to attach the feature template to the device template and then push it to the edge router. 


## Conclusion

In this section, we have learned how to create new VPN at a site using vManage template configuration APIs.

Instead of .yaml file we can also store all required variables in .csv file and create the templates by reading variables data from .csv file. 