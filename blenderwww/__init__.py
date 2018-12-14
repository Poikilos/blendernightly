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


def get_subdir_names(folder_path, hidden=False):
    ret = None
    if os.path.exists(folder_path):
        ret = []
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if ((hidden or sub_name[:1]!=".") and
                    (os.path.isdir(sub_path))):
                ret.append(sub_name)
    return ret

def get_file_names(folder_path, hidden=False):
    ret = None
    if os.path.exists(folder_path):
        ret = []
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if ((hidden or sub_name[:1]!=".") and
                    (os.path.isfile(sub_path))):
                ret.append(sub_name)
    return ret

def name_from_url(url):
    filename = url
    slash_i = url.rfind("/")
    if slash_i >= 0:
        filename = url[slash_i+1:]
    return filename

def get_ext(filename):
    ext = ""
    dot_i = filename.rfind('.')
    if dot_i > -1:
        ext = filename[dot_i+1:]
    return ext

# program_name is same as dest_id
def get_installed_bin(programs_path, dest_id, flag_names):
    found = False
    ret = None
    versions_path = programs_path
    for flag_name in flag_names:
        installed_path = os.path.join(versions_path, dest_id)
        flag_path = os.path.join(installed_path, flag_name)
        if os.path.isfile(flag_path):
            found = True
            ret = flag_path
            # print("    found: '" + flag_path + "'")
            break
        else:
            pass
            # print("    not_found: '" + flag_path + "'")
    return ret

def is_installed(programs_path, dest_id, flag_names):
    path = get_installed_bin(programs_path, dest_id, flag_names)
    return (path is not None)

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
        self.extensions = [".zip", ".dmg", ".tar.gz", ".tar.bz2"]
        self.closers = ["-glibc"]
        self.openers = ["blender-"]
        self.remove_this_dot_any = ["-10."]
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
            self.platform_flag = "OSX"
            self.release_arch = "x86_64"  # always x86_64
        elif self.os_name == "windows":
            # parent css class of section (above ul): "platform-win"
            self.platform_flag = "win64"
            self.release_arch = "win64"
            # self.release_arch = "win32"
        elif self.os_name == "linux":
            # parent css class of section (above ul): "platform-linux"
            self.platform_flag = "linux"
            self.release_arch = "x86_64"
            # self.release_arch = "i686"
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

    def id_from_name(self, filename, remove_arch=True,
                     remove_win_arch=False, remove_ext=False,
                     remove_openers=True, remove_closers=True):
        only_v = self.release_version
        only_p = self.platform_flag
        only_a = self.release_arch
        ret = filename
        if remove_openers:
            for opener in self.openers:
                # ret = ret.replace(opener, "")
                o_i = ret.find(opener)
                if o_i == 0:
                    ret = ret[len(opener):]
        # only remove platform and arch if not Windows since same
        # (only way to keep them & allow installing 64&32 concurrently)
        if only_p is not None:
            if remove_win_arch or ("win" not in only_p.lower()):
                ret = ret.replace("-"+only_p, "")
        if only_a is not None:
            if remove_win_arch or ("win" not in only_a.lower()):
                ret = ret.replace("-"+only_a, "")
        if remove_closers:
            for closer in self.closers:
                c_i = ret.find(closer)
                if c_i > -1:
                    next_i = -1
                    dot_i = ret.find(".", c_i+1)
                    hyphen_i = ret.find("-", c_i+1)
                    if dot_i > -1:
                        next_i = dot_i
                    if hyphen_i > -1:
                        if next_i > -1:
                            if hyphen_i < next_i:
                                next_i = hyphen_i
                        else:
                            next_i = hyphen_i
                    if next_i > -1:
                        # don't remove extension or other chunks
                        ret = ret[:c_i] + ret[next_i:]
                    else:
                        ret = ret[:c_i]
                    break
        for rt in self.remove_this_dot_any:
            for i in range(0, 99):
                osx = rt + str(i)
                ext_i = ret.find(osx)
                if ext_i > -1:
                    ret = ret[:ext_i]
                    break
        if remove_ext:
            for ext in self.extensions:
                ext_i = ret.find(ext)
                if ext_i > -1:
                    ret = ret[:ext_i]
        return ret

    def id_from_url(self, url, remove_arch=True,
                    remove_win_arch=False, remove_ext=False,
                    remove_openers=True, remove_closers=True):
        filename = name_from_url(url)
        return self.id_from_name(
            filename,
            remove_arch=remove_arch,
            remove_win_arch=remove_win_arch,
            remove_ext=remove_ext,
            remove_openers=remove_openers,
            remove_closers=remove_closers
        )

    def blender_tag_from_url(self, url):
        tag_and_commit = self.id_from_url(url, remove_ext=True)
        h_i = tag_and_commit.find("-")
        version_s = tag_and_commit
        if h_i > -1:
            version_s = tag_and_commit[:h_i]
        return version_s

    def blender_commit_from_url(self, url):
        tag_and_commit = self.id_from_url(url, remove_ext=True)
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
        self.shortcut_ext = "desktop"
        profile_path = None
        appdata_path = None
        if "windows" in platform.system().lower():
            self.shortcut_ext = "bat"
            if 'USERPROFILE' in os.environ:
                profile_path = os.environ['USERPROFILE']
                appdatas_path = os.path.join(profile_path, "AppData")
                appdata_path = os.path.join(appdatas_path, "Local")
            else:
                print("ERROR: missing USERPROFILE variable")
        else:
            if "darwin" in platform.system().lower():
                self.shortcut_ext = "command"
            if 'HOME' in os.environ:
                profile_path = os.environ['HOME']
                appdata_path = os.path.join(profile_path, ".config")
            else:
                print("ERROR: missing HOME variable")
        self.profile_path = profile_path
        self.appdata_path = appdata_path

    def get_shortcut_ext(self):
        return self.shortcut_ext

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

    def download(self, file_path, url, cb_progress=None, cb_done=None,
                 chunk_len=16*1024):
        response = request.urlopen(url)
        evt = {}
        evt['loaded'] = 0
        # evt['total'] is not implemented (would be from contentlength
        # aka content-length)
        with open(file_path, 'wb') as f:
            while True:
                chunk = response.read(chunk_len)
                if not chunk:
                    break
                evt['loaded'] += chunk_len
                if cb_progress is not None:
                    cb_progress(evt)
                f.write(chunk)
        if cb_done is not None:
            cb_done(evt)

    def get_downloads_path(self):
        return os.path.join(self.profile_path, "Downloads")

    def get_desktop_path(self):
        return os.path.join(self.profile_path, "Desktop")

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
