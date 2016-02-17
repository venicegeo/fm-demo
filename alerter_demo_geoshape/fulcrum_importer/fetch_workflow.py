import json
import requests
############################################################################################
#                                                                                          #
#   Issues found in pz_workflow:                                                           #
#                                                                                          #
#   Events created but return 502                                                          #
#   Events and triggers created but they become null values and cannot be retrieved        #
#   New events or triggers will cause old ones to become null                              #
#                                                                                          #
############################################################################################
class PzWorkflow:

    def __init__(self, url):
        self.addr = url
        print self.addr

    def status(self):
        return requests.get(self.addr).status_code;

    def get_trigger(self, data):
        search = json.loads(data)
        triggers = requests.get(self.addr + "/v1/triggers/").json()
        for trigger in triggers:
            if trigger is not None:
                if (search.get("title") == trigger.get("title")) and (search.get('condition') == trigger.get('condition')): # to python dict
                    return trigger
        return None

    def post_trigger(self, data):
        check = self.get_trigger(data)
        if not check:
            posted_trigger = requests.post(self.addr + "/v1/triggers/", data = data)
            if posted_trigger.status_code == 201:
                print"Trigger created"
                return posted_trigger
            else:
                check = self.get_event(data)
                if not check:
                    print "Trigger not created"
                else:
                    print "Trigger created with status code: " + str(posted_trigger.status_code)
                return posted_trigger
        else:
            print "Trigger already exists"
            return None

    def get_all_triggers(self):
        return requests.get(self.addr + "/v1/triggers/").json() #to python dict

    def delete_trigger(self, id):
        pass

    def get_event(self, data):
        search = json.loads(data)
        events = requests.get(self.addr + "/v1/events/").json()
        for event in events:
            if event is not None:
                if event.get("type") == search.get("type"):
                    return event
        return None

    def get_all_events(self):
        return requests.get(self.addr + "/v1/events/").json()

    def post_event(self, data):
        check = self.get_event(data)
        if not check:
            posted_event = requests.post(self.addr + "/v1/events/", data=data)
            if posted_event.status_code == 201:
                print "Event created"
                return posted_event
            else:
                check = self.get_event(data)
                if not check:
                    print "Event not created"
                else:
                    print "Event created with status code: " + str(posted_event.status_code)
                return posted_event
        else:
            print "Event already exists"
            return None

    def get_all_alerts(self):
        return requests.get(self.addr + "/v1/alerts/").json()

    def get_alert(self, id):
        search = id
        alerts = requests.get(self.addr + "/v1/alerts/").json()
        for alert in alerts:
            if alert:
                if alert.get("id") == search:
                    return search
        return None


    def delete_alert(self, id):
        check = self.get_alert(id)
        if check:
            print "Deleting"
            deleted_id = requests.delete(self.addr + "/v1/alerts/" + id)
            check = self.get_alert(id)
            if check:
                print "Delete failed"
                return deleted_id
            else:
                print "Success"
                return deleted_id
        else:
            print "Could not find alert to delete"
            return None



# post trigger, get trigger, post event, get event, delete trigger, get alerts
def main():
    trigger = '{"title":"Test", "condition": {"type":"newtype","query":"another query"}, "job":{"task":"do something"}}'
    event = '{"type": "Type1", "date": "2016-02-16T21:20:48.052Z", "data": {}}'
    a = "A8"

    pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")

    #posted_response = pz_workflow.post_trigger(input)

    #if posted_response is not None:
    #    print posted_response.text

    #print pz_workflow.get_trigger(input)
    #print pz_workflow.get_event(event)
    #pz_workflow.post_event(event)
   # print pz_workflow.get_event(event)
    print pz_workflow.status()
    print pz_workflow.get_alert(a)
    print pz_workflow.delete_alert(a)
    print pz_workflow.get_alert(a)
    pass

if(__name__ == "__main__"):
    main()

# things = requests.get(addr)
#     print things

#json.dumps changes to string
#json.loads and .json() change to python dict