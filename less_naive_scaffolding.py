from argparse import ArgumentParser
from Bio import SeqIO
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from operator import itemgetter
from itertools import combinations


parser = ArgumentParser()
parser.add_argument("efile", help="Error rate file")
parser.add_argument("summaryfile", help="Contig Distance Summary file")
parser.add_argument("contigfile", help="Contig File")
#parser.add_argument("--maxdev", help="Maximal deviation", type=float, default=2.0)
parser.add_argument("--mindepth", help="Minimal depth", type=int, default=20)

args = parser.parse_args()

reads = {}
greads = {}
cgreads = []
contigs = {}


for read in SeqIO.parse(args.contigfile, "fasta"):
    contigs[read.id] = len(read.seq)

print("Nr. of scaffolds: " + str(len(contigs)))

class Scaffold:
    sr_info = dict()
    lr_info = dict()
    contigs = dict()
    contigset = set()
    sequence = ""
    nr_of_scaffolds = 0
    #id = 
    # All contigs will have scaffold coordinates.
    # Before scaffolds are merged all scaffold coordinates 
    # are equal to long read coordinates of the orginal long read 
    # that initialized the scaffold
    
    def __init__(self):
        Scaffold.nr_of_scaffolds += 1
        #lr_info[lr[0]] = lr[1]

    def add_sr_info(self, sr):
        pass
    
    def add_lr_info(self, lr):
        self.lr_info[lr[0]] = lr[1]
        for part in lr[1]["maps"]:
            if part["contig"].startswith("QBL"):
                contigset.add(part["contig"])

    def print_contigset():
        


    def del_lr_info(self, lrid):
        pass
        # can be complicated
        # probably it's easiest to create a new object
        # with all the reads except for the specified lrid

    def del_sr_info(self, srid):
        pass
    
    @classmethod
    def init_from_LR(cls,lr):
        newinst = cls()
        newinst.add_lr_info(lr)
        return newinst

    @staticmethod
    def return_contig_set():
        return contigset

# nanopore read info
with open(args.efile) as f:
    for line in f:
        sline = line.split()
        rid = sline[0]
        ctg = sline[1]
        strand = int(sline[8])
        scr = int(sline[5])
        ecr = int(sline[6])
        scc = int(sline[9])
        ecc = int(sline[10])
        lc = int(sline[11])
        payload = {"contig":ctg,"strand":strand,"scr":scr,"ecr":ecr,"scc":scc,"ecc":ecc,"lc":lc}
        if rid in reads:
            reads[rid]["maps"].append(payload)
        else:
            reads[rid] = {}
            reads[rid]["length"] = int(sline[7])
            reads[rid]["maps"] = [payload]

scaffolds = {}
# get interesting reads
# and sort contigs by left coordinate
greadst = {}
for rid in reads:
    counter = 0
    for item in reads[rid]["overlaps"]:
        if item["contig"].endswith("QBL"):
            greadst[rid] = reads[rid]
            break

for rid in greadst:
    #print(reads[rid]["overlaps"])
    nscaff = Scaffold.init_from_LR((rid,reads[rid]))
    scaffolds[id(nscaff)] = nscaff
    soverlaps = sorted(reads[rid]["overlaps"], key = itemgetter("scr"))
    greads[rid] = greadst[rid]
    greads[rid]["overlaps"]=soverlaps

print(scaffolds)



# cluster np-reads 
print("scaffolding long reads ....")
contig2cluster = {}
creads = {}
clusternr = 0
while len(greads) > 0:
    clusternr += 1
    current_cluster = {}
    current_contigs = set()
    # take a random read and build a cluster from it
    cr = greads.popitem()
    current_cluster[cr[0]] = cr[1]
    olen = 0
    while len(current_cluster) != olen:
        olen = len(current_cluster)
        for contig in cr[1]["overlaps"]:
            if not contig["contig"].startswith("chr"):
                contigs.pop(contig["contig"], None)
                current_contigs.add(contig["contig"])
                contig2cluster[contig["contig"]] = clusternr
        for readid,readval in greads.items():
            contig_found = False
            for contig in readval["overlaps"]:
                if not contig["contig"].startswith("chr"):
                    if contig["contig"] in current_contigs:
                        contig_found = True
                        current_cluster[readid] = readval
                        cr = (readid, greads.pop(readid))
                        break
                   
            if contig_found:
                break
    creads[clusternr] = current_cluster
print("Nr. of scaffolds: " + str(clusternr+len(contigs)) + " (" + str(clusternr) + " cluster + " + str(len(contigs))+ " contigs)")

# simpler data structure to collect contigs into scaffolds
#scaffolds={}
for i, cluster in creads.items():
    current_contigs = set([])
    for readid,read in cluster.items():
        #print(read)
        for contig in read["overlaps"]:
            if not contig["contig"].startswith("chr"):
                current_contigs.add(contig["contig"])
    scaffolds[i] = current_contigs
#print(scaffolds)

def addcontig(ctg, cluster):
    contig2cluster[ctg] = cluster
    scaffolds[cluster].add(ctg)
    contigs.pop(ctg, None)
    
def mergecluster(cluster1, cluster2):
    for contig in scaffolds[cluster2]:
        contig2cluster[contig] = cluster1
        scaffolds[cluster1].add(contig)
    scaffolds.pop(cluster2)

# very lenient clustering of short reads
print("scaffolding short reads ....")
with open(args.summaryfile) as f:
    for line in f:
        sline = line.split()
        ctg1 = sline[0].split("_")[0].strip("+").strip("-")
        ctg2 = sline[0].split("_")[1].strip("+").strip("-")
        if sline[1] == "NA":
            continue
        if int(sline[2]) < args.mindepth:
            continue
        #moddist = float(sline[1])
        if ctg1 in contig2cluster:
            if ctg2 in contig2cluster:
                if contig2cluster[ctg1] != contig2cluster[ctg2]:
                    #print("merging clusters " + str(contig2cluster[ctg1]) + " and " + str(contig2cluster[ctg2]))
                    mergecluster(contig2cluster[ctg1], contig2cluster[ctg2])
            else:
                addcontig(ctg2, contig2cluster[ctg1])
            #print("cluster of ctg1 (" + ctg1 + "): " + str(contig2cluster[ctg1]))
        elif ctg2 in contig2cluster:
            addcontig(ctg1, contig2cluster[ctg2])
        else:
            clusternr += 1
            #print("new cluster: " + str(clusternr))
            scaffolds[clusternr] = set([ctg1, ctg2])
            contig2cluster[ctg1] = clusternr
            contig2cluster[ctg2] = clusternr
            contigs.pop(ctg1, None)
            contigs.pop(ctg2, None)
            
            
print("Nr. of scaffolds: " + str(len(scaffolds)+len(contigs)) + " (" + str(len(scaffolds)) + " cluster + " + str(len(contigs))+ " contigs)")
#print(contigs)
for scaf in scaffolds:
    print(scaffolds[scaf])
    sys.exit(0)
def get_rightmost_contig(scaf_id):
    print(creads[scaf_id])
    if len(creads[scaf_id]) > 1:
        print("not implemented yet")
    else:
        rid, read = creads[scaf_id].items()
        for ov in read["overlaps"]:
            print(ov)

#get_rightmost_contig(1)
#sys.exit(0)
