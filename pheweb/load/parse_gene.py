#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Description:       :
@Date     :2023/08/29 11:38:14
@Author      :Tingfeng Xu and 
@version      :1.0
@Source: https://github.com/statgen/locuszoom-api/blob/master/locuszoom/api/models/gene.py
'''



import argparse
import json
import textwrap
from copy import deepcopy
from subprocess import run
from myjob.utils import load_gff3, formatChr

try:
    from sortedcontainers import SortedSet
except ImportError:
    import pip

    pip.main(["install", "sortedcontainers"])
    from sortedcontainers import SortedSet


class Exon(object):
    cargs = "exon_id chrom start end strand".split()

    def __init__(self, **kwargs):
        for arg in Exon.cargs:
            self.__dict__[arg] = kwargs.get(arg)

    def to_dict(self):
        return deepcopy(self.__dict__)

    def __hash__(self):
        return hash(self.exon_id)

    def __eq__(self, other):
        return self.exon_id == other.exon_id

    def __lt__(self, other):
        if self.chrom == other.chrom:
            if self.start < other.start:
                return True
            else:
                return False
        else:
            raise ValueError("Comparing exons on separate chromosomes")


class Transcript(object):
    cargs = "transcript_id chrom start end strand".split()

    def __init__(self, **kwargs):
        for arg in Transcript.cargs:
            self.__dict__[arg] = kwargs.get(arg)

        self.exons = SortedSet()

    def add_exon(self, exon):
        self.exons.add(exon)

    def to_dict(self):
        dd = {}
        for k in Transcript.cargs:
            v = self.__dict__[k]
            if isinstance(v, (set, SortedSet)):
                v = list(v)

            dd[k] = v

        for e in self.exons:
            dd.setdefault("exons", []).append(e.to_dict())

        return dd

    def __hash__(self):
        return hash(self.transcript_id)

    def __eq__(self, other):
        return self.transcript_id == other.transcript_id

    def __lt__(self, other):
        if self.chrom == other.chrom:
            if self.start < other.start:
                return True
            else:
                return False
        else:
            raise ValueError("Comparing transcripts on separate chromosomes")


class Gene(object):
    cargs = "gene_id gene_name chrom start end strand gene_type".split()

    def __init__(self, **kwargs):
        for arg in Gene.cargs:
            self.__dict__[arg] = kwargs.get(arg)

        self.transcripts = SortedSet()
        self.exons = SortedSet()

    def add_transcript(self, transcript):
        self.transcripts.add(transcript)

    def add_exon(self, exon):
        self.exons.add(exon)

    def to_dict(self):
        """
        Convert this gene object into a dictionary, suitable for returning as JSON.

        Returns:
          dict
        """

        dd = {}
        for k in Gene.cargs:
            v = self.__dict__[k]
            if isinstance(v, (set, SortedSet)):
                v = list(v)

            dd[k] = v

        for t in self.transcripts:
            dd.setdefault("transcripts", []).append(t.to_dict())

        for e in self.exons:
            dd.setdefault("exons", []).append(e.to_dict())

        return dd


def test():
    g = Gene(gene_id="ENSG1", gene_name="ABC", chrom="1", start=42, end=800, strand="+")
    t = Transcript(transcript_id="ENST1", chrom="1", start=45, end=600, strand="+")

    e1 = Exon(exon_id="ENSE1", chrom="1", start=46, end=50, strand="+")

    e2 = Exon(exon_id="ENSE2", chrom="1", start=52, end=58, strand="+")

    g.add_transcript(t)
    t.add_exon(e1)
    t.add_exon(e2)
    g.add_exon(e1)
    g.add_exon(e2)

    from pprint import pprint

    pprint(g.to_dict())

    print("Trying to convert to JSON")
    js = json.dumps(g.to_dict())
    pprint(js)



def getParser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
        %prog - cond on top locis of GWAS summary file;
        summary File should be formatted as by GWASFomat.py, see GWASFomat.py for more details

        Author: Tingfeng Xu (xutingfeng@big.ac.cn)
        Version: 1.0
        """
        ),
    )

    parser.add_argument("-i", "--inputFolder", dest="inputFolder", required=True)
    parser.add_argument("-o", "--output", dest = "output", required=True)

    

    return parser


if __name__ == "__main__":
    parser = getParser()
    args = parser.parse_args()
    inputFolder = args.inputFolder
    output = args.output

    row_list = load_gff3(inputFolder)
    gene_list = {}
    # get genes 
    for row in row_list:
        if row["type_"] == "gene":
            gene_id = row["gene_id"]
            gene_list[gene_id] = Gene(**row)
        else:
            continue 
    # set transcripts and exons
    for row in row_list:
        if row["type_"] == "transcript":
            parent_gene_id = row["gene_id"]
            if parent_gene_id in gene_list:
                gene_list[parent_gene_id].add_transcript(Transcript(**row))
            else:
                raise ValueError(f"transcript without gene : {str(row)}")
        elif row["type_"] == "exon":
            parent_transcript_id = row["transcript_id"]
            parent_gene_id = row["gene_id"]
            if parent_gene_id in gene_list:
                gene_list[parent_gene_id].add_exon(Exon(**row))
                for transcript in gene_list[parent_gene_id].transcripts:
                    if transcript.transcript_id == parent_transcript_id:
                        transcript.add_exon(Exon(**row))
                        break       
        else: 
            continue 
    gene_list_json = [g.to_dict() for g in gene_list.values()]

    # save to bed 
    with open(output + ".bed", "w", encoding="utf-8") as f:
        f.write("chrom\tstart\tend\tjson\n")
        for gene in gene_list_json:
            chrom = formatChr(gene["chrom"])
            start = gene["start"]
            end = gene["end"]
            json_str = json.dumps(gene)
            f.write(f"{chrom}\t{start}\t{end}\t{json_str}\n")


    run(f"bgzip {output}.bed",shell = True)
    run(f"tabix -s 1 -b 2 -e 3 -c c -f {output}.bed.gz",shell = True)
                    


    # print(gene_list_json[0])
    # outer = {
    #     "data": gene_list_json,
    #     "meta": {
    #     "datasets": None
    #     },
    #     "lastPage": None
    # }
    # with open(output, "w", encoding="utf-8") as f:
    #     json.dump(outer, f, ensure_ascii=False, indent=4)






        