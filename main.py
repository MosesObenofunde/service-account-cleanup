from google.oauth2 import service_account
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import googleapiclient.discovery
import os
import time
from datetime import date, datetime
import requests
import google.oauth2.id_token
import google.auth
import google.auth.transport.requests

PROJECT=os.environ.get('GCP_PROJECT')

service = discovery.build('iam', 'v1')

rq = service.projects().serviceAccounts().list(name="projects/"+PROJECT)

def clean_up_service_account(request):
  request_json = request.get_json()
  credentials, project_id = google.auth.default( scopes='https://www.googleapis.com/auth/cloud-platform')
  
  
  auth_req = google.auth.transport.requests.Request()
  credentials.refresh(auth_req)
  id_token=credentials.token
  headers= {"Authorization": f"Bearer {id_token}"}    
  rq = service.projects().serviceAccounts().list(name="projects/"+PROJECT)    
  while True:
      response = rq.execute()
  
      for service_account in response.get('accounts', []):
          try:
            if service_account["disabled"] and PROJECT+".iam.gserviceaccount.com" in service_account["email"] :
              print("InActive : "+service_account["email"])
            
              url="https://policyanalyzer.googleapis.com/v1/projects/"+PROJECT+"/locations/global/activityTypes/serviceAccountLastAuthentication/activities:query?filter=activities.full_resource_name%3D%22%2F%2Fiam.googleapis.com%2Fprojects%2F"+PROJECT+"%2FserviceAccounts%2F"+service_account["email"]+"%22"

              name="projects/"+PROJECT+"/serviceAccounts/"+service_account["email"]
               
              try:
                res = requests.get(url, headers=headers)
                result=res.json() 
                d1=result["activities"][0]["activity"]["lastAuthenticatedTime"].partition('T')[0].strip()
                d2=str(date.today())
                  
                d1t = datetime.strptime(d1, "%Y-%m-%d")
                d2t = datetime.strptime(d2, "%Y-%m-%d")
                delta = d2t - d1t
                print ("Last Authentication in days: ", delta.days) 
                if delta.days >= 7:
                  print("Deleting the service account : "+service_account["email"])
                  service.projects().serviceAccounts().delete(name=name).execute()   

              except KeyError:
                print("Deleting the service account : "+service_account["email"])
                service.projects().serviceAccounts().delete(name=name).execute()
                
          except KeyError:
            if PROJECT+".iam.gserviceaccount.com" in service_account["email"]:    
              print("Active : "+service_account["email"])
              keyreq = service.projects().serviceAccounts().keys().list(name="projects/"+PROJECT+"/serviceAccounts/"+service_account["email"])
              for key in keyreq.execute()["keys"]:
                if key["keyType"] == "USER_MANAGED":
                  print("Removing the keys : "+key["name"])
                  service.projects().serviceAccounts().keys().delete(name=key["name"]).execute()
                else:
                  continue

                
  
      rq = service.projects().serviceAccounts().list_next(previous_request=rq, previous_response=response)
      if rq is None:
          break
  return "success"
