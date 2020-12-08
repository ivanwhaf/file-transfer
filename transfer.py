import os
import time
import json
import socket
import threading
import wx

PORT_BROADCAST = 1060  # 广播端口 用于探测同一局域网内用户
PORT_TRANSFER = 1080  # 文件传输端口
ALIVE_HOSTS = {}  # 存活主机信息


def get_host_ip():
    local_ip, s = None, None
    try:
        if not local_ip:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        return local_ip
    finally:
        if s:
            s.close()
        return local_ip


host_name = socket.gethostname()  # 主机名
print('host name:', host_name)
# host_ip = socket.gethostbyname(host_name)  # 主机ip
host_ip = get_host_ip()  # 主机ip
print('host ip:', host_ip)


class mainFrame(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title)
        self.SetSize((500, 220))
        self.Center()
        self.Show()
        self.ip_choice = wx.Choice(self, pos=(
            10, 20), size=(130, 30))  # ip选择下拉框
        self.file_path_text = wx.TextCtrl(self, pos=(
            160, 20), size=(200, 25), style=wx.TE_READONLY)  # 文件名文本框
        self.file_button = wx.Button(self, label='打开', pos=(
            370, 20), size=(50, 25))  # 打开文件按钮
        self.send_button = wx.Button(self, label='发送', pos=(
            425, 20), size=(50, 25))  # 发送按钮
        self.gauge = wx.Gauge(self, range=100, pos=(
            10, 80), size=(465, 30), style=wx.GA_HORIZONTAL)  # 进度条
        self.rate = wx.StaticText(self, pos=(
            220, 110), label='', size=(50, 30), style=wx.ALIGN_CENTER)  # 发送进度文本

        self.file_button.Bind(wx.EVT_BUTTON, self.open_file)
        self.send_button.Bind(wx.EVT_BUTTON, self.send)

        self.status_bar = wx.StatusBar(self, -1)
        self.SetStatusBar(self.status_bar)
        self.status_bar.SetStatusText('Host ip:'+host_ip)

        self.is_transfering = False
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_sock.bind((host_ip, PORT_BROADCAST))  # 套接字绑定广播端口

        thread_detect = threading.Thread(
            target=self.detect_lan_hosts, args=(udp_sock,))
        thread_detect.setDaemon(True)
        thread_detect.start()  # 探测局域网内主机线程

        thread_judge = threading.Thread(
            target=self.judge_hosts_alive, args=(udp_sock,))
        thread_judge.setDaemon(True)
        thread_judge.start()  # 判断主机是否存活线程

        thread_receive = threading.Thread(target=self.receive, args=())
        thread_receive.setDaemon(True)
        thread_receive.start()  # 接收线程

    def open_file(self, event):
        # 打开文件函数，单机打开文件按钮触发
        dlg = wx.FileDialog(self, "请选择文件!", os.getcwd(),
                            style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
            self.file_path_text.SetValue(file_path)  # 文本框设置文件路径值
        dlg.Destroy()

    def send_file(self, file_path, filename, size, s):
        # 发送文件
        try:
            f = open(file_path, 'rb')
            send_size = 0
            accum_time, accum_count = 0, 0
            for line in f:
                time_start = time.time()
                s.send(line)
                accum_time += time.time()-time_start
                accum_count += 1
                if accum_time >= 0.5:  # 每隔0.5秒计算一次速率
                    rate = accum_count
                    accum_count, accum_time = 0, 0
                    self.rate.SetLabel(str(round(rate/2, 3))+'KB/s')
                send_size += len(line)
                self.gauge.SetValue(send_size/size*100)
        except:
            dlg = wx.MessageDialog(None, filename+'发送失败!')
            dlg.ShowModal()
            dlg.Destroy()
            self.gauge.SetValue(0)
            self.rate.SetLabel('')
            s.close()
            self.is_transfering = False
            return

        dlg = wx.MessageDialog(None, filename+'发送成功!')
        dlg.ShowModal()
        dlg.Destroy()
        self.gauge.SetValue(0)
        self.rate.SetLabel('')
        s.close()
        self.status_bar.SetStatusText('文件发送完毕...')
        self.is_transfering = False

    def send(self, event):
        # 点击发送按钮触发
        if self.is_transfering == True:
            dlg = wx.MessageDialog(None, '请不要重复执行!')
            dlg.ShowModal()
            dlg.Destroy()
            return

        file_path = self.file_path_text.GetValue()
        ip = self.ip_choice.GetStringSelection()
        if file_path == '':
            dlg = wx.MessageDialog(None, '请先选择文件!')
            dlg.ShowModal()
            dlg.Destroy()
            return
        if ip == '':
            dlg = wx.MessageDialog(None, '请先选择对方ip!')
            dlg.ShowModal()
            dlg.Destroy()
            return

        # s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = socket.socket()
        try:
            s.connect((ip, PORT_TRANSFER))
        except:
            dlg = wx.MessageDialog(None, '连接失败!')
            dlg.ShowModal()
            dlg.Destroy()
            s.close()
            return

        self.is_transfering = True

        size = os.path.getsize(file_path)  # 文件大小
        dir_, filename = os.path.split(file_path)
        header = {'filename': filename, 'size': size}
        header_json = json.dumps(header)  # 文件头信息打包成json字符串
        try:
            s.send(header_json.encode('utf-8'))  # 发送文件头
            self.status_bar.SetStatusText('等待对方同意...')
            confirm = s.recv(4)  # 接收确认信息 ok/no/busy
        except:
            dlg = wx.MessageDialog(None, '连接中断!')
            dlg.ShowModal()
            dlg.Destroy()
            s.close()
            self.is_transfering = False
            return

        if confirm.decode('utf-8') == 'ok':
            self.status_bar.SetStatusText('开始发送文件...')
            send_thread = threading.Thread(
                target=self.send_file, args=(file_path, filename, size, s))
            send_thread.setDaemon(True)
            send_thread.start()
        elif confirm.decode('utf-8') == 'no':
            self.status_bar.SetStatusText('对方拒绝接收文件...')
            dlg = wx.MessageDialog(None, '对方拒绝接收文件,发送失败!')
            dlg.ShowModal()
            dlg.Destroy()
            s.close()
            self.is_transfering = False
        elif confirm.decode('utf-8') == 'busy':
            self.status_bar.SetStatusText('对方正忙...')
            dlg = wx.MessageDialog(None, '对方正忙,发送失败!')
            dlg.ShowModal()
            dlg.Destroy()
            s.close()
            self.is_transfering = False

    def receive(self):
        # 接收文件
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp socket
        s.bind((host_ip, PORT_TRANSFER))
        s.listen(1)
        while True:
            conn, addr = s.accept()  # conn为新建立的socket!
            header = conn.recv(1024).decode('utf-8') #文件头
            if self.is_transfering:  # 正在传送文件，拒接收文件
                conn.send('busy'.encode('utf-8'))
                continue

            print(addr[0]+':'+header)
            header = json.loads(header)
            filename = header['filename']
            size = header['size']

            dlg = wx.MessageDialog(
                None, '是否接受来自'+addr[0]+'的文件:'+filename+'?', style=wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:  # 确认接收文件
                dlg.Destroy()
                dlg2 = wx.DirDialog(self, "请选择文件保存路径!", os.getcwd(), style=0)
                # dlg2 = FileDialog(self,"请选择文件保存路径",os.getcwd(),style=wx.FD_OPEN)
                if dlg2.ShowModal() == wx.ID_OK:
                    conn.send('ok'.encode('utf-8'))
                    path = dlg2.GetPath()
                    print(path)
                    dlg2.Destroy()
                else:
                    conn.send('no'.encode('utf-8'))
                    dlg.Destroy()
                    continue

                try:
                    f = open(path+'/'+filename, 'wb')
                    self.status_bar.SetStatusText('开始接收文件...')
                    print('开始接收:'+filename+'...')
                    receie_size = 0
                    accum_time, accum_count = 0, 0
                    while receive_size < size:
                        time_start = time.time()
                        line = conn.recv(1024)
                        accum_time += time.time()-time_start
                        accum_count += 1
                        if accum_time >= 0.5:
                            rate = accum_count
                            accum_count, accum_time = 0, 0
                            self.rate.SetLabel(str(round(rate/2, 3))+'KB/s')

                        f.write(line)
                        receive_size += len(line)
                        self.gauge.SetValue(receive_size/size*100)
                    f.close()
                except:
                    dlg = wx.MessageDialog(None, filename+'接收失败!')
                    dlg.ShowModal()
                    dlg.Destroy()
                    f.close()
                    self.gauge.SetValue(0)
                    self.rate.SetLabel('')
                    continue

                print(filename+'接收完成!')
                dlg = wx.MessageDialog(None, filename+'接收完成!')
                dlg.ShowModal()
                dlg.Destroy()
                self.status_bar.SetStatusText('文件接收完毕...')
                self.gauge.SetValue(0)
                self.rate.SetLabel('')
            else:
                conn.send('no'.encode('utf-8'))
                dlg.Destroy()
        s.close()  # 与while对齐!

    def detect_lan_hosts(self, s):
        # 探测局域网内存活主机
        while True:
            data, address = s.recvfrom(5)  # alive单词长度为5 buffer最小设为5
            data = data.decode('utf-8')
            if data == 'alive':
                if address[0] != host_ip:  # 非本机ip广播
                    t = time.time()
                    if address[0] not in list(ALIVE_HOSTS.keys()):
                        ALIVE_HOSTS[address[0]] = t
                        alive_hosts_lst = [host for host in ALIVE_HOSTS.keys()]
                        self.ip_choice.SetItems(alive_hosts_lst)  # 更新存活主机列表
                    ALIVE_HOSTS[address[0]] = t  # 更新生存时间
                print(address[0]+':'+data)
            time.sleep(1)

    def judge_hosts_alive(self, s):
        # 更新局域网内存活主机信息并广播本机存活信息
        while(True):
            s.sendto('alive'.encode('utf-8'),
                     ('<broadcast>', PORT_BROADCAST))  # 发送本机存活信息
            t = time.time()
            for host in list(ALIVE_HOSTS.keys()):
                if t-ALIVE_HOSTS[host] >= 2:  # 如果3秒还没收到alive消息则判定主机退出
                    del ALIVE_HOSTS[host]
                    alive_hosts_lst = [host for host in ALIVE_HOSTS.keys()]
                    self.ip_choice.SetItems(alive_hosts_lst)  # 更新存活主机列表
            time.sleep(1)


def main():
    app = wx.App()
    frame = mainFrame('FileTransfer')
    app.MainLoop()


if __name__ == '__main__':
    main()
