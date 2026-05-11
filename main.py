import configparser
import os.path
import re
import threading
import time
import queue
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import urllib3
from bs4 import BeautifulSoup
import random


class Course:
    id = '0'
    class_id = '0'
    flag = True
    check_list = []
    class_list = []
    check_detect_time = {}
    monitor_thread = None
    stop_event = threading.Event()


monitor_delay_seconds = 0
monitor_sign_count_threshold = 1


def parse_non_negative_int(value, default):
    try:
        result = int(value)
        return result if result >= 0 else default
    except (ValueError, TypeError):
        return default


def append_log(message):
    if not message.endswith("\n"):
        message += "\n"
    text_box.insert(tk.END, message)
    text_box.see(tk.END)


def push_ui_log(message):
    ui_queue.put(("log", message))


def push_ui_status(message):
    ui_queue.put(("status", message))


def drain_ui_queue():
    try:
        while True:
            kind, payload = ui_queue.get_nowait()
            if kind == "log":
                append_log(payload)
            elif kind == "status":
                status_var.set(payload)
            elif kind == "warning":
                messagebox.showwarning("提示", payload)
    except queue.Empty:
        pass
    root.after(100, drain_ui_queue)


def on_combo_change(event):
    className = combo_var.get()
    for i in Course.class_list:
        if i["CourseName"] == className:
            Course.id = i["CourseID"]
            Course.class_id = i["TClassID"]


def save_cookie(_x):
    config['INFO'] = {
        'cookie': _x.request.headers.get("cookie")
    }
    with open(filename, 'w') as f:
        config.write(f)


def login_link():
    link = link_entry.get()
    code = re.search(r"(?<=code=)\S{32}", link)
    if code is not None:
        x.cookies.clear()
        code = code[0]
        _r = x.get(url=host + f"/P.aspx?authtype=1&code={code}&state=1", timeout=5)
        get_class_list()
        save_cookie(_r)
    else:
        messagebox.showerror("error", "链接有误")


def login():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.duifene.com/AppGate.aspx"
    }
    params = f'action=loginmb&loginname={username.get()}&password={password.get()}'
    x.cookies.clear()
    x.get(host, timeout=5)
    _r = x.post(url=host + "/AppCode/LoginInfo.ashx", data=params, headers=headers, timeout=5)
    if _r.status_code == 200:
        text_box.delete("1.0", "end")
        msg = _r.json()["msgbox"]
        text_box.insert(tk.END, f"\n{msg}\n")
        if msg == "登录成功":
            get_class_list()
            save_cookie(_r)
    else:
        messagebox.showerror("错误提示", "登录失败")


def select_tab(event=None):
    tab_id = tab_control.index(tab_control.select())
    text_box.delete("1.0", "end")
    if tab_id == 0:
        text = '''
        1、打开电脑端微信，复制如下链接到文件传输助手并发送\n
        【https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx1b5650884f657981&redirect_uri=https://www.duifene.com/_FileManage/PdfView.aspx?file=https%3A%2F%2Ffs.duifene.com%2Fres%2Fr2%2Fu6106199%2F%E5%AF%B9%E5%88%86%E6%98%93%E7%99%BB%E5%BD%95_876c9d439ca68ead389c.pdf&response_type=code&scope=snsapi_userinfo&connect_redirect=1#wechat_redirect】\n\n
        2、点击进入链接，点击微信浏览器窗口右上角三个点，点击复制链接，并把微信链接粘贴到左侧输入框。\n
        '''
        text_box.insert(tk.END, text)
        root.after(10, link_entry.focus_set)
    elif tab_id == 1:
        text_box.insert(tk.END, "账号密码登录模式不支持二维码签到。\n")
        root.after(10, username.focus_set)


def get_user_id():
    _r = x.get(url=host + "/_UserCenter/MB/index.aspx", timeout=5)
    if _r.status_code == 200:
        soup = BeautifulSoup(_r.text, "lxml")
        stu_id = soup.find(id="hidUID").get("value")
        return stu_id


def sign(sign_code):
    # 签到码
    if len(sign_code) == 4:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://www.duifene.com/_CheckIn/MB/CheckInStudent.aspx?moduleid=16&pasd="
        }
        params = f"action=studentcheckin&studentid={get_user_id()}&checkincode={sign_code}"
        _r = x.post(
            url=host + "/_CheckIn/CheckIn.ashx", data=params, headers=headers, timeout=5)
        if _r.status_code == 200:
            msg = _r.json()["msgbox"]
            if msg == "签到成功！":
                return True, msg
            return False, msg
    # 二维码
    else:
        _r = x.get(url=host + "/_CheckIn/MB/QrCodeCheckOK.aspx?state=" + sign_code, timeout=5)
        if _r.status_code == 200:
            soup = BeautifulSoup(_r.text, "lxml")
            msg = soup.find(id="DivOK").get_text()
            if "签到成功" in msg:
                return True, msg
            return False, "非微信链接登录，二维码无法签到"
    return False, "签到请求失败"


def sign_location(longitude, latitude):
    longitude = str(round(float(longitude) + random.uniform(-0.000089, 0.000089), 8))
    latitude = str(round(float(latitude) + random.uniform(-0.000089, 0.000089), 8))

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.duifene.com/_CheckIn/MB/CheckInStudent.aspx?moduleid=16&pasd="
    }
    params = f"action=signin&sid={get_user_id()}&longitude={longitude}&latitude={latitude}"
    _r = x.post(
        url=host + "/_CheckIn/CheckInRoomHandler.ashx", data=params, headers=headers, timeout=5)
    if _r.status_code == 200:
        msg = _r.json()["msgbox"]
        if msg == "签到成功！":
            return True, msg
        return False, msg
    return False, "定位签到请求失败"


def get_checkin_count(check_in_id):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.duifene.com/_CheckIn/MB/TeachCheckIn.aspx"
    }
    params = {
        "action": "getcheckintotalbyciid",
        "ciid": check_in_id,
        "t": "cking"
    }
    _r = x.post(url=host + "/_CheckIn/MBCount.ashx", data=params, headers=headers, timeout=5)
    if _r.status_code != 200:
        return None, None
    try:
        datajson = _r.json()
        total_count = int(datajson.get("TotalNumber", 0))
        absence_count = int(datajson.get("AbsenceNumber", total_count))
        signed_count = max(total_count - absence_count, 0)
        return signed_count, total_count
    except (TypeError, ValueError, AttributeError):
        return None, None


def watching_sign_worker():
    while not Course.stop_event.is_set() and Course.flag:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        delay_seconds = monitor_delay_seconds
        sign_count_threshold = monitor_sign_count_threshold
        push_ui_status(f"持续监控中：{current_time}")

        try:
            _r = x.get(url=host + f"/_CheckIn/MB/TeachCheckIn.aspx?classid={Course.class_id}&temps=0&checktype=1&isrefresh=0"
                                  f"&timeinterval=0&roomid=0&match=", timeout=5)
            if _r.status_code == 200 and "HFChecktype" in _r.text:
                status = False
                result_msg = ""
                soup = BeautifulSoup(_r.text, "lxml")

                HFSeconds = soup.find(id="HFSeconds").get("value")
                HFChecktype = soup.find(id="HFChecktype").get("value")
                HFCheckInID = soup.find(id="HFCheckInID").get("value")
                HFClassID = soup.find(id="HFClassID").get("value")
                if Course.class_id in HFClassID:
                    if HFCheckInID not in Course.check_list:
                        if HFCheckInID not in Course.check_detect_time:
                            Course.check_detect_time[HFCheckInID] = now
                        elapsed_seconds = int((now - Course.check_detect_time[HFCheckInID]).total_seconds())
                        signed_count, total_count = get_checkin_count(HFCheckInID)
                        # 阈值为0表示关闭人数限制，只按时间阈值判断。
                        count_ok = sign_count_threshold <= 0 or (
                            signed_count is not None and signed_count >= sign_count_threshold
                        )
                        can_sign_now = elapsed_seconds >= delay_seconds and count_ok
                        # 数字签到
                        if HFChecktype == '1':
                            sign_code = soup.find(id="HFCheckCodeKey").get("value")
                            if sign_code is not None and can_sign_now:
                                push_ui_log(f"\n\n{current_time} 签到ID：{HFCheckInID} 开始签到\t签到码：{sign_code}")
                                status, result_msg = sign(sign_code)
                            else:
                                signed_text = "--" if signed_count is None else str(signed_count)
                                total_text = "--" if total_count is None else str(total_count)
                                push_ui_log(
                                    f"\t签到码签到\t未到签到时间\t倒计时：{HFSeconds}秒\t已开始：{elapsed_seconds}秒"
                                    f"\t目标延迟：{delay_seconds}秒\t已签到人数：{signed_text}/{total_text}"
                                    f"\t人数阈值：{sign_count_threshold}\t签到码：{sign_code}")
                        # 二维码签到
                        elif HFChecktype == '2':
                            if HFCheckInID is not None and can_sign_now:
                                push_ui_log(f"\n\n{current_time} 签到ID：{HFCheckInID} 开始签到\t二维码签到")
                                status, result_msg = sign(HFCheckInID)
                            else:
                                signed_text = "--" if signed_count is None else str(signed_count)
                                total_text = "--" if total_count is None else str(total_count)
                                push_ui_log(
                                    f"\t二维码签到\t未到签到时间\t倒计时：{HFSeconds}秒\t已开始：{elapsed_seconds}秒"
                                    f"\t目标延迟：{delay_seconds}秒\t已签到人数：{signed_text}/{total_text}"
                                    f"\t人数阈值：{sign_count_threshold}")
                        # 定位签到
                        elif HFChecktype == '3':
                            HFRoomLongitude = soup.find(id="HFRoomLongitude").get("value")
                            HFRoomLatitude = soup.find(id="HFRoomLatitude").get("value")
                            if HFRoomLongitude is not None and HFRoomLatitude is not None and can_sign_now:
                                push_ui_log(f"\n\n{current_time} 签到ID：{HFCheckInID} 开始签到\t定位签到")
                                status, result_msg = sign_location(HFRoomLongitude, HFRoomLatitude)
                            else:
                                signed_text = "--" if signed_count is None else str(signed_count)
                                total_text = "--" if total_count is None else str(total_count)
                                push_ui_log(
                                    f"\t定位签到\t未到签到时间\t倒计时：{HFSeconds}秒\t已开始：{elapsed_seconds}秒"
                                    f"\t目标延迟：{delay_seconds}秒\t已签到人数：{signed_text}/{total_text}"
                                    f"\t人数阈值：{sign_count_threshold}")

                        if result_msg:
                            push_ui_log(f"\t{result_msg}\n")
                        if status:
                            Course.check_list.append(HFCheckInID)
                            Course.check_detect_time.pop(HFCheckInID, None)
                else:
                    push_ui_log("\t检测到非本班签到")
        except (requests.ConnectionError, requests.Timeout):
            push_ui_status(f"网络波动：{current_time}")

        time.sleep(1)


def start_watching_sign():
    if Course.monitor_thread and Course.monitor_thread.is_alive():
        return
    Course.stop_event.clear()
    Course.flag = True
    Course.monitor_thread = threading.Thread(target=watching_sign_worker, daemon=True)
    Course.monitor_thread.start()


def go_sign():
    global monitor_delay_seconds, monitor_sign_count_threshold
    monitor_delay_seconds = parse_non_negative_int(delay_entry.get(), 0)
    monitor_sign_count_threshold = parse_non_negative_int(sign_count_entry.get(), 1)
    if combo.get() is None or combo.get() == '':
        messagebox.showerror("错误提示", "请先登录")
        return
    headers = {
        "Referer": "https://www.duifene.com/_UserCenter/MB/index.aspx"
    }
    _r = x.get(url=host + "/_UserCenter/MB/Module.aspx?data=" + Course.id, headers=headers, timeout=5)
    if _r.status_code == 200:
        if Course.id in _r.text:
            text_box.delete("1.0", "end")
            soup = BeautifulSoup(_r.text, "lxml")
            CourseName = soup.find(id="CourseName").text
            append_log(f"正在监听【{CourseName}】的签到活动\n\n")
            start_watching_sign()


def get_class_list():
    # 获取用户课程列表
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.duifene.com/_UserCenter/PC/CenterStudent.aspx"
    }
    params = "action=getstudentcourse&classtypeid=2"
    _r = x.post(url=host + "/_UserCenter/CourseInfo.ashx", data=params, headers=headers, timeout=5)
    if _r.status_code == 200:
        _json = _r.json()
        if _json is not None:
            try:
                msg = _json["msgbox"]
                messagebox.showerror("", f"{msg} 请重新登录。")
                x.cookies.clear()
            except Exception as e:
                messagebox.showinfo("提示", "登录成功")
                class_name_list = []
                for i in _json:
                    class_name_list.append(i["CourseName"])
                combo['values'] = tuple(class_name_list)
                combo.set(class_name_list[0])
                Course.id = _json[0]['CourseID']
                Course.class_id = _json[0]["TClassID"]
                Course.class_list = _json


def is_login():
    headers = {
        "Referer": "https://www.duifene.com/_UserCenter/PC/CenterStudent.aspx",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    _r = x.get(host + "/AppCode/LoginInfo.ashx", data="Action=checklogin", headers=headers, timeout=5)
    if _r.status_code == 200:
        if _r.json()["msg"] == "1":
            return True
        else:
            messagebox.showwarning("登录状态失效", "请重新登录账号")
            x.cookies.clear()
            Course.flag = False
            Course.stop_event.set()
            return False


def init():
    try:
        if not os.path.exists(filename):
            config['INFO'] = {
                'cookie': '1=1'
            }
            with open(filename, 'w') as configfile:
                config.write(configfile)
            x.get(host, timeout=5)
        else:
            try:
                config.read(filename)
                cookie = config.get('INFO', 'cookie')
                cookies = {}
                for pair in cookie.split('; '):
                    key, value = pair.split('=')
                    cookies[key] = value
                x.cookies.update(cookies)
                get_class_list()
            except Exception as e:
                pass
    except (requests.ConnectionError, requests.Timeout):
        # 如果请求失败，则没有互联网连接
        messagebox.showwarning("网络状态", "未检测到互联网连接，请检查你的网络设置。")
        root.destroy()


if __name__ == '__main__':
    host = "https://www.duifene.com"
    UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) '
         'Mobile/15E148 MicroMessenger/8.0.40(0x1800282a) NetType/WIFI Language/zh_CN '
    urllib3.disable_warnings()
    x = requests.Session()
    x.headers['User-Agent'] = UA
    # x.proxies = {"https": "127.0.0.1:8888"}
    x.verify = False
    filename = 'duifenyi.ini'
    config = configparser.ConfigParser()

    # 创建UI
    root = tk.Tk()
    # 标题
    root.title("2026.4.20")
    # 禁用窗口的调整大小
    root.resizable(False, False)

    # tab控制
    tab_control = ttk.Notebook(root)
    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)
    # 添加选项卡
    tab_control.add(tab1, text="微信链接登录")
    tab_control.add(tab2, text="账号密码登录")
    # 当选项卡被选中时，调用select_tab函数
    tab_control.bind("<<NotebookTabChanged>>", select_tab)
    tab_control.pack(fill=tk.BOTH, side=tk.LEFT)

    # tab选项卡中的内容_链接登录
    tab_frame1 = tk.Frame(tab1)
    tab_frame1.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
    tk.Label(tab_frame1, text="支持二维码和签到码\n查看右侧说明进行登录", font=('宋体', 10)).pack(pady=5)
    tk.Label(tab_frame1, text="登录链接", font=('宋体', 10)).pack(pady=5)
    link_entry = tk.Entry(tab_frame1, font=('宋体', 12))
    link_entry.pack(pady=5, padx=10)
    tk.Button(tab_frame1, text="登录", command=login_link, font=('宋体', 14)).pack(pady=5)

    # tab选项卡中的内容_密码登录
    tab_frame2 = tk.Frame(tab2)
    tab_frame2.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
    tk.Label(tab_frame2, text="不支持二维码签到", font=('宋体', 10)).pack(padx=5)
    tk.Label(tab_frame2, text="账号", font=('宋体', 14)).pack(padx=10)
    username = tk.Entry(tab_frame2, font=('宋体', 12))
    username.pack(padx=10)
    tk.Label(tab_frame2, text="密码", font=('宋体', 14)).pack(padx=10)
    password = tk.Entry(tab_frame2, show="*", font=('宋体', 12))
    password.pack(padx=10)
    tk.Button(tab_frame2, text="登录", command=login, font=('宋体', 14)).pack(pady=5)

    # 右边frame_选择课程
    frame_mid = tk.Frame(root)
    frame_mid.pack(side=tk.TOP)
    status_var = tk.StringVar(value="未开始监听")
    ui_queue = queue.Queue()
    tk.Label(frame_mid, textvariable=status_var, font=('宋体', 9), fg='gray').pack(side=tk.TOP, fill=tk.BOTH, pady=(2, 2))
    tk.Label(frame_mid, text="选择课程").pack(side=tk.TOP, fill=tk.BOTH, pady=(10, 0))
    combo_var = tk.StringVar()
    combo = ttk.Combobox(frame_mid, textvariable=combo_var, state="readonly")
    combo.bind("<<ComboboxSelected>>", on_combo_change)
    combo.pack(side=tk.LEFT, padx=(0, 6))
    tk.Label(frame_mid, text="开始后延迟X秒").pack(side=tk.LEFT, padx=(2, 0))
    delay_entry = tk.Spinbox(frame_mid, from_=0, to=9999, width=5, font=('宋体', 10))
    delay_entry.delete(0, tk.END)
    delay_entry.insert(0, "0")
    delay_entry.pack(side=tk.LEFT, padx=(2, 0))

    def update_delay_seconds(_event=None):
        global monitor_delay_seconds
        monitor_delay_seconds = parse_non_negative_int(delay_entry.get(), 0)

    delay_entry.configure(command=update_delay_seconds)
    delay_entry.bind("<KeyRelease>", update_delay_seconds)
    delay_entry.bind("<FocusOut>", update_delay_seconds)
    update_delay_seconds()

    tk.Label(frame_mid, text="人数阈值>=X").pack(side=tk.LEFT, padx=(8, 0))
    sign_count_entry = tk.Spinbox(frame_mid, from_=0, to=9999, width=5, font=('宋体', 10))
    sign_count_entry.delete(0, tk.END)
    sign_count_entry.insert(0, "1")
    sign_count_entry.pack(side=tk.LEFT, padx=(2, 0))

    def update_sign_count_threshold(_event=None):
        global monitor_sign_count_threshold
        monitor_sign_count_threshold = parse_non_negative_int(sign_count_entry.get(), 1)

    sign_count_entry.configure(command=update_sign_count_threshold)
    sign_count_entry.bind("<KeyRelease>", update_sign_count_threshold)
    sign_count_entry.bind("<FocusOut>", update_sign_count_threshold)
    update_sign_count_threshold()

    btn = tk.Button(frame_mid, text="开始监听签到", command=go_sign)
    btn.pack(side=tk.RIGHT, padx=10, pady=10)

    # 输出框
    frame_right = tk.Frame(root)
    frame_right.pack(side=tk.RIGHT)
    text_box = tk.Text(frame_right, width=90, height=20, font=('宋体', 9))
    text_box.pack(pady=(0, 10), padx=(0, 10))

    # 初始化tab说明与输入焦点
    select_tab()
    drain_ui_queue()

    # 初始化
    init()
    root.mainloop()
