import urllib2
import urllib

class Crawler:
    """
    A internet information retrieval package
    """
    
    def __init__(self):
        self._processed_urls = []
    
    def fetchurl(self, url, params = {}, method = "GET"):
        """ 
        Fetch a page
        """
        
        string_params = urllib.urlencode(params)
        if params and method == "GET":
            url += "?" + string_params
        
        try:
            req = urllib2.Request(url, None)
            req.add_header('User-agent', 
                           'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.231 Safari/534.10')
            if params and method == "POST":
                req.add_data(params)

            url_obj = urllib2.urlopen(req)
            html_data = url_obj.read();

            url_obj.close()
        except:
            # do some logging here
            return False
        
        return html_data
