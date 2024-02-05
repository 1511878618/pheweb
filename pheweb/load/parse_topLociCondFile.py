#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Description:       :
@Date     :2023/08/28 19:42:08
@Author      :Tingfeng Xu
@version      :1.0
'''
import re

import pathlib as p
import argparse
from subprocess import run


import textwrap


import gzip 

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


    inputFolder = p.Path(inputFolder)
    phenoPathList = [x for x in inputFolder.iterdir() if x.is_dir()]

    out=[]
    for phenoPath in phenoPathList:
        lociPathList = [x for x in phenoPath.iterdir() if x.is_dir()]
        for lociPath in lociPathList:
            lociName = lociPath.name.split("_")
            if len(lociName) != 3: # correct for lociName with chr_centerPos with width 2mb
                chr = int(lociName[0])
                start = int(lociName[1]) - 1000000 if int(lociName[1]) - 1000000 > 0 else 1
                end = int(lociName[1]) + 1000000
            else:
                chr = int(lociName[0])
                start = int(lociName[1])
                end = int(lociName[2])
            
            condPathList = [x for x in lociPath.glob("*.gz")]
            for each in condPathList:
                # print(each.name)
                condName = int(re.findall(r"\d+",each.name)[0])+1
                # if condName == 0:
                    # continue 
                # else:
                out.append({"chr":chr,"start":start,"end":end,"phenocode":phenoPath.name,"condTime":condName,"path":each})
    out = sorted(out,key = lambda x: (x["chr"],x["start"],x["end"]))

    with open(output + ".tsv", "w") as f: 
        f.write("chr\tstart\tend\tphenocode\tcondTime\tfile\n")
        for each in out:
            f.write(f"{each['chr']}\t{each['start']}\t{each['end']}\t{each['phenocode']}\t{each['condTime']}\t{each['path']}\n")
    run(f"bgzip {output}.tsv",shell = True)
    run(f"tabix -s 1 -b 2 -e 3 -c c -f {output}.tsv.gz",shell = True)
                    



 
