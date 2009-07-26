#!/usr/bin/env python

import sys
import httplib2
import flickrapi
import web
from web import form

try:
    import json
except ImportError:
    import simplejson as json


API_KEY="36196c69558d86ae98bf650f42e8f54e"
flickr = flickrapi.FlickrAPI(API_KEY)

http = httplib2.Http()

render = web.template.render('templates/')

form1 = form.Form(
    form.Textbox("username", form.notnull),
    form.Dropdown('service', ['twitter', 'flickr'], form.notnull),
    form.Textbox("search", form.notnull))

def search_twitter(username, search):
    pass

def flickr_hcard(username, info):
    return {
        'service': 'flickr',
        'username': username,
        'fn': info.findtext('realname'),
        'url': info.findtext('profileurl')
    }

def search_flickr(username, search):
    user_id = flickr.people_findByUsername(username=username).find('user').attrib['nsid']
    contacts = flickr.contacts_getPublicList(user_id=user_id, per_page=1000, page=0)
    contacts = contacts.find('contacts').findall('contact')
    cards = []
    for contact in contacts:
        nsid = contact.attrib['nsid']
        name = contact.attrib['username']
        if name.find(search) > -1:
            info = flickr.people_getInfo(user_id=nsid).find('person')
            cards.append(flickr_hcard(name, info))
    return cards

searchers = {
    'twitter': search_twitter,
    'flickr': search_flickr
}

def find_matches(service, username, search):
    cards = searchers[service](username, search)
    ncards = len(cards) if cards else 0
    return render.choose(cards, ncards)

class index:
    """
    Ask the user for their username on a service, and for a search string
    """
    def GET(self):
        return render.form1(form1())

class profile_chooser:
    """
    Ask the user to choose a result to hcardify
    """
    def POST(self):
        form = form1()
        if not form.validates():
            return render.form1(form)
        return find_matches(form.d.service,form.d.username,form.d.search)

def chirag_hcard(data, username):
    card = {}
    card['fn'] = username
    if 'fn' in data['attributes']:
        card['fn'] = data['attributes']['fn']
    card['url'] = data['attributes']['url']
    return card

class hcardify:
    """
    hCardifiy whatever they chose
    """
    def POST(self):
        i = web.input()
        url = "http://chiarg.com/t/net.php"

        card = i.card
        service = i["service-%s" % card]
        username = i["username-%s" % card]

        resp, content = http.request(
            "%s?service=%s&uid=%s" % (url, service, username), "GET")

        data = json.loads(content)

        return render.hcard(chirag_hcard(data, username))

urls = (
    '/', 'index',
    '/search', 'profile_chooser',
    '/consolidate', 'hcardify'
)

app = web.application(urls, globals())

if __name__=="__main__":
    app.run()
