import os
import crawler

from BeautifulSoup import BeautifulSoup
from django.conf import settings

def bing_xml_location():
    return os.path.join(settings.BING_WALLPAPER_FOLDER, 
                        settings.BING_XML_FILE)

def download_bing_xml():
    """Download Bing XML, store locally, once per day"""

    localxml = bing_xml_location()

    try:
        c = crawler.Crawler()
        xmlcontent = c.fetchurl('http://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=en-US')

        f = open(localxml, 'w')
        f.write(xmlcontent)
        f.close()

        return True
    except:
        pass

    return False

def download_bing_wallpaper(save_to=None):
    """Download bing photo of the day"""

    if not save_to:
        save_to = os.path.join(settings.BING_WALLPAPER_FOLDER,
                                settings.BING_PHOTO_FILE)
    if os.path.exists(save_to): return True

    # downloading the xml
    bing_xml = download_bing_xml()
    if not bing_xml: return None

    # interpret the xml, extract the image and copyright
    with open(bing_xml_location()) as xml_file:
        soup = BeautifulSoup(xml_file.read())
        try: bing_image = 'http://www.bing.com%s' % soup.images.image.url.string
        except: bing_image = None
        
        if not bing_image: 
            return None

        return {'image': bing_image,
                'copy': soup.images.image.copyright.string,
                'copystr': soup.images.image.copyrightlink.string}
