# https://github.com/rancher/rancher/blob/331d18b352cfd58d5e0fc4815dffad97ca30eb49/tests/validation/tests/v3_api/test_node_annotation.py#L185
# https://github.com/kubernetes-client/python/tree/master/examples

# pip requirements
#  pip3.10 install git+https://github.com/rancher/client-python.git@master
#  pip3.10 install kubernetes

import rancher
from kubernetes import client, config
import os

# This is the workaround for adding annotations to namespaces from projects. 

try:
    # Grabs the kubeconfig of the cluster this script is running on.
    config = config.load_incluster_config()
    # use this config for testing locally on laptop
    #config = config.load_kube_config()
except Exception as e:
     print(e)

v1 = client.CoreV1Api()

# Connect to the Rancher API
ranch_client = rancher.Client(url=os.getenv('ANNO_URL'),
                       access_key=os.getenv('ANNO_ACCESS_KEY'),
                       secret_key=os.getenv('ANNO_SECRET_KEY'))

# Function to grab the project id which is something generated like "cluster_id:project_id".
def get_project_anno(cluster_project_id):
    proj = ranch_client.by_id_project(cluster_project_id)

    return proj.annotations

# Function to apply annotations from its project
def set_anno(namespace,project):
    ns_name = namespace.metadata.name

    # User defined annotations to look for
    team_anno = ["product","teamemail","division","costcenter"]
    ns_anno_dict = {}

    for key,value in project.items():
        if key in team_anno:
            ns_anno_dict.update({key:value})
    
    # TODO: Grab existing annotations and compare, only patch if necessary

    # Patch the namespace if annotations are found
    if len(ns_anno_dict) > 0:
        v1.patch_namespace(ns_name, body={
            "metadata":{"annotations":ns_anno_dict}
        })
        print("Adding annotations...: ",ns_anno_dict)
    else:
        print("* defined annotations not found...")
    print("")

ns = v1.list_namespace()

# Go through the dictionary of namespaces
for x in ns.items:

    anno = x.metadata.annotations
    proj_found = False
    print(" ")
    print("checking namespace: ",x.metadata.name)

    for a in anno:
        # Only process namespaces that have projects attached to them as annotations
        if 'field.cattle.io/projectId' in a and 'cattle' not in x.metadata.name:
            proj_found = True
            print("namespace has projectId annotation...")
            break

    if proj_found:
        cluster_project_id = x.metadata.annotations['field.cattle.io/projectId']
        proj_anno = get_project_anno(cluster_project_id)
        set_anno(x,proj_anno)
    else:
        print("field.cattle.io/projectId annotation not found in namespace",x.metadata.name)
