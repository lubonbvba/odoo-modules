#!/usr/bin/env python
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from lxml import etree as LET
from lxml import objectify
import pdb,logging
from datetime import datetime,timedelta

logger = logging.getLogger(__name__)
api_url = 'https://q02mon003.q.lan:9398/api'
username = "q\\admlbonjean"

session = False

def create_session():
    global session

    session = requests.Session()
    f=open('/home/odoo/.odoo/admlbonjean.pass','r')
    password=f.readlines()[0].replace('\n', '')
    r = session.post(api_url+'/sessionMngr/?v=latest', auth=(username, password), verify=False)
    session.headers.update({'X-RestSvcSessionId': r.headers['X-RestSvcSessionId']})
    #print r
    return

def veeam_get(href):
    r = session.get(href, verify=False)
    if r.status_code == 200:
        return r
    else:
        print "error"
        print r.status_code
        logger.error("url: %s" % href)
        return r




def veeam_decode(href,attrname=None,attrvalue=None):
    result=[]
    r= veeam_get(href)

    b=LET.fromstring(r.content)
    for ref in b:
#        print ref.attrib
#        pdb.set_trace()

        for links in ref:
#            print links.attrib
            #db.set_trace()
            for link in links:
                #pdb.set_trace()
                if not attrname  or ((attrname in link.keys()) and (link.attrib[attrname]==attrvalue)):
#                    print link.attrib
                    result.append(link)
                #s=veeam_get(link.attrib['Href'])
                #c=LET.fromstring(s.content)
 #   pdb.set_trace()        
    return {'result': result,'href':href, 'response': r }



def get_restorepoints(vmname,date=None,querytype=None):

#    print "start create session"
    create_session()
#    print "veeam_get"     
                             # backup server                         # credential ID
    #links=veeam_decode(api_url + "/catalog/vms/C0044CTX001","Rel","Alternate")
    #links=veeam_decode(api_url + '/query?type=HierarchyRoot&filter=Name=="Q01VCE002.q.lan"&format=entities')
    #urn:veeam:HierarchyRoot:bcbe8d35-fca9-440d-a55d-e1480e8a2de4
    #links=veeam_decode(api_url + '/query?type=restorepoint', 'Type', 'VmRestorePointReferenceList')
    #'urn:veeam:HierarchyRoot:067ab425-d735-49f2-a34f-c2ebd433ced9', 'Name': 'q01vce002.q.lan'
    #links=veeam_decode(api_url + '/lookup?type=vm&hierarchyRef="urn:veeam:HierarchyRoot:067ab425-d735-49f2-a34f-c2ebd433ced9"')

    #links=veeam_decode(api_url + "/hierarchyRoots", 'Type', 'BackupServerReference') #, 'Type', 'HierarchyRoot')
    #links=veeam_decode(api_url + "/hierarchyRoots", "Rel", "Alternate")#, 'Name','Q01BUP002.q.lan') #, 'Type', 'HierarchyRoot')
    #links=veeam_decode(api_url + '/lookup?type=vm&host=6bb9e181-2368-4d3c-a6d3-b632934a10b3')


    #links=veeam_decode(api_url + "/restorePoints/1950be56-45c9-4d24-8e65-00169f748253?format=Entity")
    #restorePoints/1950be56-45c9-4d24-8e65-00169f748253?format=Entity
    #links=veeam_decode(api_url + "/backupSessions","Rel","Alternate")
    #links=veeam_decode(api_url + "/lookupSvc","Type", "HierarchyItemList")
    if not date:
        date=datetime.today() - timedelta(days=1)
        date=datetime.strftime(date, "%Y-%m-%d")
    date_start=date + " 12:00:00"
    date_end=datetime.strptime(date, "%Y-%m-%d").date() + timedelta(days=1)
    date_end=datetime.strftime(date_end, "%Y-%m-%d") + " 12:00:00"
#    pdb.set_trace()

    result=veeam_decode(api_url + '/query?type='+ querytype +'&format=entities&filter=VmDisplayName=="'+ vmname +'";CreationTime>="'+date_start+'";CreationTime<"'+date_end+'"','Type',querytype)
#    result=veeam_decode(api_url + '/query?type=VmRestorePoint&format=entities&filter=VmDisplayName=="'+ vmname +'";CreationTime>="'+date_start+'";CreationTime<"'+date_end+'"','Type','VmRestorePoint')
#    result=veeam_decode(api_url + '/query?type=VmReplicaPoint&format=entities&filter=VmDisplayName=="'+ vmname +'";CreationTime>="'+date_start+'";CreationTime<"'+date_end+'"','Type','VmReplicaPoint')

    links=result['result']
 #   print "nr of results:", len(links)
    res=[]
    for r in links:
        restorepoint={}
        restorepoint['uid']=r.attrib['UID']
        for t in r:
           # print t
            if len(t) == 0:
                if t.tag.lower().find('creationtimeutc') > 0:
                    #print 'creation time: ', t.text
                    restorepoint['creationtimeutc']= t.text
                elif t.tag.lower().find('algorithm') > 0:
                    #print 'algorithm: ', t.text
                    restorepoint['algorithm']= t.text
                elif t.tag.lower().find('pointtype') > 0:
                    #print 'pointtype: ', t.text
                    restorepoint['pointtype']= t.text
                elif t.tag.lower().find('hierarchyobjref') > 0:
                    #print 'hierarchyobjref: ', t.text
                    restorepoint['hierarchyobjref']= t.text
#                else:
#                    print t
            else:
                print "Len >0", len(t) 
                for u in t:
                    if 'Type' in u.attrib.keys() and u.attrib['Type']=='BackupServerReference':
                        restorepoint['BackupServerReference']=u.attrib['Name']
                        #print u.attrib
        res.append(restorepoint)
    return {'res': res,'href':result['href'], 'response':result['response']}    

def get_all_points(date,querytype):
    points=[]
    if not date:
        date=datetime.today() - timedelta(days=1)
        date=datetime.strftime(date, "%Y-%m-%d")
    date_start=date + " 12:00:00"
    create_session()
    result=veeam_get(api_url + '/query?type='+ querytype +'&format=entities&filter=CreationTime>="'+ date_start + '"')
    a=LET.fromstring(result.content)
    for b in a[0]:
        #print len(b)
        for c in b:
      #      print c.keys()
    #        print c.attrib['Name'].split('@')[0],c.attrib['Name'].split('@')[1],c.attrib['Type'],c.attrib['UID']
            point={
            'Name':c.attrib['Name'].split('@')[0],
            'Date':c.attrib['Name'].split('@')[1],
            'Type':c.attrib['Type'],
            'UID':c.attrib['UID'],
            }
            for t in c:
                #pdb.set_trace()
                if t.tag.lower().find('creationtimeutc') > 0:
                    #print 'creation time: ', t.text
                   point['creationtimeutc']= t.text
                elif t.tag.lower().find('algorithm') > 0:
                    #print 'algorithm: ', t.text
                    point['algorithm']= t.text
                elif t.tag.lower().find('pointtype') > 0:
                    #print 'pointtype: ', t.text
                    point['pointtype']= t.text
                elif t.tag.lower().find('hierarchyobjref') > 0:
                    #print 'hierarchyobjref: ', t.text
                    point['hierarchyobjref']= t.text

            points.append(point)    
    return points


def test_functions():
    #points = get_restorepoints("C0008ALF001","2018-01-22",'VmRestorePoint')
    #print len (points)
    create_session()
    #result=veeam_get('http://q02mon003.q.lan:9399/api/restorePoints')
    #result=veeam_get('http://q02mon003.q.lan:9399/api/query?type=VmRestorePoint&format=entities&filter=VmDisplayName=="Q02MON001";CreationTime>="2018-01-24 12:00:00";CreationTime<"2018-01-25 12:00:00"')
    result=veeam_get('http://q02mon003.q.lan:9399/api/query?type=VmRestorePoint&format=entities&filter=CreationTime>="2018-01-26 12:00:00"')
    #result=veeam_get('http://q02mon003.q.lan:9399/api/query?type=VmRestorePoint&format=entities&filter=VmDisplayName=="Q02MON001"')

    a=LET.fromstring(result.content)
    for b in a[0]:
        print len(b)
        for c in b:
      #      print c.keys()
            print c.attrib['Name'].split('@')[0],c.attrib['Name'].split('@')[1],c.attrib['Type'],c.attrib['UID']
            for tag in c:
                print tag

     #       print c.attrib['UID']
     #       print c.attrib['Href']

    pdb.set_trace()
