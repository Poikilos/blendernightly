#!/usr/bin/env python

import blenderwww as bw
import os
import shutil
import tarfile
import threading
import zipfile
import sys
import traceback
import tempfile
import subprocess

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
dl_buttons = []
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
    err = evt.get('error')
    if err is None:
        print("Download finished!")
    else:
        print("Download stopped due to: {}".format(err))
    pbar['value'] = 0
    master.update()


def make_shortcut(meta, program_name, uninstall=False):

    ret = True
    desktop_path = mgr.get_desktop_path()
    sc_ext = mgr.get_shortcut_ext()
    bin_path = meta.get('installed_bin')
    action = "create"
    if uninstall:
        action = "uninstall"
    if not uninstall:
        if bin_path is None:
            msg = "installed_bin is missing from meta."
            push_label("{} shortcut failed since".format(action))
            push_label(msg)
            print(msg)
            return False
    print("* {} shortcut...".format(action))
    desktop_sc_name = program_name
    version = meta.get('version')
    sc_src_name = program_name
    if version is not None:
        desktop_sc_name += " " + version + " Nightly"
    sc_label_s = desktop_sc_name[0].upper() + desktop_sc_name[1:]
    if sc_ext != "desktop":
        # filename is visible if not "desktop" format, so capitalize
        desktop_sc_name = sc_label_s
    if len(sc_ext) > 0:
        desktop_sc_name += "." + sc_ext
        sc_src_name += "." + sc_ext
    else:
        print("WARNING: The shortcut extension is unknown for your"
              " platform.")
    desktop_sc_path = os.path.join(desktop_path, desktop_sc_name)

    user_downloads_path = mgr.get_downloads_path()
    bn_path = os.path.join(user_downloads_path, "blendernightly")
    # archives_path = os.path.join(bn_path, "archives")
    # if not os.path.isdir(archives_path):
        # print("  {}: ".format(action) + archives_path)
        # os.makedirs(archives_path)
    versions_path = os.path.join(bn_path, "versions")

    installed_path = os.path.join(versions_path, meta['id'])
    print("* id: {}".format(meta['id']))
    if sc_ext == "desktop":
        PREFIX = os.path.join(mgr.profile_path, ".local")
        BIN = os.path.join(PREFIX, "bin")
        sh_path = os.path.join(BIN, "blendernightly-logged.sh")
        logexec = bin_path
        CACHES = os.path.join(mgr.profile_path, ".cache")
        CACHE = os.path.join(CACHES, "blender-nightly")
        if not os.path.isdir(CACHE):
            os.makedirs(CACHE)
        if bin_path is not None:
            logexec += ' > ' + CACHE + '/blender-`date "+%Y-%m-%d"`-error.log 2>&1'
        if not uninstall:
            with open(sh_path, 'w') as outs:
                outs.write("#!/bin/sh" + "\n")
                outs.write(logexec + "\n")
            os.chmod(sh_path, 0o755)
            print("* wrote {}".format(sh_path))
            if os.path.isfile(desktop_sc_path):
                print("* removing {}".format(desktop_sc_path))
                os.remove(desktop_sc_path)
            print("* writing {}...".format(desktop_sc_path))
            sc_src_path = os.path.join(installed_path, sc_src_name)
            if not os.path.isfile(sc_src_path):
                msg = sc_src_name + " is missing"
                push_label("ERROR: {} shortcut failed since"
                           "".format(action))
                push_label(msg)
                print(msg)
                return False
            with open(desktop_sc_path, 'w') as outs:
                with open(sc_src_path, "r") as ins:
                    for line_orig in ins:
                        line = line_orig.rstrip()
                        exec_flag = "Exec="
                        name_flag = "Name="
                        if line[:len(exec_flag)] == exec_flag:
                            exec_line = exec_flag + sh_path
                            print("  - {}".format(exec_line))
                            outs.write(exec_line + "\n")
                        elif line[:len(name_flag)] == name_flag:
                            name_line = name_flag + sc_label_s
                            print("  - {}".format(name_line))
                            outs.write(name_line + "\n")
                        else:
                            outs.write(line + "\n")
            try:
                # Keep the desktop shortcut and mark it executable.
                os.chmod(desktop_sc_path, 0o755)
                # ^ leading 0o denotes octal
            except:
                print("WARNING: could not mark icon as executable")
        else:
            pass
            # print("* {} is skipping shortcut writing".format(action))

        PREFIX = os.path.join(mgr.profile_path, ".local")
        SHARE = os.path.join(PREFIX, "share")
        applications_path = os.path.join(SHARE, "applications")
        if not uninstall:
            if not os.path.isdir(applications_path):
                os.makedirs(applications_path)
        sc_name = "org.blender.blender-nightly.desktop"
        sc_path = os.path.join(
            applications_path,
            sc_name
        )
        desktop_installer = "xdg-desktop-menu"
        u_cmd_parts = [desktop_installer, "uninstall", sc_path]
        if not uninstall:
            tmp_sc_dir_path = tempfile.mkdtemp()
            tmp_sc_path = os.path.join(tmp_sc_dir_path,
                                       sc_name)
            shutil.copy(desktop_sc_path, tmp_sc_path)
            print("* using {} for {}".format(desktop_sc_path, tmp_sc_path))
            # ^ XDG requires this naming.
        # "--novendor" can force it, but still not if there are spaces.

        # Always remove the old icons first, even if not uninstall:

        if os.path.isfile(desktop_sc_path):
            print("* removing {}...".format(desktop_sc_path))
            os.remove(desktop_sc_path)
        elif uninstall:
            print("* there is no {}...".format(desktop_sc_path))

        if os.path.isfile(sc_path):
            # print("* removing shortcut \"{}\"".format(sc_path))
            # os.remove(desktop_sc_path)
            print("* uninstalling shortcut \"{}\"".format(sc_path))
            subprocess.run(u_cmd_parts)
            # ^ Using only the name also works: sc_name])
            # ^ Using the XDG uninstall subcommand ensures that the
            #   icon in the OS application menu gets updated if the
            #   shortcut was there but different (such as with a
            #   different version number or otherwise different
            #   name).
        elif uninstall:
            print("* there is no {}...".format(sc_path))
        # else:
        #     print("* there's no {}...".format(sc_path))
        if not uninstall:
            sc_cmd_parts = [desktop_installer, "install", tmp_sc_path]
            install_proc = subprocess.run(sc_cmd_parts)
            inst_msg = "OK"
            os.remove(tmp_sc_path)
            if install_proc.returncode != 0:
                inst_msg = "FAILED"
                print("* {}...{}".format(" ".join(sc_cmd_parts),
                                         inst_msg))
                print("  - attempting to copy to {} manually..."
                      "".format(sc_path))
                shutil.copyfile(desktop_sc_path, sc_path)
            else:
                print("* {}...{}".format(" ".join(sc_cmd_parts),
                                         inst_msg))

    elif sc_ext == "bat":
        if not uninstall:
            outs = open(desktop_sc_path, 'w')
            outs.write('"' + bin_path + '"' + "\n")
            outs.close()
        else:
            if os.path.isfile(desktop_sc_path):
                print("* removing {}...".format(desktop_sc_path))
                os.remove(desktop_sc_path)
    elif sc_ext == "command":
        if not uninstall:
            outs = open(desktop_sc_path, 'w')
            outs.write('"' + bin_path + '"' + "\n")
            outs.close()
        else:
            if os.path.isfile(desktop_sc_path):
                print("* removing {}...".format(desktop_sc_path))
                os.remove(desktop_sc_path)
    else:
        msg = "unknown shortcut format " + sc_ext
        push_label("{} shortcut failed since".format(action))
        push_label(msg)
        print(msg)
    return ret


def uninstall_click(meta):
    print("* uninstalling {}".format(meta))
    # make_shortcut(meta, "blender", uninstall=True)
    d_click(meta, uninstall=True)


def remove_ar_click(meta):
    print("* uninstalling {}".format(meta))
    # make_shortcut(meta, "blender", uninstall=True)
    d_click(meta, uninstall=False, remove_download=True)


def d_click(meta, uninstall=False, remove_download=False):
    global shown_progress
    global pbar
    update_past_verb = "Updated"
    update_present_verb = "Updating"
    action_present_verb = "Installing"
    action = "install"
    enable_install = True
    if uninstall:
        enable_install = False
        update_past_verb = "Removed"
        update_present_verb = "Removing"
        action_present_verb = "Uninstalling"
        action = "uninstall"
    if remove_download:
        enable_install = False
    for btn in dl_buttons:
        btn.config(state=tk.DISABLED)
    refresh_btn.config(state=tk.DISABLED)
    btn = meta.get('button')
    uninstall_btn = meta.get("uninstall_button")
    if not uninstall:
        if btn is not None:
            btn.pack_forget()
    else:
        if remove_download:
            if btn is not None:
                btn.pack_forget()
        if uninstall_btn is not None:
            uninstall_btn.pack_forget()

    master.update()
    shown_progress = 0
    print("")
    for label in msg_labels:
        label.pack_forget()
    print(action_present_verb + ":")
    print("  version: " + meta['version'])
    print("  commit: " + meta['commit'])
    pbar['maximum'] = 200*1024*1024  # TODO: get actual MB count
    pbar['value'] = 0
    url = meta.get('url')
    abs_url = None
    if url is not None:
        abs_url = mgr.absolute_url(url)

    dest_id = meta.get('id')
    if dest_id is None:
        dest_id = mgr.parser.id_from_name(meta['filename'],
                                          remove_ext=True)
    # print("new_filename: " + mgr.parser.id_from_url(url))
    dl_name = meta.get('filename')  # bw.name_from_url(url)
    user_downloads_path = mgr.get_downloads_path()
    bn_path = os.path.join(user_downloads_path, "blendernightly")
    archives_path = os.path.join(bn_path, "archives")
    if not os.path.isdir(archives_path):
        print("  creating: " + archives_path)
        os.makedirs(archives_path)
    versions_path = os.path.join(bn_path, "versions")
    installed_path = os.path.join(versions_path, dest_id)
    print("  {}: {}".format(action, installed_path))  # /2.??-<commit>
    archive_path = None
    if dl_name is not None:
        archive_path = os.path.join(archives_path, dl_name)
    if enable_install:
        for flag_name in bin_names:
            flag_path = os.path.join(installed_path, flag_name)
            if os.path.isfile(flag_path):
                msg = "Already installed " + meta['id'] + "."
                print("  already_installed: true")
                count_label.config(text=msg)
                for btn in dl_buttons:
                    btn.config(state=tk.NORMAL)
                refresh_btn.config(state=tk.NORMAL)
                master.update()
                return

        if not os.path.isfile(archive_path):
            # abs_url should never be None if file already exists
            print("  - downloading: " + abs_url)
            mgr.download(archive_path, abs_url, cb_progress=d_progress,
                         cb_done=d_done)
    tar = None
    ext = None
    fmt = None
    fmt_bad = False
    if archive_path is not None:
        ext = bw.get_ext(archive_path)
        # if archive_path.lower()[-8:] == ".tar.bz2":
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
    if enable_install:
        if fmt is not None:
            # try:
            if fmt != "zip":
                tar = tarfile.open(archive_path, fmt)
            else:
                tar = zipfile.ZipFile(archive_path)
            '''
            except:
                fmt_bad = True
                msg = "ERROR: archive not " + fmt
                push_label(msg)
                print(msg)
            '''
    if fmt_bad:
        os.remove(archive_path)
        msg = "  - deleting downloaded '" + archive_path + "'..."
        print(msg)
        push_label("Deleted bad download.")
        push_label("Download again.")
    if remove_download:
        msg = "  - deleting downloaded '" + archive_path + "'..."
        print(msg)
        os.remove(archive_path)
    else:
        if archive_path is not None:
            msg = "  - leaving downloaded '" + archive_path + "'..."
            print(msg)

    if tar is None:
        if enable_install:
            for btn in dl_buttons:
                btn.config(state=tk.NORMAL)
            refresh_btn.config(state=tk.NORMAL)
            return
    else:
        print("  fmt: " + fmt)
    tmp_path = os.path.join(bn_path, "tmp")
    if enable_install:
        if not os.path.isdir(tmp_path):
            print("* created {}".format(tmp_path))
            os.makedirs(tmp_path)
    else:
        print("* tmp_path: {}".format(tmp_path))
    # for i in tar:
        # tar.extractfile(i)
    ok = False
    try:
        # if uninstall:
        #     msg = "examining archive..."
        if enable_install:
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
    finally:
        if tar is not None:
            tar.close()
            tar = None
    ext_path = tmp_path  # changes to sub if archive has only 1 dir
    if enable_install:
        msg = "checking tmp..."
        count_label.config(text=msg)
        master.update()
        # push_label(msg)
        print(msg)
        subdirs = bw.get_subdir_names(tmp_path)

        if len(subdirs) == 1:
            ext_path = os.path.join(tmp_path, subdirs[0])
            print("  Detected tar-like (single-folder) archive using '"
                  + ext_path + "' as program root")
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
        if tar is not None:
            tar.close()
            tar = None

    if enable_install:
        msg = "moving from tmp..."
        # if uninstall:
        #     msg = "examining extracted tmp..."
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
        if enable_install:
            if make_shortcut(meta, "blender", uninstall=uninstall):
                msg = ("  - {} the old desktop shortcut"
                       "".format(update_past_verb))
            else:
                msg = ("  - {} the old desktop shortcut failed."
                       "".format(update_present_verb))
            count_label.config(text=msg)
            master.update()
            remove_tmp = True
        else:
            make_shortcut(meta, "blender", uninstall=uninstall)
    if remove_tmp:
        if os.path.isdir(tmp_path):
            print("  - deleting temporary '" + tmp_path + "'...")
            shutil.rmtree(tmp_path)
    if ok:
        try:
            if enable_install:
                print("  - moving {} to {}".format(ext_path,
                                                   installed_path))
                shutil.move(ext_path, installed_path)
            else:
                if os.path.isdir(ext_path):
                    print("* WARNING: removing {}".format(ext_path))
                    shutil.rmtree(ext_path)
                if os.path.isdir(installed_path):
                    print("* uninstalling {}".format(ext_path))
                    shutil.rmtree(installed_path)
            count_label.config(text=action+" is complete.")
            print("* {} is complete".format(action))
            if enable_install:
                if btn is not None:
                    btn.pack_forget()
            else:
                if uninstall_btn is not None:
                    uninstall_btn.pack_forget()

            master.update()
            meta['installed_bin'] = bw.get_installed_bin(
                versions_path,
                meta['id'],
                bin_names
            )
            if enable_install:
                if make_shortcut(meta, "blender", uninstall=uninstall):
                    msg = ("{} the desktop shortcut"
                           "".format(update_past_verb))
                else:
                    msg = ("{} the desktop shortcut failed."
                           "".format(update_present_verb))
            else:
                make_shortcut(meta, "blender", uninstall=uninstall)
        except:
            msg = action + " could not finish moving"
            if uninstall:
                msg = action + " could not finish deleting"
            push_label(msg)
            count_label.config(text="Installation failed.")
            master.update()
            push_label("to " + meta['id'])
            print("  from (extracted) '" + ext_path + "'")
            print(msg)
            print("  to '" + installed_path + "'")
            view_traceback()
    else:
        if archive_path is not None:
            msg = "  Deleting downloaded '" + archive_path + "'..."
            print(msg)
            push_label("Deleted bad download.")
            push_label("Download again.")
            os.remove(archive_path)

    for btn in dl_buttons:
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
    global dl_buttons
    for label in msg_labels:
        label.pack_forget()
    for btn in dl_buttons:
        btn.pack_forget()
    dl_buttons = []
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
    inst_metas = []
    dl_but_not_inst_count = 0
    print("  existing_downloads: ")  # /2.??-<commit>
    added_ids = []
    for dl_name in bw.get_file_names(archives_path):
        archive_path = os.path.join(archives_path, dl_name)
        dest_id = mgr.parser.id_from_url(dl_name, remove_ext=True)
        meta = {}
        dl_metas.append(meta)
        added_ids.append(dest_id)
        installed_path = os.path.join(versions_path, dest_id)
        meta['downloaded'] = True
        # meta['url'] = None
        meta['filename'] = dl_name
        meta['id'] = dest_id
        meta['version'] = mgr.parser.blender_tag_from_url(dl_name)
        meta['commit'] = mgr.parser.blender_commit_from_url(dl_name)
        print("  - (archive) '" + installed_path + "'")
        bin_path = bw.get_installed_bin(versions_path, meta['id'],
                                        bin_names)
        if bin_path is not None:
            meta['installed_bin'] = bin_path
        else:
            dl_but_not_inst_count += 1
    if versions_path is None:
        raise RuntimeError("versions_path is None.")

    for installed_name in bw.get_subdir_names(versions_path):
        installed_path = os.path.join(versions_path, installed_name)
        dest_id = installed_name
        if dest_id in added_ids:
            continue
        meta = {}
        inst_metas.append(meta)
        # ^ formerly mgr.parser.id_from_name(installed_name)
        meta['downloaded'] = True
        meta['install_path'] = installed_path
        meta['id'] = dest_id
        name_parts = dest_id.split("-")
        meta['version'] = name_parts[0]
        meta['installed'] = True
        if len(name_parts) > 1:
            meta['commit'] = name_parts[1]
        else:
            print("INFO: There is no commit hash in the directory name"
                  " \"{}\"".format(dest_id))
        print("  - (installed) '" + installed_path + "'")
        bin_path = bw.get_installed_bin(versions_path, meta['id'],
                                        bin_names)
        if bin_path is not None:
            meta['installed_bin'] = bin_path

    status_s = v_msg + "count: " + str(len(a_urls))
    count_label.config(text=status_s)
    master.update()
    print("  matched " + str(len(a_urls)) + " " + a_msg + "url(s)")

    row = 1
    url_installed_count = 0
    for meta in metas + inst_metas:
        # see https://stackoverflow.com/questions/17677649/\
        # tkinter-assign-button-command-in-loop-with-lambda
        user_button = tk.Button(
            master,
            text = "Install " + meta['id'],
            command=lambda meta=meta: d_click(meta)
        )

        meta['button'] = user_button

        uninstall_caption = "Uninstall"
        if meta.get('installed') is True:
            uninstall_caption = "Remove old"
        else:
            dl_buttons.append(user_button)
            user_button.pack()  # grid(row = row, column = 0)
        uninstall_button = tk.Button(
            master,
            text = uninstall_caption + " " + meta['id'],
            command=lambda meta=meta: uninstall_click(meta)
        )
        meta['uninstall_button'] = uninstall_button
        bin_path = bw.get_installed_bin(versions_path, meta['id'],
                                        bin_names)
        if bin_path is not None:
            meta['installed_bin'] = bin_path
            user_button.config(state=tk.DISABLED)
            if os.path.isfile(bin_path):
                dl_buttons.append(uninstall_button)
                uninstall_button.pack()  # grid(row = row, column = 0)
            # else:
            #     uninstall_button.config(state=tk.DISABLED)
            url_installed_count += 1
        else:
            print("The bin path is unknown for {}".format(meta))
        row += 1
    if url_installed_count > 0:
        push_label("(already installed " + str(url_installed_count) +
                   " above)")
    else:
        print("no available downloads are installed into {} yet."
              "".format(versions_path))
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
            dl_buttons.append(user_button)
            user_button.pack()  # grid(row = row, column = 0)

            if meta['id'] in ( meta['id'] for meta in metas ):
                # already is a button
                continue
            # print("  # not installed: " + meta['filename'])
            remove_button = tk.Button(
                master,
                text = "Delete " + meta['id'],
                command=lambda meta=meta: remove_ar_click(meta)
            )
            meta['button'] = remove_button
            dl_buttons.append(remove_button)
            remove_button.pack()  # grid(row = row, column = 0)


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
    # if len(dl_buttons) > 2:
    master.update()
    # use max heights to resize window,
    # since widget height is 0 if crushed by window:
    btn_h_max = refresh_btn.winfo_height()
    label_h_max = count_label.winfo_height()
    for i in range(0, len(dl_buttons)):
        if dl_buttons[i].winfo_height() > btn_h_max:
            btn_h_max = dl_buttons[i].winfo_height()
        expand += btn_h_max
    for i in range(0, len(msg_labels)):
        if msg_labels[i].winfo_height() > label_h_max:
            label_h_max = msg_labels[i].winfo_height()
        expand += label_h_max
    if expand > 0:
        print("expand: " + str(expand))
        # master.config(height=master.winfo_width()+expand)
        root.geometry('400x' + str(old_bottom+expand))

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
