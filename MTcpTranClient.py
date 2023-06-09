import socket
from MTcpTranPack import TcpTranPack
from MTcpTranUnPack import TcpTranUnPack

class TcpTranClient :
    def __init__(self,Timeout=2,OneSizePack=1024) :
        self.Error=[]
        self.Host="" # 要连接的主机
        self.Port="" # 要连接的主机的端口
        self.Timeout=Timeout
        self.OneSizePack=OneSizePack
        self.Soc=socket.socket()

        self.UPK=TcpTranUnPack()
    def __del__(self) :
        self.Soc.close()
    
    def __err__(self,stde,mye) :
        self.Error.append((stde,mye))
    
    def Connect(self,Host,Port) :
        try :
            self.Soc.settimeout(self.Timeout) #设置超时时间
            self.Soc.connect((Host,Port))
            self.Soc.settimeout(None) # 恢复为系统默认超时时间
            
            return True
        except Exception as e :
            self.__err__(e,"连接主机 "+str(self.Host)+" 失败")
            return False
    
    def Send(self,data:str,packname="Unknown",description="nothinghere") :
        #print(data)####
        try :
            PK=TcpTranPack(Destination=self.Host,PackName=packname,Description=description,Port=self.Port,OnePackSize=self.OneSizePack)
            JsPkLst=PK.Pack(data)
        except Exception as e :
            self.__err__(e,"将数据 "+data+" 打包失败")
            return False
        try :
            for pk in JsPkLst :
                self.Soc.send(pk.encode(encoding="utf-8"))
        except Exception as e :
            self.__err__(e,"send 数据 "+data+" 失败")
            return False
        return True
    def Recv(self) :
        try :
            while True :
                dt=self.Soc.recv(self.OneSizePack)
                dc=self.UPK.UnPack(dt)
                if dc!={} :
                    return dc
        except Exception as e :
            self.__err__(e,"阻塞接受数据失败")
            return {}
            
