import json

class TcpTranUnPack :
    def __init__(self,BeginCode="This is a Begin.",EndCode="This is the End.") :
        self.Error=[]
        self.BeginCode=BeginCode
        self.EndCode=EndCode
        self.Packs={}
    def __err__(self,stde,mye) :
        self.Error.append((stde,mye))
    def __rpckey__(self,dic,old,new):
        try :
            data=dic[old]
            del dic[old]
            dic[new]=data
            return dic
        except Exception as e :
            self.__err__(e,"在替换字典 "+str(dic)+"键值"+str(old)+"时出错")
            return {}
    def UnPack(self,JsonPack:str) :
        try :
            try :
                Pack=json.loads(JsonPack)
            except Exception as e :
                self.err(e,"无法对 "+JsonPack+" 使用方法 json.loads()")
                return
            
            PackPreCode=Pack.get("PreCode")
            PackNxtCode=Pack.get("NxtCode")
            if PackPreCode==None :
                self.__err__("","这是一个没有 PreCode 的包:"+JsonPack)
                return
            if PackNxtCode==None :
                self.__err__("","这是一个没有 NxtCode 的包:"+JsonPack)
                return

            if PackPreCode != self.BeginCode and PackPreCode not in self.Packs.keys() : # 不是新包并且之前没有存在过
                self.__err__("","这个包没有前缀,可能不完整:"+JsonPack)

            if self.Packs.get(PackPreCode)==None :
                self.Packs[PackPreCode]=[]
            self.Packs[PackPreCode].append(Pack)
            self.Packs=self.__rpckey__(self.Packs,PackPreCode,PackNxtCode) # 更新 PreCode->NxtCode
            
            if PackNxtCode==self.EndCode : # 如果是最后一个包
                unpack={}
                for pk in self.Packs[PackNxtCode] :
                    for ky in pk :
                        if ky!="PreCode" and ky!="NxtCode" and ky!="EndCode" : # 排除这三种没有携带信息的键值
                            if unpack.get(ky)==None :
                                unpack[ky]=""
                            unpack[ky]+=str(pk[ky]) # 合并其它键值
                return unpack
            else :
                return {}
        
        except Exception as e :
            self.__err__(e,"在对包 "+JsonPack+" 解压时出错")
            return {}

