#TODO: warning

class Scopus(object):

    '''
        Scopus Class
    '''
    _search_url_base = "http://api.elsevier.com/content/search/scopus?"
    _author_url_base = "http://api.elsevier.com/content/search/author?"
    _author_retrieve_url_base = "http://api.elsevier.com/content/author/author_id/"
    _abstract_url_base = "http://api.elsevier.com/content/abstract/scopus_id/"

    def __init__(self, apikey=None):
        self.apikey = apikey
        
    def authenticate(self, apikey):
        self.apikey = apikey

    def search_author(self, query_dict, show=True, verbose=False):
        #{{{ search for author
        import warnings
        import numpy as np
        import pandas as pd 
        from urllib import quote
        from urllib2 import urlopen
        from utils import _parse_author
        from bs4 import BeautifulSoup as bs
        #TODO: Verbose mode;
        #      Limited to "and" logic

        '''
            Search for specific authors
            Details: http://api.elsevier.com/documentation/AUTHORSearchAPI.wadl
            Fields: http://api.elsevier.com/content/search/fields/author

            query_dict: a dictoinary containing all the fields as key-value pairs

            returns a list of dictionaries
        '''

        # parse query dictionary
        query = ''
        for key in query_dict:
            query += key + '%28{}%29'.format(quote(query_dict[key])) + '%20and%20'
        query = query[:-9]

        url = self._author_url_base +\
            'apikey={}&query={}&start=0&httpAccept=application/xml'.format(self.apikey, query)


        soup = bs(urlopen(url).read(), 'lxml')
        total = float(soup.find('opensearch:totalresults').text)

        print 'A total number of ', int(total), ' records for the query.'
        starts = np.array([i*25 for i in range(int(np.ceil(total/25.)))])

        author_list = []
        for start in starts:
            search_url = self._author_url_base + \
            'apikey={}&start={}&query={}&httpAccept=application/xml'.format(self.apikey, start, query)

            results = bs(urlopen(search_url).read(), 'lxml')
            entries = results.find_all('entry')
            for entry in entries:
                author_list.append(_parse_author(entry))

        if show:
            df = pd.DataFrame(author_list)
            print df
        
        # }}}
        return author_list

    def retrieve_author(self, author_id, show=True, verbose=False):
        #{{{ retrieve author info
        import warnings
        import numpy as np
        import pandas as pd 
        from urllib import quote
        from urllib2 import urlopen
        from utils import _parse_author_retrieval
        from bs4 import BeautifulSoup as bs
        #TODO: Verbose mode;

        '''
            Search for specific authors
            Details: http://api.elsevier.com/documentation/AuthorRetrievalAPI.wadl

            returns a dictionary
        '''

        # parse query dictionary

        url = self._author_retrieve_url_base +\
            '{}?apikey={}&httpAccept=application/xml'.format(author_id, self.apikey)

        soup = bs(urlopen(url).read(), 'lxml')
        with open('test.xml', 'wb') as testxml:
            testxml.write(soup.prettify())

        author_info = _parse_author_retrieval(soup)

        # nothing find
        if not author_info:
            print 'No matched record found!'
            return None

        if show:
            print 'Name: %s' %(author_info['first-name'] + ' ' + author_info['last-name'])
            print 'Affiliation: %s (%s)' %(author_info['current-affiliation'][0]['name'],\
                    author_info['current-affiliation'][0]['address'])
        
        # }}}
        return author_info

    def search_author_publication(self, author_id, show=True, verbose=False):
        #{{{ search author's publications using authid
        import warnings
        import numpy as np
        import pandas as pd 
        from urllib2 import urlopen
        from utils import trunc, _parse_author, _parse_xml
        from bs4 import BeautifulSoup as bs
        #TODO: Verbose mode

        '''
            Search author's publication by author id
            returns a list of dictionaries
        '''
        url = self._search_url_base + 'apikey={}&query=au-id({})&start=0&httpAccept=application/xml'.format(self.apikey, author_id)
        soup = bs(urlopen(url).read(), 'lxml')
        total = float(soup.find('opensearch:totalresults').text)
        print 'A toal number of ', int(total), ' records for author ', author_id
        starts = np.array([i*25 for i in range(int(np.ceil(total/25.)))])

        publication_list = []
        for start in starts:
            search_url = self._search_url_base + 'apikey={}&start={}&query=au-id({})&httpAccept=application/xml'.format(self.apikey, start, author_id)
            results = bs(urlopen(search_url).read(), 'lxml')
            entries = results.find_all('entry')
            for entry in entries:
                publication_list.append(_parse_xml(entry))

        if show:
            #pd.set_printoptions('display.expand_frame_repr', False)
            #print df['title'].to_string(max_rows=10, justify='left')
            df = pd.DataFrame(publication_list)
            titles = np.array(df['title'])
            for i in range(titles.size):
                t = trunc(titles[i])
                print i, t
        # }}}
        return publication_list
    
    def search_abstract(self, scopus_id, force_ascii=True, show=True, verbose=False):
        #{{{ search for abstracts
        import warnings
        import numpy as np
        import pandas as pd
        from urllib2 import urlopen
        from utils import _parse_xml
        from bs4 import BeautifulSoup as bs
        #TODO: Verbose mode; Fixing possible bugs

        '''
            returns a dictionary
        '''

        abstract_url = self._abstract_url_base + scopus_id + "?APIKEY={}&httpAccept=application/xml".format(self.apikey)

        # parse abstract xml
        try:
            abstract = bs(urlopen(abstract_url).read(), 'lxml')
            abstract_text = abstract.find('ce:para').text
            title = abstract.find('dc:title').text
        except:
            print 'Fail to find abstract!'
            return None
        
        # force encoding as utf-8
        if force_ascii:
            abstract_text = abstract_text.encode('ascii', 'ignore')
            title = title.encode('ascii', 'ignore')

        if show:
            print "\n####Retrieved info for publication %s (id: %s)####" % (title, scopus_id)
            print 'abstract: ', abstract_text
            print 
        #}}}
        return {'text':abstract_text, 'id':scopus_id,'title': title}

