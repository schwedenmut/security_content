import sys
from time import sleep
import splunklib.results as results
import splunklib.client as client
import splunklib.results as results
import requests

from typing import Union

def enable_delete_for_admin(splunk_host, splunk_port, splunk_password):
    try:
        service = client.connect(
            host=splunk_host,
            port=splunk_port,
            username='admin',
            password=splunk_password
        )
    except Exception as e:
        raise(Exception("Unable to connect to Splunk instance: " + str(e)))
        

    # search and replace \\ with \\\
    # search = search.replace('\\','\\\\')
    role = service.roles['admin']
    try:
        role.grant('delete_by_keyword')
    except Exception as e:
        print("Error - failed trying to grant 'can_delete' privs to admin: [%s]"%(str(e)))
        return False
    return True



def test_baseline_search(splunk_host, splunk_port, splunk_password, search, pass_condition, baseline_name, baseline_file, earliest_time, latest_time)->dict:
    try:
        service = client.connect(
            host=splunk_host,
            port=splunk_port,
            username='admin',
            password=splunk_password
        )
    except Exception as e:
        raise(Exception("Unable to connect to Splunk instance: " + str(e)))
        


    # search and replace \\ with \\\
    # search = search.replace('\\','\\\\')

    if search.startswith('|'):
        search = search
    else:
        search = 'search ' + search

    kwargs = {"exec_mode": "blocking",
              "dispatch.earliest_time": earliest_time,
              "dispatch.latest_time": latest_time}

    splunk_search = search + ' ' + pass_condition

    try:
        job = service.jobs.create(splunk_search, **kwargs)
    except Exception as e:
        raise(Exception("Unable to execute baseline: " + str(e)))
        

    test_results = dict()
    test_results['diskUsage'] = job['diskUsage']
    test_results['runDuration'] = job['runDuration']
    test_results['baseline_name'] = baseline_name
    test_results['baseline_file'] = baseline_file
    test_results['scanCount'] = job['scanCount']

    if int(job['resultCount']) != 1:
        print("Test failed for baseline: " + baseline_name)
        test_results['error'] = True
        return test_results
    else:
        print("Test successful for baseline: " + baseline_name)
        test_results['error'] = False
        return test_results



def test_detection_search(splunk_host:str, splunk_port:int, splunk_password:str, search:str, pass_condition:str, detection_name:str, detection_file:str, earliest_time:str, latest_time:str)->dict:
    if search.startswith('|'):
        search = search
    else:
        search = 'search ' + search 

    kwargs = {"exec_mode": "blocking",
              "dispatch.earliest_time": "-1d",
              "dispatch.latest_time": "now"}

    splunk_search = search + ' ' + pass_condition
    test_results = dict()
    
    #These will always be present. By default, we will say that the
    #test has failed AND there was an error (until they are set otherwise)
    test_results['search_string'] = splunk_search
    test_results['detection_name'] = detection_name
    test_results['detection_file'] = detection_file
    
    test_results['success'] = False
    test_results['error'] = True

    
    try:
        service = client.connect(
            host=splunk_host,
            port=splunk_port,

            username='admin',
            password=splunk_password
        )
    except Exception as e:
        print("Unable to connect to Splunk instance: " + str(e),file=sys.stderr)
        test_results['error'] = True
        return test_results


    # search and replace \\ with \\\
    # search = search.replace('\\','\\\\')

   

    print("SEARCH: %s"%(splunk_search))


    try:
        job = service.jobs.create(splunk_search, **kwargs)
    except Exception as e:

        print("Unable to execute detection:\n%s"%(str(e)))
        test_results['error'] = True
        return test_results

    test_results['diskUsage'] = job['diskUsage']
    test_results['runDuration'] = job['runDuration']
    test_results['scanCount'] = job['scanCount']
    
    #If we get this far, then there was not an error
    #The search may have FAILED, but there was no error in the search
    test_results['error'] = False 


    #Should this be 1 for a pass, or should it be greater than 0?
    if int(job['resultCount']) != 1:
        #print("Test failed for detection: " + detection_name)
        test_results['success'] = False
        return test_results
    else:
        #print("Test successful for detection: " + detection_name)
        test_results['success'] = True
        return test_results


def delete_attack_data(splunk_host:str, splunk_password:str, splunk_port:int, wait_on_delete:Union[dict,None], search_string:str, detection_filename:str)->bool:
    
    try:
        service = client.connect(
            host=splunk_host,
            port=splunk_port,

            username='admin',
            password=splunk_password
        )
    except Exception as e:

        raise(Exception("Unable to connect to Splunk instance: " + str(e)))

    #splunk_search = 'search index=test* | delete'
    if wait_on_delete:
        print(wait_on_delete['message'])
        print("FILENAME : [%s]"%(detection_filename))
        print("SEARCH   :\n%s"%(search_string))
        _ = input("****************Press ENTER to Complete Test and DELETE data****************\n\n\n")
    splunk_search = 'search index=main | delete'

    kwargs = {"exec_mode": "blocking",
              "dispatch.earliest_time": "-1d",
              "dispatch.latest_time": "now"}

    try:
        job = service.jobs.create(splunk_search, **kwargs)
    except Exception as e:
        raise(Exception("Unable to execute search: " + str(e)))
    
    return True