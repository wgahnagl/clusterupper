import sys
import os
import requests
import subprocess
import io

CLUSTERNAME = "wgahnagl" 

def main():
    print("welcome to the puffball official clusterupper, your one stop shopping for upping clusters") 
    if len(sys.argv) < 2 :
        clusterbotLink = input("Please provide the link to the clusterbot build: ")
    else:
        clusterbotLink = sys.argv[1] 
    imageURL = getImageURL(clusterbotLink)
    
    print("Image pull URL found: " + imageURL )
    if not imageExists(imageURL):
        try:
            output = subprocess.run(["podman", "pull", imageURL+"/release"], check=True)
        except Exception as e:
            if (e.returncode == 125): 
                f = open("podmancreds", "r") 
                username = f.readline().strip()
                password = f.readline().strip()
                f.close()
                try:
                    subprocess.run(["podman", "login", "--username", username, "--password", password, "quay.io"], check=True)
                except: 
                    return 
                subprocess.run(["podman", "pull", imageURL+"/release"])

    writeConfigFile(imageURL) 
    print("config written")
    print("preparing to launch cluster...")  
    f = open("rundata", "r") 
    counter = (int(f.readline()))
    f.close()     
    counter += 1 
    xokdinst = os.path.expanduser('~') + "/.cargo/bin/" +  "xokdinst"
    try:
        launchCluster(counter, xokdinst)
    except KeyboardInterrupt:
        print("\n Destroying cluster " + CLUSTERNAME + str(counter))
        subprocess.Popen([xokdinst, "destroy", CLUSTERNAME + str(counter)]) 
        sys.exit()

def imageExists(imageURL):
    images = subprocess.check_output(["podman", "images"]) 
    return imageURL in str(images)

def launchCluster(counter, xokdinst):
    while True: 
        print ("attempting to launch cluster named " + CLUSTERNAME + str(counter)) 
        cmd = [xokdinst, "launch", CLUSTERNAME + str(counter) ,"-K","-I",  "registry.ci.openshift.org/ocp/release"]
        success = execute(cmd)
        if success == "destroy" : 
            destCmd = [xokdinst, "destroy", CLUSTERNAME + str(counter)] 
            print("destroying the last cluster") 
            counter += 1 
            f = open("rundata", "w") 
            f.write(str(counter))
            f.close()  
            subprocess.Popen(destCmd)
        elif success == "error" or success == "success": 
            break 



def execute(cmd, destroy=False):
   with subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1,
           universal_newlines=True) as p, io.StringIO() as buf:
    for line in p.stdout:
        print(line, end='')
    for line in p.stderr: 
        print(line, end='')
        if destroy == False and "use destroy to remove it" in line: 
            return "destroy"
        if destroy == False and "Error" in line: 
            return "error" 
    return "success" 

def writeConfigFile(imageURL):
    subprocess.run(["oc", "registry", "login", "--registry", "registry.build01.ci.openshift.org" ,"--to=registry.json"])
    configJson = os.path.expanduser('~') + "/.docker/config.json"
    configTmpJson = configJson + "1"
    configTmp = open(configTmpJson, "w")
    jqCommand = subprocess.run(["jq", "-s", ".[0] * .[1]", "registry.json", configJson],stdout=configTmp)
    subprocess.run(["mv", configTmpJson, configJson])

def getImageURL(clusterbotLink): 
    jobNumber = clusterbotLink.split("/")[-1]
    url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs/origin-ci-test/logs/release-openshift-origin-installer-launch-gcp/" + jobNumber + "/build-log.txt"
    resp = requests.get(url).text
    output = resp.split("images will be pullable from")[1].split(":${component}")[0].split("/stable")[0].strip()
    output = "-".join(output.split("-")[0:-1])
    return output
main() 


