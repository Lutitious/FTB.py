#! /usr/bin/env python3

import sys
import os
import json
import requests
import zipfile
import shutil

apiLink = "https://api.modpacks.ch/"

def getModpacks():
    print("Getting modpack list from the API...")
    modpacks = requests.get(apiLink + "public/modpack/all")
    # Store the modpacks in a json file called packlist.json
    with open("packlist.json", "w") as f:
        f.write(json.dumps(modpacks.json(), indent=4))

def getModpackInfo(modpackId):
    print("Getting modpack info from the API...")
    req = requests.get(apiLink + "public/modpack/" + str(modpackId))
    with open("pack-"+str(modpackId)+".json", "w") as f:
        f.write(json.dumps(req.json(), indent=4))

def downloadModpackJson(downloadLink):
    print("Downloading modpack from the API...")
    req = requests.get(downloadLink)
    with open("download.json", "w") as f:
        f.write(json.dumps(req.json(), indent=4))

def listModpackVersions():
    # Open the packlist.json file and load the data
    with open("packlist.json", "r") as f:
        data = json.load(f)
    packids = data["packs"]
    print("packids: ", packids)
    selected = input("Enter the pack id: ")
    getModpackInfo(selected)
    global packIdGlobal
    packIdGlobal = selected
    with open("pack-"+selected+".json", "r") as f:
        modpackData = json.load(f)
    name = modpackData["name"]
    global modpackName
    modpackName = name
    global modpackAuthor
    modpackAuthor = modpackData["authors"][0]["name"]
    print(name+" selected.")
    versions = modpackData["versions"]
    versionList = []
    for i in range(len(versions)):
        versionList.append(versions[i]["id"])
    print("Versions: ", versionList)
    selectedVersion = -1
    selectedVersion = input("Enter the version: ")
    downloadLink = apiLink + "public/modpack/" + selected + "/" + selectedVersion
    downloadModpackJson(downloadLink)
    getModpackFiles()

def getModpackFiles():
    if not os.path.exists("pack_files"):
        os.mkdir("pack_files")
    # Open the download.json file and load the data
    with open("download.json", "r") as f:
        data = json.load(f)
    # Get minecraft and modloader versions
    mcVersion = data["targets"][1]["version"]
    modloaderName = data["targets"][0]["name"]
    modloaderVersion = data["targets"][0]["version"]

    # Get the files from the json
    files = data["files"]
    # First grab all files with the type "mod"
    curseModFiles = []
    for i in range(len(files)):
        if "curseforge" in files[i]:
            curseModFiles.append(files[i])
    curseId = []
    for i in range(len(curseModFiles)):
        tempCurseId = []
        tempCurseId.append(curseModFiles[i]["curseforge"]["project"])
        tempCurseId.append(curseModFiles[i]["curseforge"]["file"])
        curseId.append(tempCurseId)
    # Covert the list to a the cf format { "fileID": 2234141, "projectID": 223005, "required": true }, instead of [2234141, 223005]
    curseFiles = []
    for i in range(len(curseId)):
        tempCurseFile = {}
        tempCurseFile["fileID"] = curseId[i][1]
        tempCurseFile["projectID"] = curseId[i][0]
        tempCurseFile["required"] = True
        curseFiles.append(tempCurseFile)

    # Convert the minecraft and modloader versions to the format "modLoaders": [{ "id": "forge-", "primary": true }], "version": "1.7.10"
    print("Creating manifest.json...")
    modloader = {}
    if modloaderName == "neoforge" and mcVersion == "1.20.1":
        modloader["id"] = modloaderName + "-" + mcVersion + "-" + modloaderVersion
    else:
        modloader["id"] = modloaderName + "-" + modloaderVersion
    modloader["primary"] = True
    minecraft = {}
    minecraft["version"] = mcVersion
    minecraft["modLoaders"] = [modloader]

    finalJson = {}
    finalJson["author"] = modpackAuthor
    finalJson["files"] = curseFiles
    finalJson["manifestType"] = "minecraftModpack"
    finalJson["manifestVersion"] = 1
    finalJson["minecraft"] = minecraft
    finalJson["name"] = modpackName
    finalJson["overrides"] = "overrides"
    finalJson["version"] = "1.0.0"
    with open("pack_files/manifest.json", "w") as f:
        f.write(json.dumps(finalJson, indent=4))

    # Create the overrides folder
    if not os.path.exists("pack_files/overrides"):
        os.mkdir("pack_files/overrides")
    # Get a list of all non curse files
    nonCurseFiles = []
    for i in range(len(files)):
        if "curseforge" not in files[i]:
            nonCurseFiles.append(files[i])
    # Download the non curse files
    for i in range(len(nonCurseFiles)):
        url = nonCurseFiles[i]["url"]
        modFilePath = nonCurseFiles[i]["path"]
        modFileName = nonCurseFiles[i]["name"]
        # remove ./ from the file name
        modFilePath = modFilePath[2:]
        # Create the directories if they don't exist
        if not os.path.exists("pack_files/overrides/"+modFilePath):
            os.makedirs("pack_files/overrides/"+modFilePath)
        print("Downloading: ", modFileName)
        r = requests.get(url, allow_redirects=True)
        open("pack_files/overrides/"+modFilePath+modFileName, "wb").write(r.content)
    zipModpack()

def zipModpack():
    # Create an output folder
    if not os.path.exists("output"):
        os.mkdir("output")
    # Zip the pack_files folder
    print("Zipping the modpack...")
    zf = zipfile.ZipFile("output/"+modpackName+".zip", "w")
    for dirname, subdirs, files in os.walk("pack_files"):
        zf.write(dirname)
        for filename in files:
            zf.write(os.path.join(dirname, filename))
    zf.close()
    print("Modpack created: ", modpackName+".zip")
    # Clean up the pack_files folder
    shutil.rmtree("pack_files", ignore_errors=True)
    shutil.rm


def main():
    getModpacks()
    listModpackVersions()

if __name__ == "__main__":
    main()