#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2

import os
import logging
import urllib, urllib2, json


# register for API key at https://foursquare.com/developers/register
import client_id
import client_secret

# register for API key at https://developer.flightstats.com/getting-started
import appKey
import appId
  
JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
   
   
class MainHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("In MainHandler")
        template_values={}
        template = JINJA_ENVIRONMENT.get_template('searchform.html')
        self.response.write(template.render(template_values))
    
class HomePageHandler(webapp2.RequestHandler):
    def get(self):
        vals = {}
        vals['page_title']="Home page"
        logging.info(type(self))
        req = self.request
        logging.info(type(req))
        vals['url']= req.url
        vals['counter_list']= range(n)
        template = JINJA_ENVIRONMENT.get_template('hello.html')
        self.response.write(template.render(vals))
# #   
def safeGet(url):
    try:
        print urllib2.urlopen(url)
        return urllib2.urlopen(url)
    except urllib2.HTTPError, e:
        print "The server couldn't fulfill the request." 
        print "Error code: ", e.code
    except urllib2.URLError, e:
        print "We failed to reach a server"
        print "Reason: ", e.reason
    return None


def fourSquare(baseurl = 'https://api.foursquare.com/v2/venues/explore?',
    params={},
    ):
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['v'] = '20161224'
    params['m'] = 'foursquare'
    params['radius']=500
    url = baseurl + urllib.urlencode(params)
    logging.info(url)
    return safeGet(url)      
  
def flightPath(baseurl = 'https://api.flightstats.com/flex/flightstatus/rest/v2/json/flight/tracks/',
                 params={}
                 ):
    params['appId']=appId
    params['appKey']=appKey
    params['maxPositions']=2
    params['includeFlightPlan']='false'
    params['utc']='false'
    url = baseurl + urllib.urlencode(params)
    return safeGet(url)     
    

class SearchPageHandler(webapp2.RequestHandler):
    def get(self):
        vals = {}
        vals['page_title']="Search form"
        template = JINJA_ENVIRONMENT.get_template('searchform.html')
        self.response.write(template.render(vals))


    
def display_info(t):
    logging.info(t)
    
    id = t['venue']['id']    
    photoUrl = 'https://api.foursquare.com/v2/venues/' + str(id) + '/photos?v=20161224&client_id=' + client_id + '&client_secret=' + client_secret
    
    logging.info(photoUrl)
    safeUrl = safeGet(photoUrl)
    jsresult = safeUrl.read()
    data = json.loads(jsresult)
#     photo = data['response']['photos']['items'][0]['prefix'] + '300x300' + data['response']['photos']['items'][0]['suffix']
    venueData = {
#         'photo':photo,
        'info':t}
    return venueData
           
class SearchResponseHandler(webapp2.RequestHandler):
    def post(self):
        vals = {}
        vals['page_title']="Greeting Page Response"
        airline = self.request.get('airline')
        flightNum = self.request.get('flightNum')
        date = self.request.get('date')
   
        go = self.request.get('gobtn') 
        url = "https://api.flightstats.com/flex/flightstatus/rest/v2/json/flight/tracks/" + airline + "/" + str(flightNum) + "/arr/" + date + "?"
        print flightPath(baseurl=url).read()
        data = json.loads(flightPath(baseurl=url).read())
        logging.info(data)
        
        long = data['flightTracks'][0]['positions'][0]['lon']
        lat = data['flightTracks'][0]['positions'][0]['lat']
        ll = str(round(lat,1)) + ',' + str(round(long, 1))
        logging.info('ll: ' + ll)
        
        vals['ll']=ll
        vals['airline']=airline
        vals['flightNum']=flightNum
        vals['speed']=data['flightTracks'][0]['positions'][0]['speedMph']
        result = fourSquare(params={'ll':ll})
        jsresult = result.read()
        data = json.loads(jsresult)
        logging.info(data)
        if len(data['response']['groups']) > 0:
            vals['venue'] = [display_info(t) for t in data['response']['groups'][0]['items']]        
            logging.info(vals)
            template = JINJA_ENVIRONMENT.get_template('results.html')
            self.response.write(template.render(vals))
            logging.info('data found')
        else:
            # if not, then show the form again with a correction to the user
            vals['prompt'] = "We are not over anything trendy"
            template = JINJA_ENVIRONMENT.get_template('searchform.html')
            self.response.write(template.render(vals))
            logging.info('no data')
        
    
# for all URLs except alt.html, use MainHandler
application = webapp2.WSGIApplication([ \
                                      ('/search', SearchPageHandler),
                                      ('/results', SearchResponseHandler),
                                      ('/home.html', HomePageHandler),
                                      ('/.*', MainHandler)
                                      ],
                                     debug=True)
