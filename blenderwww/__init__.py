#!/usr/bin/env python
python_mr = 3  # major revision
try:
    import urllib.request
    request = urllib.request
except:
    # python2
    python_mr = 2
    import urllib2 as urllib
    request = urllib
try:
    from html.parser import HTMLParser
except:
    # python2
    from HTMLParser import HTMLParser
import platform
import os

# create a subclass and override the handler methods
class DownloadPageParser(HTMLParser):

    def __init__(self, meta):
        # avoid "...instance has no attribute rawdata":
        #   Old way:
        #     HTMLParser.__init__(self)
        #   On the next commented line, python2 would say:
        #       "argument 1 must be type, not classobj"
        #     super(DownloadPageParser, self).__init__()
        try:
            super().__init__()
            # print("Used python3 super syntax")
        except:
            # python2
            HTMLParser.__init__(self)
            # print("Used python2 super syntax")

        self.urls = []
        self.verbose = False
        self.must_contain = None
        self.release_version = "2.80"  # find href /download//blender-*
        self.meta = meta
        self.tag = None
        self.tag_stack = []
        # Linux, Darwin, or Windows:
        platform_system = platform.system()
        self.os_name = platform_system.lower()
        self.platform_flag = None
        self.release_arch = "x86_64"
        self.os_flags = {"Win64":"windows", "Win32":"windows",
                         "linux":"linux", "OSX":"macos"}
        if self.os_name == "darwin":
            self.os_name = "macos"  # change to Blender build naming
            # parent css class of section (above ul): "platform-macOS"
            self.platform_flag = "-OSX"
            self.release_arch = "x86_64"
        elif self.os_name == "windows":
            # parent css class of section (above ul): "platform-win"
            self.platform_flag = "-win64"
            self.release_arch = "win64"
        elif self.os_name == "linux":
            # parent css class of section (above ul): "platform-linux"
            self.platform_flag = "-linux"
            self.release_arch = "x86_64"
        else:
            print("WARNING: unknown system '" + platform_system + "'")

        self.os_release = platform.release()
        self.dl_os_name = None

    def handle_decl(self, decl):
        self.urls = []
        print("CLEARED dl list since found document decl: " + decl)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "html":
            self.urls = []
            print("CLEARED dl list since found <html...")
        if self.verbose:
            print(" " * len(self.tag_stack) + "push: " + str(tag))
        self.tag_stack.append(tag)
        # attrs is an array of (name, value) tuples:
        attr_d = dict(attrs)
        href = attr_d.get("href")
        if href is not None:
            if (self.must_contain is None) or (self.must_contain in href):
                # print(href)
                self.urls.append(href)
        if self.verbose:
            # print(" " * len(self.tag_stack) + "attrs: " + str(attrs))
            print(" " * len(self.tag_stack) + "attr_d: " + str(attr_d))

        self.tag = tag

    def handle_endtag(self, tag):
        if tag.lower() != self.tag_stack[-1].lower():
            found = None
            for i in range(1, len(self.tag_stack)+1):
                if tag.lower() == self.tag_stack[-i].lower():
                    found = i
                    break
            if found is not None:
                for i in range(found, len(self.tag_stack)+1):
                    if self.verbose:
                        print(" " * len(self.tag_stack) +
                              "unwind: (" + self.tag_stack[-1] +
                              " at ) " + str(tag))
                    self.tag_stack.pop()
            else:
                if self.verbose:
                    print(" " * len(self.tag_stack) + "UNEXPECTED: " +
                          str(tag))
        else:
            self.tag_stack.pop()
            if self.verbose:
                print(" " * len(self.tag_stack) + ":" + str(tag))

    def handle_data(self, data):
        if self.verbose:
            print(" " * len(self.tag_stack) + "data:" + str(data))

    def blender_dir_from_url(self, url):
        only_v = self.release_version
        only_p = self.platform_flag
        only_a = self.release_arch
        filename = url
        slash_i = url.rfind("/")
        if slash_i >= 0:
            filename = url[slash_i+1:]
        ret = filename
        ret = ret.replace("blender-", "")
        if only_p is not None:
            if "win" not in only_p.lower():
                ret = ret.replace(only_p, "")
        if only_a is not None:
            if "win" not in only_a.lower():
                ret = ret.replace("-"+only_a, "")
        gc_i = ret.find("-glibc")
        if gc_i > -1:
            ret = ret[:gc_i]
        for i in range(6, 99):
            osx = "-10." + str(i)
            ext_i = ret.find(osx)
            if ext_i > -1:
                ret = ret[:ext_i]
        for ext in [".zip", ".dmg", ".tar.gz", ".tar.bz2"]:
            ext_i = ret.find(ext)
            if ext_i > -1:
                ret = ret[:ext_i]
        return ret

    def blender_tag_from_url(self, url):
        tag_and_commit = self.blender_dir_from_url(url)
        h_i = tag_and_commit.find("-")
        version_s = tag_and_commit
        if h_i > -1:
            version_s = tag_and_commit[:h_i]
        return version_s

    def blender_commit_from_url(self, url):
        tag_and_commit = self.blender_dir_from_url(url)
        h_i = tag_and_commit.find("-")
        commit_s = tag_and_commit
        if h_i > -1:
            commit_s = tag_and_commit[h_i+1:]
        return commit_s

class LinkManager:

    def __init__(self):
        self.meta = {}
        self.html_url = "https://builder.blender.org/download/"
        self.parser = DownloadPageParser(self.meta)
        profile_path = None
        appdata_path = None
        if "windows" in platform.system().lower():
            if 'USERPROFILE' in os.environ:
                profile_path = os.environ['USERPROFILE']
                appdatas_path = os.path.join(profile_path, "AppData")
                appdata_path = os.path.join(appdatas_path, "Local")
            else:
                print("ERROR: missing HOME variable")
        else:
            if 'HOME' in os.environ:
                profile_path = os.environ['HOME']
                appdata_path = os.path.join(profile_path, ".config")
            else:
                print("ERROR: missing HOME variable")
        self.profile_path = profile_path
        self.appdata_path = appdata_path

    def name_from_url(self, url):
        filename = url
        slash_i = url.rfind("/")
        if slash_i >= 0:
            filename = url[slash_i+1:]
        return filename

    def get_urls(self, verbose=False, must_contain=None):
        # self.parser.urls = []  # done automatically on BODY tag
        # python2 way: `urllib.urlopen(self.html_url)`
        response = request.urlopen(self.html_url)
        dat = response.read()
        self.parser.must_contain = must_contain
        self.parser.verbose = verbose
        # print("GOT:" + dat)
        # Decode dat to avoid error on Python 3:
        #   htmlparser self.rawdata  = self.rawdata + data
        #   TypeError: must be str not bytes
        self.parser.feed(dat.decode("UTF-8"))
        return self.parser.urls

    def get_downloads_path(self):
        return os.path.join(self.profile_path, "Downloads")

    def absolute_url(self, rel_href):
        route_i = rel_href.find("//")
        if route_i > -1:
            # assume before '//' is route (not real directory) & remove:
            rel_href = rel_href[route_i+2:]
        if (self.html_url[-1] == "/") and (rel_href[0] == "/"):
            rel_href = rel_href[1:]
        return self.html_url + rel_href

if __name__ == "__main__":
    print("You must import this module and call get_meta() to use it"
          "--maybe you meant to run update.pyw")
