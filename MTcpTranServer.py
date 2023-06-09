import socket
from MTcpTranPack import TcpTranPack
from MTcpTranUnPack import TcpTranUnPack

# 服务端套节字
class TcpTranServer :
    def __err__(self,stde,mye) :
        self.Error.append((stde,mye))

    def __init__(self,Host="",Port=29191,OneSizePack=1024) :
        self.Error=[]
        self.Host=Host
        self.Port=Port
        self.OneSizePack=OneSizePack
        self.LisSoc=socket.socket() # 监听套接字
        self.UPK=TcpTranUnPack()
    def __del__(self) :
        try :
            self.LisSoc.close()
        except Exception as e :
            self.__err__(e,"关闭套接字错误")
    
    def Bind(self) :
        try :
            self.LisSoc.bind((self.Host,self.Port))
        except :
            # 使用用户指定的端口绑定套接字失败,让系统自己分配端口绑定套接字
            try :
                self.LisSoc.bind((self.Host,0))
                return self.LisSoc.getsockname()[1] # 返回新绑定的端口
            except Exception as e :
                # 仍然绑定失败
                self.__err__(e,"为套接字绑定端口失败")
                return -1
        else : # 否则绑定默认端口成功
            return self.Port
    def Listen(self,Listeners=512) :
        try :
            # 设置套接字为监听套接字
            self.LisSoc.listen(Listeners)
            return True
        except Exception as e:
            self.__err__(e,"设置套接字为监听套接字失败")
            return False
    def Accept(self) :
        try :
            return self.LisSoc.accept()
        except Exception as e :
            self.__err__(e,"套接字阻塞时失败")
            return None,None
    
    def SetTimeOut(self,Timeout=2) :
        try :
            self.LisSoc.settimeout(Timeout)
            return True
        except Exception as e :
            self.__err__(e,"设置套接字超时时间失败")
            return False

    def Send(self,dsoc:socket,data:str,destionation="Unknown",packname="Unknown",description="nothinghere") :
        #print("Send"+data)####
        try :
            PK=TcpTranPack(Destination=destionation,PackName=packname,Description=description,Port=self.Port,OnePackSize=self.OneSizePack)
            JsPkLst=PK.Pack(data)
        except Exception as e :
            self.__err__(e,"将数据 "+data+" 打包失败")
            return False
        try :
            for pk in JsPkLst :
                dsoc.send(pk.encode(encoding="utf-8"))
        except Exception as e :
            self.__err__(e,"send 数据 "+data+" 失败")
            return False
        return True
    def Recv(self,soc) :
        try :
            while True :
                dt=soc.recv(self.OneSizePack)
                dc=self.UPK.UnPack(dt)
                if dc!={} :
                    #print(dc)####
                    return dc
        except Exception as e :
            self.__err__(e,"阻塞接受数据失败")
            return {}

