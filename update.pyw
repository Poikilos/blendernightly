#!/usr/bin/env python

import blenderwww as bw
import os
import shutil
import tarfile
import threading
import zipfile
import sys
import traceback

min_indent = "  "

def view_traceback():
    ex_type, ex, tb = sys.exc_info()
    print(min_indent+str(ex_type))
    print(min_indent+str(ex))
    traceback.print_tb(tb)
    del tb

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
base_height = 300
root.geometry('300x' + str(base_height))
master = root
urls = None
count_label = None
only_v = None
only_a = None
v_urls = None  # urls matching specified Blender version (tag)
p_urls = None  # urls matching specified platform flag
a_urls = None  # urls matching specified architecture
version_e = None
refresh_btn = None
pbar = None
del_arc_var = tk.IntVar()
mgr = bw.LinkManager()  # contains mgr.profile_path
d_buttons = []
msg_labels = []
bin_names = ["blender", "blender.exe"]

def push_label(s):
    new_label = tk.Label(master, text=s)
    new_label.pack()
    msg_labels.append(new_label)
    master.update()

shown_progress = 0
def d_progress(evt):
    global shown_progress
    global pbar
    if evt['loaded'] - shown_progress > 1000000:
        shown_progress = evt['loaded']
        pbar['value'] = evt['loaded']
        # print(evt['loaded'])
        # evt['total'] is not implemented
        count_label.config(text="downloading..." +
                           str(int(evt['loaded']/1024/1024)) + "MB..")
    master.update()

def d_done(evt):
    print("Download finished!")
    pbar['value'] = 0
    master.update()

def make_shortcut(meta, program_name):
    ret = True
    desktop_path = mgr.get_desktop_path()
    sc_ext = mgr.get_shortcut_ext()
    bin_path = meta.get('installed_bin')
    if bin_path is None:
        msg = "installed_bin is missing from meta."
        push_label("Cannot create shortcut since")
        push_label(msg)
        print(msg)
        return False
    sc_name = program_name
    version = meta.get('version')
    sc_src_name = program_name
    if version is not None:
        sc_name += " " + version + " Nightly"
    sc_label_s = sc_name[0].upper() + sc_name[1:]
    if sc_ext != "desktop":
        # filename is visible if not "desktop" format, so capitalize
        sc_name = sc_label_s
    if len(sc_ext) > 0:
        sc_name += "." + sc_ext
        sc_src_name += "." + sc_ext
    else:
        print("WARNING: Shortcut extension is unknown for your platform.")
    sc_path = os.path.join(desktop_path, sc_name)

    user_downloads_path = mgr.get_downloads_path()
    bn_path = os.path.join(user_downloads_path, "blendernightly")
    # archives_path = os.path.join(bn_path, "archives")
    # if not os.path.isdir(archives_path):
        # print("  creating: " + archives_path)
        # os.makedirs(archives_path)
    versions_path = os.path.join(bn_path, "versions")

    installed_path = os.path.join(versions_path, meta['id'])
    if sc_ext == "desktop":
        sc_src_path = os.path.join(installed_path, sc_src_name)
        if not os.path.isfile(sc_src_path):
            msg = sc_src_name + " is missing"
            push_label("Cannot create shortcut since")
            push_label(msg)
            print(msg)
            return False
        with open(sc_path, 'w') as outs:
            with open(sc_src_path, "r") as ins:
                for line_orig in ins:
                    line = line_orig.rstrip()
                    exec_flag = "Exec="
                    name_flag = "Name="
                    if line[:len(exec_flag)] == exec_flag:
                        outs.write(exec_flag + bin_path + "\n")
                    elif line[:len(name_flag)] == name_flag:
                        outs.write(name_flag + sc_label_s + "\n")
                    else:
                        outs.write(line + "\n")
        try:
            os.chmod(sc_path, 0o755)  # leading 0o denotes octal
        except:
            print("WARNING: could not mark icon as executable")
        PREFIX = os.path.join(mgr.profile_path, ".local")
        SHARE = os.path.join(PREFIX, "share")
        applications_path = os.path.join(SHARE, "applications")
        if not os.path.isdir(applications_path):
            os.makedirs(applications_path)
        standard_icon_path = os.path.join(
            applications_path,
            "org.blender.blender-nightly.desktop"
        )
        shutil.copyfile(sc_path, standard_icon_path)
    elif sc_ext == "bat":
        outs = open(sc_path, 'w')
        outs.write('"' + bin_path + '"' + "\n")
        outs.close()
    elif sc_ext == "command":
        outs = open(sc_path, 'w')
        outs.write('"' + bin_path + '"' + "\n")
        outs.close()
    else:
        msg = "unknown shortcut format " + sc_ext
        push_label("Cannot create shortcut since")
        push_label(msg)
        print(msg)
    return ret



def d_click(meta):
    global shown_progress
    global pbar
    for btn in d_buttons:
        btn.config(state=tk.DISABLED)
    refresh_btn.config(state=tk.DISABLED)
    btn = meta.get('button')
    if btn is not None:
        btn.pack_forget()
    master.update()
    shown_progress = 0
    print("")
    for label in msg_labels:
        label.pack_forget()
    print("Installing:")
    print("  version: " + meta['version'])
    print("  commit: " + meta['commit'])
    pbar['maximum'] = 200*1024*1024  # TODO: get actual MB count
    pbar['value'] = 0
    url = meta.get('url')
    abs_url = None
    if url is not None:
        abs_url = mgr.absolute_url(url)
    dest_id = mgr.parser.id_from_name(meta['filename'], remove_ext=True)
    # print("new_filename: " + mgr.parser.id_from_url(url))
    dl_name = meta['filename']  # bw.name_from_url(url)
    user_downloads_path = mgr.get_downloads_path()
    bn_path = os.path.join(user_downloads_path, "blendernightly")
    archives_path = os.path.join(bn_path, "archives")
    if not os.path.isdir(archives_path):
        print("  creating: " + archives_path)
        os.makedirs(archives_path)
    versions_path = os.path.join(bn_path, "versions")
    installed_path = os.path.join(versions_path, dest_id)
    print("  install: " + installed_path)  # /2.??-<commit>
    archive_path = os.path.join(archives_path, dl_name)
    for flag_name in bin_names:
        flag_path = os.path.join(installed_path, flag_name)
        if os.path.isfile(flag_path):
            msg = "Already installed " + meta['id'] + "."
            print("  already_installed: true")
            count_label.config(text=msg)
            for btn in d_buttons:
                btn.config(state=tk.NORMAL)
            refresh_btn.config(state=tk.NORMAL)
            master.update()
            return
    if not os.path.isfile(archive_path):
        # abs_url should never be None if file already exists
        print("  downloading: " + abs_url)
        mgr.download(archive_path, abs_url, cb_progress=d_progress,
                     cb_done=d_done)
    else:
        print("  already_downloaded: " + archive_path)
    tar = None
    ext = bw.get_ext(archive_path)
    # if archive_path.lower()[-8:] == ".tar.bz2":
    fmt = None
    fmt_bad = False
    if ext.lower() == "bz2":
        fmt = "r:bz2"
    elif ext.lower() == "gz":
        fmt = "r:gz"
    elif ext.lower() == "xz":
        fmt = "r:xz"
    elif ext.lower() == "zip":
        fmt = "zip"
    else:
        msg = ("ERROR: unknown file format for '" +
               archive_path + "'")
        push_label("unknown format " + ext)
        print(msg)
    if fmt is not None:
        try:
            if fmt != "zip":
                tar = tarfile.open(archive_path, fmt)
            else:
                tar = zipfile.ZipFile(archive_path)
        except:
            fmt_bad = True
            msg = "ERROR: archive not " + fmt
            push_label(msg)
            print(msg)
    if fmt_bad:
        os.remove(archive_path)
        msg = "  Deleting downloaded '" + archive_path + "'..."
        print(msg)
        push_label("Deleted bad download.")
        push_label("Download again.")
    if tar is None:
        for btn in d_buttons:
            btn.config(state=tk.NORMAL)
        refresh_btn.config(state=tk.NORMAL)
        return
    else:
        print("  fmt: " + fmt)
    tmp_path = os.path.join(bn_path, "tmp")
    if not os.path.isdir(tmp_path):
        os.makedirs(tmp_path)
    # for i in tar:
        # tar.extractfile(i)
    ok = False
    try:
        msg = "extracting..."
        count_label.config(text=msg)
        master.update()
        # push_label(msg)
        print(msg)
        tar.extractall(tmp_path)
        ok = True
    except EOFError:
        msg = "ERROR: archive incomplete"
        push_label(msg)
        print(msg)

    msg = "checking tmp..."
    count_label.config(text=msg)
    master.update()
    # push_label(msg)
    print(msg)
    subdirs = bw.get_subdir_names(tmp_path)
    ext_path = tmp_path
    if len(subdirs) == 1:
        ext_path = os.path.join(tmp_path, subdirs[0])
        print("  Detected tar-like (single-folder) archive, used '" +
              ext_path + "' as program root")
    elif len(subdirs) == 0:
        print("  Detected no extracted subdirectories...")
        files = bw.get_file_names(tmp_path)
        if len(files) == 0:
            print("    and found no files either, so failed.")
            ok = False
        else:
            print("    but found files, so using '" + ext_path +
                  "' as program root")
    else:
        print("  Detected windows-like (multi-folder) archive, used '" +
              ext_path + "' as program root")
    tar.close()

    msg = "moving from tmp..."
    count_label.config(text=msg)
    master.update()
    # push_label(msg)
    print(msg)

    remove_tmp = False
    if not ok:
        remove_tmp = True
    if os.path.isdir(installed_path):
        # msg = "Already installed " + meta['id'] + "."
        meta['installed_bin'] = bw.get_installed_bin(
            versions_path,
            meta['id'],
            bin_names
        )
        if make_shortcut(meta, "blender"):
            msg = "Updated Desktop icon."
        else:
            msg = "Update desktop icon failed."
        count_label.config(text=msg)
        master.update()
        remove_tmp = True
    if remove_tmp:
        print("  Deleting temporary '" + tmp_path + "'...")
        shutil.rmtree(tmp_path)
    if ok:
        try:
            shutil.move(ext_path, installed_path)
            count_label.config(text="Finished installing.")
            print("* finished installing")
            master.update()
            meta['installed_bin'] = bw.get_installed_bin(
                versions_path,
                meta['id'],
                bin_names
            )
            if make_shortcut(meta, "blender"):
                msg = "Updated Desktop icon."
            else:
                msg = "Update desktop icon failed."
        except:
            msg = "Could not finish moving"
            push_label(msg)
            count_label.config(text="Installation failed.")
            master.update()
            push_label("to " + meta['id'])
            print("  from (extracted) '" + ext_path + "'")
            print(msg)
            print("  to '" + installed_path + "'")
            view_traceback()
    else:
        msg = "  Deleting downloaded '" + archive_path + "'..."
        print(msg)
        push_label("Deleted bad download.")
        push_label("Download again.")
        os.remove(archive_path)

    for btn in d_buttons:
        btn.config(state=tk.NORMAL)
    refresh_btn.config(state=tk.NORMAL)
    master.update()

def refresh():
    print("")
    print("Downloading the html page...")
    global count_label
    global urls
    global p_urls
    global a_urls
    global version_e
    global pflag_e
    global arch_e
    global d_buttons
    for label in msg_labels:
        label.pack_forget()
    for btn in d_buttons:
        btn.pack_forget()
    d_buttons = []
    count_label.config(text="scraping Downloads page...")
    master.update()
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
                        must_contain="/blender-")
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

    user_downloads_path = mgr.get_downloads_path()
    bn_path = os.path.join(user_downloads_path, "blendernightly")
    archives_path = os.path.join(bn_path, "archives")

    metas = []
    for url in p_urls:
        if (only_a is None) or (only_a in url):
            a_urls.append(url)
            print(url)
            meta = {}
            meta['url'] = url
            meta['filename'] = bw.name_from_url(url)
            meta['id'] = mgr.parser.id_from_url(url, remove_ext=True)
            meta['version'] = mgr.parser.blender_tag_from_url(url)
            meta['commit'] = mgr.parser.blender_commit_from_url(url)
            metas.append(meta)
            try_dl_path = os.path.join(mgr.get_downloads_path(),
                                       meta['filename'])
            dst_dl_path = os.path.join(archives_path,
                                       meta['filename'])
            if (os.path.isfile(try_dl_path) and
                    not os.path.isfile(dst_dl_path)):
                shutil.move(try_dl_path, dst_dl_path)
                msg = ("collected old download '" + meta['filename'] +
                       "' from Downloads to '" + archives_path + "'")
                print(msg)
                push_label("collected old download:")
                push_label(meta['id'])

    if not os.path.isdir(archives_path):
        print("  creating: " + archives_path)
        os.makedirs(archives_path)
    versions_path = os.path.join(bn_path, "versions")

    # get already-downloaded versions and see if they are installed
    # (in case certain downloaded builds are no longer available)
    dl_metas = []
    dl_but_not_inst_count = 0
    print("  existing_downloads: ")  # /2.??-<commit>
    for dl_name in bw.get_file_names(archives_path):
        archive_path = os.path.join(archives_path, dl_name)
        meta = {}
        dl_metas.append(meta)
        dest_id = mgr.parser.id_from_url(dl_name, remove_ext=True)
        installed_path = os.path.join(versions_path, dest_id)
        meta['downloaded'] = True
        # meta['url'] = None
        meta['filename'] = dl_name
        meta['id'] = dest_id
        meta['version'] = mgr.parser.blender_tag_from_url(dl_name)
        meta['commit'] = mgr.parser.blender_commit_from_url(dl_name)
        print("  - '" + installed_path + "'")
        bin_path = bw.get_installed_bin(versions_path, meta['id'],
                                        bin_names)
        if bin_path is not None:
            meta['installed_bin'] = bin_path
        else:
            dl_but_not_inst_count += 1

    status_s = v_msg + "count: " + str(len(a_urls))
    count_label.config(text=status_s)
    master.update()
    print("  matched " + str(len(a_urls)) + " " + a_msg + "url(s)")

    row = 1
    url_installed_count = 0
    for meta in metas:
        # see https://stackoverflow.com/questions/17677649/\
        # tkinter-assign-button-command-in-loop-with-lambda
        user_button = tk.Button(
            master,
            text = "Install " + meta['id'],
            command=lambda meta=meta: d_click(meta)
        )
        meta['button'] = user_button
        d_buttons.append(user_button)
        user_button.pack()  # grid(row = row, column = 0)
        bin_path = bw.get_installed_bin(versions_path, meta['id'],
                                        bin_names)
        if bin_path is not None:
            meta['installed_bin'] = bin_path
            user_button.config(state=tk.DISABLED)
            url_installed_count += 1
        row += 1
    if url_installed_count > 0:
        push_label("(already installed " + str(url_installed_count) +
                   " above)")
    else:
        print("no available downloads are installed yet.")
    if dl_but_not_inst_count > 0:
        push_label("Downloaded but not installed (" +
                   str(dl_but_not_inst_count) + "):")
    for meta in dl_metas:
        # see https://stackoverflow.com/questions/17677649/\
        # tkinter-assign-button-command-in-loop-with-lambda
        if meta.get('installed_bin') is None:
            if meta['id'] in ( meta['id'] for meta in metas ):
                # already is a button
                continue
            # print("  # not installed: " + meta['filename'])
            user_button = tk.Button(
                master,
                text = "Install " + meta['id'],
                command=lambda meta=meta: d_click(meta)
            )
            meta['button'] = user_button
            d_buttons.append(user_button)
            user_button.pack()  # grid(row = row, column = 0)
            row += 1
        # else:
            # print("  # installed: " + meta['filename'])
    global thread1
    thread1 = None
    # refresh_btn.pack(fill="x")
    # refresh_btn.config(fg='black')
    refresh_btn.config(state=tk.NORMAL)
    expand = 0
    old_bottom = count_label.winfo_y() + count_label.winfo_height()
    # if len(d_buttons) > 2:
    master.update()
    # use max heights to resize window,
    # since widget height is 0 if crushed by window:
    btn_h_max = refresh_btn.winfo_height()
    label_h_max = count_label.winfo_height()
    for i in range(0, len(d_buttons)):
        if d_buttons[i].winfo_height() > btn_h_max:
            btn_h_max = d_buttons[i].winfo_height()
        expand += btn_h_max
    for i in range(0, len(msg_labels)):
        if msg_labels[i].winfo_height() > label_h_max:
            label_h_max = msg_labels[i].winfo_height()
        expand += label_h_max
    if expand > 0:
        print("expand: " + str(expand))
        # master.config(height=master.winfo_width()+expand)
        root.geometry('300x' + str(old_bottom+expand))

thread1 = None
def start_refresh():
    global thread1
    # refresh_btn.pack_forget()
    # refresh_btn.config(fg='gray')
    # refresh()
    if thread1 is None:
        print("")
        print("Starting refresh thread...")
        thread1 = threading.Thread(target=refresh, args=())
        refresh_btn.config(state=tk.DISABLED)
        master.update()
        thread1.start()
    else:
        print("WARNING: Refresh is already running.")

def refresh_click():
    start_refresh()

version_e = tk.Entry(master)
version_e.delete(0,tk.END)
version_e.insert(0, mgr.parser.release_version)
version_e.pack()

pflag_e = tk.Entry(master)
pflag_e.delete(0,tk.END)
pflag_e.insert(0, mgr.parser.platform_flag)
pflag_e.pack()

arch_e = tk.Entry(master)
arch_e.delete(0,tk.END)
arch_e.insert(0, mgr.parser.release_arch)
arch_e.pack()

refresh_btn = tk.Button(master, text="Refresh",
                        command=refresh_click)
refresh_btn.pack(fill='x')

pbar = ttk.Progressbar(master)
# orient="horizontal", length=200, mode="determinate"
pbar.pack(fill='x')

count_label = tk.Label(master, text="")
count_label.pack()

del_arc_cb = tk.Checkbutton(master, text="Delete archive after install",
                            variable=del_arc_var)
# del_arc_cb.pack()  # not implemented

root.after(500, start_refresh)
root.mainloop()
