import json
import socket
import uuid
import random
import string


class TcpTranPack :
    def __init__(self,
                 Destination="Unknown",PackName="Unknown",Description="Unknown",Port=-1,
                 OnePackSize=1024,BeginCode="This is a Begin.",EndCode="This is the End.",LenOfCode=32) :
        '''
        构造函数
        - 获取本机基本信息
        - 自定义通讯端口
        - 自定义一个包的大小
        - 自定义起始编码和结束编码
        '''

        self.Error=[] # 错误列表,每个元素是二元组(标准错误码,自定义描述)

        # 获取本机基本信息
        try :
            self.HostName=socket.gethostname() # 本地主机名
            self.HostIp=socket.gethostbyname(self.HostName) # 本地主机Ip
            self.HostMac=(':'.join(hex(uuid.getnode())[2:].zfill(12)[i:i+2] for i in range(0,12,2))) # 本地主机Mac(用于唯一标识一台主机)
        except Exception as e :
            self.Error.append((e,"获取本机基本信息失败"))
            self.HostIp="Unknown"
            self.HostMac="Unknown"
            self.HostName="Unknown"

        self.Port=Port # 通讯使用的端口
        self.Destination=Destination # 目标
        self.PackName=PackName # 包名
        self.Description=Description # 包的描述

        self.OnePackSize=OnePackSize # 一个包的大小
        self.BeginCode=BeginCode # 起始编码
        self.EndCode=EndCode # 结束编码
        self.LenOfCode=LenOfCode # 编码长度
        
        self.PackList=[]
    
    def __err__(self,stde,mye) :
        '''
        添加错误
        '''
        self.Error.append((stde,mye))
    def Geterr(self) :
        '''
        输出错误列表
        '''
        print(self.Error)
    
    def __randomstr__(self,n):
        '''
        返回一个随机生成的长度为 n 的字符串
        '''
        s=string.ascii_letters+string.ascii_uppercase+string.digits
        return ''.join(random.sample(s,n))
    
    def Pack(self,Data:str) :
        '''
        对 Data 打包,返回打包后的 json 风格字符串的列表
        '''

        try :
            
            self.PackList.append({"NxtCode":self.__randomstr__(self.LenOfCode)})
            # 每个包的 NxtCode 是随机生成的字符串
            
            # 构造正文包
            L,R=0,0 # 双指针
            while True :
                
                NewPack={}
                NewPack["PreCode"]=self.PackList[-1]["NxtCode"]
                NewPack["NxtCode"]=self.__randomstr__(self.LenOfCode)
                NewPack["Data"]=""
                
                RstSz=self.OnePackSize-len(json.dumps(NewPack)) # 这个包还剩下多少空间可以放
                FilSz=0 # 已经往这个包中填充了多少数据
                
                while True :
                    if R>=len(Data) :
                        break
                    Sz=len(json.dumps(Data[R]))-2 # 减去左右的引号
                    if FilSz+Sz<=RstSz : # Data[R] 放得下
                        FilSz+=Sz
                        NewPack["Data"]+=Data[R]
                        R+=1
                    else : # Data[R] 放不下
                        break
                
                if FilSz==0 : # 一个字符都没有填充进去
                    self.__err__("","您定义的单个包长度过小")
                    return []
                
                NewPack["Data"]=Data[L:R]
                self.PackList.append(NewPack)
                if R>=len(Data) :
                    break
                L=R

            # 最后一个包的 NxtCode 是自定义的 Endcode
            self.PackList[-1]["NxtCode"]=self.EndCode

            # 最后来构造第一个包
            self.PackList[0]["PreCode"]=self.BeginCode
            self.PackList[0]["EndCode"]=self.EndCode
            self.PackList[0]["Chunks"]=len(self.PackList)
            self.PackList[0]["DataSize"]=len(Data)
            self.PackList[0]["Source"]=str((self.HostIp,self.HostMac,self.HostName,self.Port))
            self.PackList[0]["Destination"]=self.Destination
            self.PackList[0]["PackName"]=self.PackName
            self.PackList[0]["Description"]=self.Description
            
            # 将打包好的数据转换为 json 风格字符串
            jspklst=[]
            for pk in self.PackList :
                jspk=json.dumps(pk)
                rstspc=self.OnePackSize-len(jspk) # 计算剩余需要填充的空格数
                if rstspc<0 :
                    self.__err__("","您定义的单个包长度过小")
                    return []
                jspk+=" "*rstspc # 不足的位置用空格填补
                jspklst.append(jspk)
            
            return jspklst
        
        except Exception as e :
            self.__err__(e,"打包数据 "+Data+" 时出错")
            return []

