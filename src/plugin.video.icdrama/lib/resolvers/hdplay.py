import re
import json
from urllib.parse import unquote
from urllib.parse import urlparse
import base64
import requests
from bs4 import BeautifulSoup
import resolveurl
from resolveurl import common
from resolveurl.resolver import ResolveUrl, ResolverError
from resolveurl.lib import helpers
import xbmc
from .. import common as cmn

class HdPlay(ResolveUrl):
    name = 'HDplay'
    domains = [ 'hdplay.se', 'drive.adramas.se']
    pattern = '(?://|\.)(hdplay\.se|drive\.adramas\.se)/(.+)'


    def __init__(self):
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA}


    def get_media_url(self, host, media_id):
        url = self.get_url(host, media_id)
        # xbmc.log(str([host, media_id, url]), xbmc.LOGERROR)
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            html = response.content.decode("utf-8")
            # capture everything, regardless of single or double quotes
            match = re.search(r'var\s+video_url\s*=\s*"([^\\"]+)"', html)
            if match:
                video_url = 'http://' + host + match.group(1)
                return video_url + helpers.append_headers(self.headers)

            # these are for after the hdplay-cache server change
            video_url = None

            if video_url is None:
                match = re.search(r'<div\s+id=video_url\s+.+?>(.+?)</div>', html)
                if match:
                    video_url = match.group(1)

            if video_url is None:
                lines = html.splitlines()
                # hack assuption that higher quality video at the bottom
                lines.reverse()
                for line in lines:
                    line = line.strip()
                    if line.startswith('/hdplay-cache/'):
                        video_url = line
                        break

            # apply fixup to the extracted video URL
            if video_url:
                if re.match(r'^.+\?v=\d$', video_url):
                    video_url = video_url[0:-len("?v=1")]
                video_url = 'http://' + host + video_url
                return video_url + helpers.append_headers(self.headers)
            xbmc.log(f"html: {html}", xbmc.LOGERROR)


        raise ResolverError(f"Unable to resolve url in hdplay: {response}")

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, 'http://{host}/{media_id}')

    @classmethod
    def _is_enabled(cls):
        return True
