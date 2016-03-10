import json
import requests

# post, get, get all, delete
class PzWorkflow:


    def __init__(self, url):
        self.addr = url
        self.map = {'trigger': "/v1/triggers/", 'eventtypes': '/v1/eventtypes/', 'event': "/v1/events/", 'alert': "/v1/alerts/"}
        print "Pz object created with url: " +self.addr

    def status(self):
        return requests.get(self.addr).status_code;

    def request(self, user_request):
        user_request = json.loads(user_request)
        if(user_request.get('action') == 'post'):
            return self.post(user_request)
        elif(user_request.get('action') == 'get'):
            return self.get(user_request)
        elif(user_request.get('action') == 'get_all'):
            return self.get_all(user_request)
        elif(user_request.get('action') == 'delete'):
            return self.delete(user_request)
        else:
            print "Could not find action"
            return None

    def find_by_id(self, items, user_request):
        print "Finding by ID"
        for item in items:
            if item is not None:
                if item.get('id') == user_request.get('data').get('id'):
                    return item
        print "Could not find item"
        return None

    def find_by_data(self, items, user_request):
        print "Finding by data objects"
        for item in items:
            if item is not None:
                un_matched = 0
                key_in_item = False
                #print 'Comparing to item ' + str(item)
                for key in user_request.get('data'):
                    #print 'Searching for "' + key + '" in item'
                    if key in item:
                        key_in_item = True
                        if item.get(key) != user_request.get('data').get(key):
                            un_matched -= 1
                if un_matched == 0 and key_in_item is True:
                    return item
        print "Could not find item by keys"
        return None

    def get(self, user_request):
        items = None
        try:
            items = requests.get(self.addr + self.map.get(user_request.get('type')))
            items = items.json()
        except:
            print "Could not get items"
            return None

        if user_request.get('data').get('id'):
            print user_request.get('data').get('id')
            return self.find_by_id(items, user_request)
        else:
            return self.find_by_data(items, user_request)

    def post(self, user_request):
        check = self.get(user_request)
        if not check:
            print "Creating. . ."
            data = json.dumps(user_request.get('data'))
            if user_request.get('type') == 'event':
                posted = requests.post(self.addr + self.map.get(user_request.get('type')) + user_request.get('eventname'), data=data)
            else:
                posted = requests.post(self.addr + self.map.get(user_request.get('type')), data=data)
            if posted.status_code == 201:
                print '{} created'.format(user_request.get('type'))
                return posted
            else:
                check = self.get(user_request)
                if not check:
                    print '{} not created with status code: {}'.format(user_request.get('type'), posted.status_code)
                else:
                    print '{} created with status code: {}'.format(user_request.get('type'), posted.status_code)
                return posted
        else:
            print '{} already exists'.format(user_request.get('type'))
            return None

    def get_all(self, user_request):
        return requests.get(self.addr + self.map.get(user_request.get('type')))

    def delete(self, user_request):
        check = self.get(user_request)
        if check:
            print "Deleting"

            if user_request.get('type') == "event":
                deleted_id = requests.delete(self.addr + self.map.get(user_request.get('type'))  + user_request.get('eventname') + "/" + check.get('id'))
            else :
                print self.addr + self.map.get(user_request.get('type')) + ':' + check.get('id')
                deleted_id = requests.delete(self.addr + self.map.get(user_request.get('type')) + check.get('id'))
            check = self.get(user_request)
            if check:
                print "Delete failed"
                return deleted_id
            else:
                print "Success"
                return deleted_id
        else:
            print "Could not find item to delete"
            return None



# post trigger, get trigger, post event, get event, delete trigger, get alerts
def main():

    pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
    user_request = {"type": "event", "action": "delete", "eventname" : "US-Phone-Number"}
    #trigger
    #user_request["data"] = {"title": "US-Phone-Number", "condition": {"type": "W3", "query": {"query": {"bool": {"must": [{"match": {"severity": 4}},{"match": {"problem": "US-Phone-Number"}}]}}}, "job": {"task" :"somestring"}}}
    #event type
    #user_request["data"] = {"name": "US-Phone-Number", "mapping" : {"itemId": "string", "severity": "integer", "problem": "string"}}
    #event
    #user_request["data"] = {"type": "W3", "date": "2007-04-05T14:30:00Z", "data": {"severity": 4, "problem": "US-Phone-Number"}}
    user_request["data"] = {"id": "W15"}
    #user_request["data"] = {"type": "ET1", "date": "2007-05-05T14:30:00Z", "data": {"code": "PHONE", "filename": "featuresFile", "severity": 3}}
    print pz_workflow.status()

    print pz_workflow.request(json.dumps(user_request))
    #requests.post(self.addr + self.map.get('event'), data=data)
    pass

if(__name__ == "__main__"):
    main()

# things = requests.get(addr)
#     print things

#json.dumps changes to string
#json.loads and .json() change to python dict