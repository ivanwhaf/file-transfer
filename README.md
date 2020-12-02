# FileTransfer
* 局域网文件传输（融合UDP广播和TCP）
* UDP广播用于探测在线主机和发送在线广播，TCP用于文件传输

# Usage
## Windows
1. 双击**transfer.exe**运行
2. 点击下拉框选择要传输文件的对方ip
3. 点击**打开**按钮，选择要发送的文件
4. 点击**发送**按钮发送文件

## Linux
* `$ python transfer.py`

# Requirements
* `$ pip install wxpython`