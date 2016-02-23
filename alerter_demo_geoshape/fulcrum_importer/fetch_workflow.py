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


# post, get, get all, delete
class PzWorkflow:



    def __init__(self, url):
        self.addr = url
        self.map = {'trigger': "/v1/triggers/", 'event': "/v1/events/", 'alert': "/v1/alerts/"}
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

    def get(self, user_request):
        items = None
        try:
            items = requests.get(self.addr + self.map.get(user_request.get('type')))
            items = items.json()
        except:
            print "Could not get items"
            return None
        if user_request.get('data').get('id'):
            print "Finding by ID"
            for item in items:
                if item.get('id') == user_request.get('data').get('id'):
                    return item
            print "Could not find item"
            return None
        else:
            print "Finding by data objects"
            for item in items:
                un_matched = 0
                #print 'Comparing to item ' + str(item)
                for key in user_request.get('data'):
                    #print 'Searching for "' + key + '" in item'
                    if key in item:
                        if item.get(key) != user_request.get('data').get(key):
                            un_matched -= 1
                if un_matched == 0:
                    return item
            print "Could not find item by keys"
            return None


    def post(self, user_request):
        check = self.get(user_request)
        if not check:
            print "Creating. . ."
            data = json.dumps(user_request.get('data'))
            print data
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

    user_request = '{"type": "trigger", "data": {"title": "Testing", "condition": {"type": "Foo", "query": "the query"}, "job": {"Task": "do something"}}, "action": "delete"}'
    event = '{"type": "event", "data": {"type" : "Food", "date": "2016-02-16T21:20:48.052Z", "data":{"type":"Feature","properties":{"name":"A place"},"geometry":{"type":"Point","coordinates":[91.99404,62.75621]}}}, "action": "post"}'
    delete_request = '{"type": "trigger", "data": {"id": "X6"}, "action": "delete"}'

    pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
    data = '{"type" : "Food", "date": "2016-02-16T21:20:48.052Z", "data":{"type":"Feature","properties":{"name":"A place"},"geometry":{"type":"Point","coordinates":[91.99404,62.75621]}}}'
    #print pz_workflow.request(user_request)
    print pz_workflow.status()
    print pz_workflow.request(event)
    requests.post(self.addr + self.map.get('event'), data=data)
    pass

if(__name__ == "__main__"):
    main()

# things = requests.get(addr)
#     print things

#json.dumps changes to string
#json.loads and .json() change to python dict