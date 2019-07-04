import socket
from socket import gethostbyname,gethostname
import threading
import time
import json
import wx
import os

port_detect=1060
port_transfer=1080
alive_hosts={}

name=gethostname()
host=gethostbyname(name)
'''
def detect_lan_hosts(s):
	while True:
		#s.sendto('alive'.encode('utf-8'),('<broadcast>',port_detect))
		data,address=s.recvfrom(65535)
		data=data.decode('utf-8')
		if data=='alive':
			if address[0]!=host:
				if address[0] not in alive_hosts:
					t=time.time()
					alive_hosts[address[0]]=t
				else:
					t=time.time()
					alive_hosts[address[0]]=t#更新生存时间
				print(address[0]+':'+data)


def judge_hosts_alive(s):
	while(True):
		s.sendto('alive'.encode('utf-8'),('<broadcast>',port_detect))
		t=time.time()
		for host in alive_hosts:
			if t-alive_hosts[host]>=3:#如果3秒还没收到alive消息则判定主机退出
				del alive_hosts[host]
		time.sleep(1)
'''

class mainFrame(wx.Frame):
	def __init__(self,title):
		wx.Frame.__init__(self,None,title=title)
		self.SetSize((500,200))
		self.Center()
		self.Show()

		self.ip_choice=wx.Choice(self,pos=(10,20),size=(130,30))
		self.filename_text=wx.TextCtrl(self,pos=(160,20),size=(200,25),style=wx.TE_READONLY)
		file_button=wx.Button(self,label='打开',pos=(370,20),size=(50,25))
		send_button=wx.Button(self,label='发送',pos=(425,20),size=(50,25))
		self.gauge=wx.Gauge(self,range=100,pos=(10,80),size=(465,30),style = wx.GA_HORIZONTAL)
		self.rate=wx.StaticText(self,pos=(220,120),label='',size=(50,30),style=wx.ALIGN_CENTER)
		file_button.Bind(wx.EVT_BUTTON,self.open_file)
		send_button.Bind(wx.EVT_BUTTON,self.send)

		s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
		s.bind(('',port_detect))

		thread_detect=threading.Thread(target=self.detect_lan_hosts,args=(s,))
		thread_detect.setDaemon(True)
		thread_detect.start()

		thread_judge=threading.Thread(target=self.judge_hosts_alive,args=(s,))
		thread_judge.setDaemon(True)
		thread_judge.start()

		thread_receive=threading.Thread(target=self.receive,args=())
		thread_receive.setDaemon(True)
		thread_receive.start()


	def send_file(self,confirm,file_full_name,filename,size,s):
		if confirm.decode('utf-8')=='ok':
			try:
				f=open(file_full_name,'rb')
				send_size=0
				all_time,all_count=0,0
				for line in f:
					time_start=time.time()
					s.send(line)
					time_end=time.time()
					time_gap=time_end-time_start
					all_count+=1
					all_time+=time_gap
					if all_time>=1:
						rate=all_count
						all_count,all_time=0,0
						self.rate.SetLabel(str(rate)+'KB/s')
					send_size+=len(line)
					self.gauge.SetValue(send_size/size*100)
			except:
				dlg=wx.MessageDialog(None,filename+'发送失败!')
				dlg.ShowModal()
				dlg.Destroy()
				self.gauge.SetValue(0)
				self.rate.SetLabel('')
				return

			dlg=wx.MessageDialog(None,filename+'发送成功!')
			dlg.ShowModal()
			dlg.Destroy()
			self.gauge.SetValue(0)
			self.rate.SetLabel('')
		s.close()


	def open_file(self,event):
		dlg = wx.FileDialog(self, "请选择文件",os.getcwd(), style = wx.FD_OPEN | wx.FD_CHANGE_DIR)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			self.filename_text.SetValue(filename)
		dlg.Destroy()


	def send(self,event):
		file_full_name=self.filename_text.GetValue()
		ip=self.ip_choice.GetStringSelection()
		if file_full_name=='':
			dlg=wx.MessageDialog(None,'请先选择文件!')
			dlg.ShowModal()
			dlg.Destroy()
			return
		if ip=='':
			dlg=wx.MessageDialog(None,'请先选择对方ip!')
			dlg.ShowModal()
			dlg.Destroy()
			return

		#s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s=socket.socket()
		try:
			s.connect((ip,port_transfer))
		except:
			dlg=wx.MessageDialog(None,'连接失败!')
			dlg.ShowModal()
			dlg.Destroy()
			return

		size=os.path.getsize(file_full_name)
		dir,filename=os.path.split(file_full_name)
		header={}
		header['filename']=filename
		header['size']=size
		header_json=json.dumps(header)
		confirm=None
		try:
			s.send(header_json.encode('utf-8'))
			confirm=s.recv(1024)
		except:
			dlg=wx.MessageDialog(None,'连接中断!')
			dlg.ShowModal()
			dlg.Destroy()
			return

		st=threading.Thread(target=self.send_file,args=(confirm,file_full_name,filename,size,s))
		st.setDaemon(True)
		st.start()
		'''
		if confirm.decode('utf-8')=='ok':
			try:
				f=open(file_full_name,'rb')
				send_size=0
				all_time,all_count=0,0
				for line in f:
					time_start=time.time()
					s.send(line)
					time_end=time.time()
					time_gap=time_end-time_start
					all_count+=1
					all_time+=time_gap
					if all_time>=1:
						rate=all_count
						all_count,all_time=0,0
						self.rate.SetLabel(str(rate)+'KB/s')
					send_size+=len(line)
					self.gauge.SetValue(send_size/size*100)
			except:
				dlg=wx.MessageDialog(None,filename+'发送失败!')
				dlg.ShowModal()
				dlg.Destroy()
				self.gauge.SetValue(0)
				return

			dlg=wx.MessageDialog(None,filename+'发送成功!')
			dlg.ShowModal()
			dlg.Destroy()
			self.gauge.SetValue(0)
		s.close()
'''

	def detect_lan_hosts(self,s):
		while True:
			data,address=s.recvfrom(1024)
			data=data.decode('utf-8')
			if data=='alive':
				if address[0]!=host:
					if address[0] not in list(alive_hosts.keys()):
						t=time.time()
						alive_hosts[address[0]]=t

						lis=[]
						for h in list(alive_hosts.keys()):
							lis.append(h)
						self.ip_choice.SetItems(lis)
					else:
						t=time.time()
						alive_hosts[address[0]]=t#更新生存时间
					print(address[0]+':'+data)



	def judge_hosts_alive(self,s):
		while(True):
			s.sendto('alive'.encode('utf-8'),('<broadcast>',port_detect))
			t=time.time()
			for host in list(alive_hosts.keys()):
				if t-alive_hosts[host]>=3:#如果3秒还没收到alive消息则判定主机退出
					del alive_hosts[host]
					lis=[]
					for h in list(alive_hosts.keys()):
						lis.append(h)
					self.ip_choice.SetItems(lis)
			time.sleep(1)


	def receive(self):
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((host,port_transfer))
		s.listen(1)
		while True:
			print('receive...')
			conn,addr=s.accept()
			data=conn.recv(1024).decode('utf-8')
			print(addr[0]+':'+data)#conn为新建立的socket!
			data=json.loads(data)
			filename=data['filename']
			size=data['size']

			dlg=wx.MessageDialog(None,'是否接受来自:'+addr[0]+'的文件:'+filename,style=wx.YES_NO | wx.ICON_QUESTION)
			if dlg.ShowModal()==wx.ID_YES:#确认接受文件
				dlg.Destroy()
				dlg = wx.DirDialog(self, "请选择文件保存路径",os.getcwd(), style = 0)
				#dlg = FileDialog(self,"请选择文件保存路径",os.getcwd(),style=wx.FD_OPEN)
				if dlg.ShowModal() == wx.ID_OK:
					conn.send('ok'.encode('utf-8'))
					path = dlg.GetPath()
					print(path)
					dlg.Destroy()

				try:
					f=open(path+'/'+filename,'wb')
					print('开始接收'+filename+'...')
					receive_size=0
					all_time,all_count=0,0
					while receive_size<size:
						time_start=time.clock()
						line=conn.recv(1024)
						time_end=time.clock()
						time_gap=time_end-time_start
						all_count+=1
						all_time+=time_gap
						if all_time>=1:
							rate=all_count
							all_count,all_time=0,0
							self.rate.SetLabel(str(rate)+'KB/s')

						f.write(line)
						receive_size+=len(line)
						self.gauge.SetValue(receive_size/size*100)
				except:
					dlg=wx.MessageDialog(None,filename+'接收失败!')
					dlg.ShowModal()
					dlg.Destroy()
					self.gauge.SetValue(0)
					self.rate.SetLabel('')
					continue

				print(filename+'接收完成!')
				dlg=wx.MessageDialog(None,filename+'接收完成!')
				dlg.ShowModal()
				dlg.Destroy()
				self.gauge.SetValue(0)
				self.rate.SetLabel('')
			else:
				s.close()
				dlg.Destroy()
		s.close() #与while对齐!




def main():
	app=wx.App()
	f=mainFrame('FileTransfer')
	app.MainLoop()

'''
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('localhost',port_transfer))
	s.listen(1)
	while True:
		conn,addr=s.accept()
		data=conn.recv(2048).decode('utf-8')
		print(addr[0]+':'+data)#conn为新建立的socket!
		data=json.loads(data)
		filename=data['filename']
		size=data['size']
		print('开始接收'+filename+'...')
		with open(filename,'wb') as f:
			receive_size=0
			while receive_size<size:
				line=conn.recv(1024)
				f.write(line)
				receive_size+=len(line)
		print(filename+'接收完成!')
	s.close()#与while对齐!

'''

if __name__ == '__main__':
	main()