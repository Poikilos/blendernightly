#!/usr/bin/env python

import blenderwww as bw
import os

try:
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk
except ImportError:  # Python 2
    import Tkinter as tk
    import tkFont
    import ttk

root = None
try:
    root = tk.Tk()
except:
    print("FATAL ERROR: Cannot use tkinter from terminal")
    exit(1)

root.wm_title("Blender Nightly Update")
root.geometry('300x300')
this_root = root
urls = None
count_label = None
only_v = None
only_a = None
v_urls = None  # urls matching specified Blender version (tag)
p_urls = None  # urls matching specified platform flag
a_urls = None  # urls matching specified architecture
version_e = None
mgr = bw.LinkManager()
d_buttons = []

def d_click(meta):
    print("Installing:")
    print("  version: " + meta['version'])
    print("  commit: " + meta['commit'])
    url = meta['url']
    abs_url = mgr.absolute_url(url)
    dest_name = mgr.parser.blender_dir_from_url(url)
    dl_name = mgr.name_from_url(url)
    downloads_path = mgr.get_downloads_path()
    if not os.path.isdir(downloads_path):
        print("  missing: " + downloads_path)
        os.makedirs(downloads_path)
    dest_path = os.path.join(downloads_path, dest_name)
    print("  destination: " + dest_path)
    dest_f_path = os.path.join(downloads_path, dl_name)
    if not os.path.isfile(dest_f_path):
        print("  downloading: " + abs_url)
    else:
        print("  using_existing: " + dest_f_path)


def refresh():
    print()
    print("Downloading the html page...")
    global count_label
    global urls
    global p_urls
    global a_urls
    global version_e
    global pflag_e
    global arch_e
    global d_buttons
    only_v = version_e.get().strip()
    if len(only_v) == 0:
        only_v = None
    only_p = pflag_e.get().strip()
    if len(only_p) == 0:
        only_p = None
    only_a = arch_e.get().strip()
    if len(only_a) == 0:
        only_a = None
    mgr.parser.release_version = only_v
    mgr.parser.platform_flag = only_p
    mgr.parser.release_arch = only_a
    v_urls = []
    p_urls = []
    a_urls = []
    urls = mgr.get_urls(verbose=False,
                        must_contain="download//blender-")
    print("Of the total " + str(len(urls)) + " blender download url(s)")
    count = 0
    v_msg = ""
    a_msg = ""
    p_msg = ""
    print("all:")
    if only_v is not None:
        v_msg = only_v + " "
    if only_a is not None:
        a_msg = only_a + " "
    for url in urls:
        if (only_v is None) or (only_v in url):
            v_urls.append(url)
            print(url)
    # count_label.config(text=v_msg+"count: "+str(len(v_urls)))
    print("  matched " + str(len(v_urls)) + " " + v_msg + "url(s)")

    print("matching version (tag):")
    for url in v_urls:
        if (only_p is None) or (only_p in url):
            p_urls.append(url)
            print(url)

    print("  matched " + str(len(p_urls)) + " " + p_msg + "url(s)")

    metas = []
    for url in p_urls:
        if (only_a is None) or (only_a in url):
            a_urls.append(url)
            print(url)
            meta = {}
            meta['url'] = url
            meta['filename'] = mgr.name_from_url(url)
            meta['name'] = mgr.parser.blender_dir_from_url(url)
            meta['version'] = mgr.parser.blender_tag_from_url(url)
            meta['commit'] = mgr.parser.blender_commit_from_url(url)
            metas.append(meta)

    count_label.config(text=v_msg+"count: "+str(len(a_urls)))
    print("  matched " + str(len(a_urls)) + " " + a_msg + "url(s)")

    row = 1
    for btn in d_buttons:
        btn.pack_forget()
    d_buttons = []
    for meta in metas:
        # see https://stackoverflow.com/questions/17677649/\
        # tkinter-assign-button-command-in-loop-with-lambda
        user_button = tk.Button(
                this_root,
                text = "Install " + meta['name'],
                command=lambda meta=meta: d_click(meta)
        )
        d_buttons.append(user_button)
        user_button.pack()  # grid(row = row, column = 0)
        row += 1

def refresh_click():
    refresh()

version_e = tk.Entry(this_root)
version_e.delete(0,tk.END)
version_e.insert(0, mgr.parser.release_version)
version_e.pack()

pflag_e = tk.Entry(this_root)
pflag_e.delete(0,tk.END)
pflag_e.insert(0, mgr.parser.platform_flag)
pflag_e.pack()

arch_e = tk.Entry(this_root)
arch_e.delete(0,tk.END)
arch_e.insert(0, mgr.parser.release_arch)
arch_e.pack()

refresh_btn = tk.Button(this_root, text="Refresh",
                        command=refresh_click)
refresh_btn.pack(fill='x')

count_label = tk.Label(this_root, text="")
count_label.pack()

root.after(500, refresh)
root.mainloop()
