import itertools
import numpy as np
from torch.utils.data import Dataset as tDataset
import datetime

PAD_ID = 0
class DateData(tDataset):
    def __init__(self,n):
        np.random.seed(1)
        self.date_cn = []
        self.date_en = []
        for timestamp in np.random.randint(143835585, 2043835585, n):
            date = datetime.datetime.fromtimestamp(timestamp)
            self.date_cn.append(date.strftime("%y-%m-%d"))
            self.date_en.append(date.strftime("%d/%b/%Y"))
        self.vocab= set(
            [str(i) for i in range(0,10)] + ["-","/","<GO>","<EOS>"] + [i.split("/")[1] for i in self.date_en]
        )
        self.v2i = {v:i for i,v in enumerate(sorted(list(self.vocab)), start=1)}
        self.v2i["<PAD>"] = PAD_ID
        self.vocab.add("<PAD>")
        self.i2v = {i:v for v,i in self.v2i.items()}
        self.x,self.y=[],[]
        for cn,en in zip(self.date_cn,self.date_en):
            self.x.append([self.v2i[v] for v in cn])
            self.y.append([self.v2i["<GO>"], ] + [self.v2i[v] for v in en[:3]] + [
                self.v2i[en[3:6]]] + [self.v2i[v] for v in en[6:]] + [self.v2i["<EOS>"],])
        self.x,self.y = np.array(self.x),np.array(self.y)
        self.start_token = self.v2i["<GO>"]
        self.end_token = self.v2i["<EOS>"]
    
    def __len__(self):
        return len(self.x)
    
    @property
    def num_word(self):
        return len(self.vocab)
    
    def __getitem__(self, index):
        return self.x[index],self.y[index], len(self.y[index])-1
    
    def idx2str(self,idx):
        x=[]
        for i in idx:
            x.append(self.i2v[i])
            if i == self.end_token:
                break
        return "".join(x)

def pad_zero(seqs, max_len):
    padded = np.full((len(seqs), max_len), fill_value=PAD_ID, dtype=np.int32)
    for i, seq in enumerate(seqs):
        padded[i, :len(seq)] = seq
    return padded

class Dataset:
    def __init__(self,x,y,v2i,i2v):
        self.x,self.y = x,y
        self.v2i, self.i2v = v2i,i2v
        self.vocab = v2i.keys()
    
    def sample(self,n):
        b_idx = np.random.randint(0,len(self.x),n)
        bx,by = self.x[b_idx],self.y[b_idx]
        return bx,by
    @property
    def num_word(self):
        return len(self.v2i)

def process_w2v_data(corpus,skip_window=2,method = "skip_gram"):
    all_words = [sentence.split(" ") for sentence in corpus]
    # groups all the iterables together and produces a single iterable as output
    all_words = np.array(list(itertools.chain(*all_words)))
    vocab,v_count = np.unique(all_words,return_counts=True)
    vocab = vocab[np.argsort(v_count)[::-1]]
    
    print("All vocabularies are sorted by frequency in decresing oreder")
    v2i = {v:i for i,v in enumerate(vocab)}
    i2v = {i:v for v,i in v2i.items()}

    pairs = []
    js = [i for i in range(-skip_window,skip_window+1) if i!=0]

    for c in corpus:
        words = c.split(" ")
        w_idx = [v2i[w] for w in words]
        if method == "skip_gram":
            for i in range(len(w_idx)):
                for j in js:
                    if i+j<0 or i+j>= len(w_idx):
                        continue
                    pairs.append((w_idx[i],w_idx[i+j]))
        elif method.lower() == "cbow":
            for i in range(skip_window,len(w_idx)-skip_window):
                context = []
                for j in js:
                    context.append(w_idx[i+j])
                pairs.append(context+[w_idx[i]])
        else:
            raise ValueError
    
    pairs = np.array(pairs)
    print("5 expample pairs:\n",pairs[:5])
    if method.lower()=="skip_gram":
        x,y = pairs[:,0],pairs[:,1]
    elif method.lower() == "cbow":
        x,y = pairs[:,:-1],pairs[:,-1]
    else:
        raise ValueError
    return Dataset(x,y,v2i,i2v)
