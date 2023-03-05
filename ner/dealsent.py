import json
def predeal(sentences,limit=126):
    newsens=[]
    for sen in sentences:
        if len(sen)<=limit:
            newsens.append(sen)
            continue
        start=0
        end = 0
        while len(sen)-end > limit:
            end=end+limit-1
            while sen[end]!="。":
                end = end-1
            newsens.append(sen[start:end+1])
            start = end+1
            end = end+1
            # print(newsens) 
        
        newsens.append(sen[start:])
        
        
    return newsens
    
def getsentences(filename):
    sentences = []
    authors=[]
    with open(filename, "r",encoding="utf8") as f:
        row_data = json.load(f)
        for d in row_data:
            if "全文" in d and d["全文"]!="":
                sentences.append(d["全文"])
                authors.append(d["作者"])
            if "款識" in d and d["款識"]!="":
                sentences.append(d["款識"])
                authors.append(d["作者"])
    return sentences,authors

def huachuang(onesentence,limit=8):
    chailist = onesentence.split("。")[:-1]
    newlist = []
    # now = 0
    for now in range(len(chailist)-1):
        ts = ""
        while len(ts+chailist[now]+"。")<limit:
            ts = ts+chailist[now]+"。"
            now = now+1
            if now>=len(chailist):break
        newlist.append(ts)
        if now>=len(chailist):break
    
    return newlist
        
def predealh(sentences,limit=126):
    dealsents = []
    for sentence in sentences:
        if len(sentence)<=limit:
            dealsents.append([])
        else:
            # print(len(sentence))
            newlist= huachuang(sentence,limit)
            # print(len(newlist))
            dealsents.append(newlist)
    return dealsents


if __name__ == '__main__':
    # sentences = ["你的是我。对的a。是谁呢阿桑的队。是德国公共。"]
    sentences,atuhors = getsentences("orig/6.json")
    print(atuhors)
    print(predealh(sentences))
    # with open("qhqs.txt","w",encoding="utf8") as f:
    #     for s in sentences:
    #         f.writelines(s+"\n")

