#!/usr/bin/env python
# coding: utf-8

# In[165]:


import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
import requests
import pandas as pd
st.set_page_config(layout="wide")


# In[166]:


# Reading JSONs stored in Local


# In[167]:

class CleanDocuments():
    def __init__(self):
        pass

    def cleanDocID(self, doc, userNameIndex):
        doc['name']=doc['name'].split("/")[userNameIndex:]

    def removeLevels(self, doc):
        for key in doc['fields']:
            for redundantKey in doc['fields'][key]:
                if redundantKey=="arrayValue":
                    doc['fields'][key]=self.removeArrayLevel(doc['fields'][key][redundantKey])
                else:
                    doc['fields'][key]=doc['fields'][key][redundantKey]

    def removeArrayLevel(self, values):
        values=values['values']
        newList=[]

        for value in values:
            for key in value:
                newList.append(value[key])
        
        return newList

    def cleanDocument(self, doc, userNameIndex):
        self.cleanDocID(doc, userNameIndex)
        self.removeLevels(doc)

    def cleanAllDocuments(self, data, userNameIndex):
        for doc in data:
            self.cleanDocument(doc, userNameIndex)

    #Run this
    def simplifyDataDump(self, data, userNameIndex=-1, filename="clean_users.json", save=False):
        self.cleanAllDocuments(data, userNameIndex)
        new_dict={}
        new_dict['documents']=data
        
        if save:
            json_obj=json.dumps(new_dict, indent=2)
            with open(filename, "w") as fo:
                fo.write(json_obj)
        return new_dict

    #Cleaning activities
    def getCleanedWorkoutData(self, data, filename="clean_last_activity.json", save=False):
        cleanLastActivity=self.simplifyDataDump(data, -3, filename, save)

        return cleanLastActivity

class GetData():
    def __init__(self):
        pass

    def getData(self, url, many=True):
        r=requests.get(url)
        data=r.json()
        temp=r.json()
        print("Initial request complete")

        if many:
            while "nextPageToken" in temp.keys():
                r=requests.get(url+"?pageToken="+temp['nextPageToken'])
                temp=r.json()
                data['documents'].extend(temp['documents'])

            print("All requests complete")
            return data['documents']
        return data

    def filterUser(self, userDoc, requiredFields):
        username=userDoc['fields']['name']['stringValue']
        email=userDoc['fields']['email']['stringValue']

        for field in requiredFields:
            if field in userDoc['fields'].keys():
                return userDoc

        return 

    def filterAll(self, userDocs, requiredFields):
        docs=[]
        for userDoc in userDocs:
            doc=self.filterUser(userDoc, requiredFields)
            if doc!=None:
                docs.append(doc)

        return docs

    def saveToFile(self, docs, filename):
        new_dict={}
        new_dict['documents']=docs
        json_obj=json.dumps(new_dict, indent=2)
        with open(filename, "w") as f:
            f.write(json_obj)

    def filterAllUsers(self, url, requiredFields=["lastActivity"], save=False, filename="users_filtered.json"):
        data=self.getData(url)
        docs=self.filterAll(data, requiredFields)
        if save:
            self.saveToFile(docs, filename)
        
        return docs

    def getLastActivityData(self, data):
        lastActivityData=[]
        baseUrl="https://firestore.googleapis.com/v1/projects/isometrix-eb8de/databases/(default)/documents/users"
        for document in data:
            collections=document['fields']['lastActivity']
            for collection in collections:
                url=baseUrl+"/"+document['name'][-1]+"/"+collection+"/"+document['fields']['lastActivityDate']
                workoutData=self.getData(url, False)
                if 'name' in workoutData.keys():
                    lastActivityData.append(workoutData)
        return lastActivityData

    def lastActivityDataReceiver(self, data, filename="last_activity.json", save=False):
        lastActivityData=self.getLastActivityData(data)

        if save:
            self.saveToFile(lastActivityData, filename)
            return
        
        return lastActivityData

class Combine():
    def __init__(self, cleanUserProfileData ,cleanLastActivityData):
        self.cleanUserProfileData = cleanUserProfileData
        self.cleanLastActivityData = cleanLastActivityData
        self.combinedData=[]
    
    def getSeparateData(self):
        return self.cleanUserProfileData, self.cleanLastActivityData
    
    def combineData(self):
        for user in self.cleanUserProfileData['documents']:
            userDict=user
            userDict['activities']=[]

            userID=user['name'][0]

            # self.combinedData.push(user)
            for activity in self.cleanLastActivityData['documents']:
                if activity['name'][0]==userID:
                    userDict['activities'].append(activity)
            
            self.combinedData.append(userDict)
    @st.cache            
    def getCombinedData(self):
        return self.combinedData

@st.cache
def execute():
    url="https://firestore.googleapis.com/v1/projects/isometrix-eb8de/databases/(default)/documents/users"

    cleaner=CleanDocuments()
    fetcher=GetData()
    userProfileData = fetcher.filterAllUsers(url)
    print("!---------------Received user profile data------------!")

    cleanUserProfileData = cleaner.simplifyDataDump(userProfileData, save=False)
    print("!-------------------Cleaned User Profile Data------------!")

    lastActivityData = fetcher.lastActivityDataReceiver(cleanUserProfileData['documents'])
    print("!---------------Received Last Activity Data------------!")

    cleanLastActivityData = cleaner.getCleanedWorkoutData(lastActivityData, save= False)
    print("!----------------------Finished Execution---------------!")


    combiner=Combine(cleanUserProfileData, cleanLastActivityData)
    combiner.combineData()

    # fetcher.saveToFile(combiner.getCombinedData(), filename="combined.json")
    return combiner


# In[168]:
# global combiner
# global data
# if st.button("Load Data", key = "Load"):
combiner = execute()
data = combiner.getCombinedData()
data = [data[1]]
# In[169]:


name_fields_array = []
date_fields_array = []


# In[170]:


for idx, elem in enumerate(data):
    name_fields_array.append(elem['fields']['name'])


# In[171]:


st.title("Last Users Activity System")
user_name = st.selectbox('Enter the Name of Client you want to check Last Activity for?',name_fields_array,key="user_name")


# In[172]:


curr_elem_idx = 0
flag = False
for idx, elem in enumerate(data):
    if elem['fields']['name'] == user_name:
        curr_elem_idx = idx
        flag = True


# In[173]:


# data[curr_elem_idx]['activities'][0]['fields']['exerciseName']


# In[147]:


date_fields_array = [data[curr_elem_idx]['fields']['lastActivityDate']]
exercise_date = st.selectbox('Enter the Last Activity Date?',date_fields_array,key="date")


# In[174]:


# data[curr_elem_idx]['activities'][0]['fields']['exerciseDate']


# In[176]:


last_exercise_activity = []
for i, act_elem in enumerate(data[curr_elem_idx]['activities']):
    if act_elem['fields']['exerciseDate'] == exercise_date:
        last_exercise_activity.append(act_elem)


# In[177]:


exercise_list = [elem['fields']['exerciseName'] for elem in last_exercise_activity]
# exercise_list


# In[178]:


exercise_name = st.selectbox('Enter the Last Activity Exercise Name?',exercise_list,key="exer_name")


# In[188]:


curr_exercise_idx = 0
for idx, act_elem in enumerate(data[curr_elem_idx]['activities']):
    if act_elem['fields']['exerciseName'] == exercise_name:
        curr_exercise_idx = idx


# In[195]:


exercise = data[curr_elem_idx]['activities'][curr_exercise_idx]


# In[196]:


exercise_name = exercise['name'][1]


# In[197]:


# exercise_name


# In[67]:


if flag == True:
    st.header("Exercise Details")
    exercise_name = exercise['name'][1]
    date = exercise['name'][2]
    dailypower = int(exercise['fields']['dailyPower'])
    x = exercise['fields']['workoutData']
    workoutData = list(map(int, x))
    peakforce = int(exercise['fields']['peakForce'])
    bps = int(exercise['fields']['bestPowerSet'])
    # Exercise Details
    st.subheader("Exercise Info")
    st.write("Client's Name: " + str(user_name))
    st.write("Exercise Name: " + str(exercise_name))
    st.write("Date: " + str(date))
    st.subheader("Exercise Plot")
    chart_data = pd.DataFrame(
    np.array(workoutData),
    columns=['workout'])
    st.line_chart(chart_data)
    st.subheader("Exercise Scores")
    st.write("Daily Power: " + str(dailypower))
    st.write("Peak Force: " + str(peakforce))
    st.write("Best Power Set: " + str(bps))

