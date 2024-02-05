
from flask import url_for, Response, redirect

try:
    import pyBigWig 
except ImportError:
    import pip
    pip.main(['install','pyBigWig'])
    import pyBigWig

try:
    import tabix 
except ImportError:
    import pip
    pip.main(['install','tabix'])
    import tabix
from ..file_utils import MatrixReader, IndexedVariantFileReader, get_filepath, get_generated_path, get_pheno_filepath


import random
import re
import itertools
import json
from typing import Optional,Dict,List,Any


class _Get_Pheno_Region:
    @staticmethod
    def _rename(d:dict, oldkey, newkey):
        d[newkey] = d[oldkey]
        del d[oldkey]

    @staticmethod
    def _dataframify(list_of_dicts:List[Dict[Any,Any]]) -> Dict[Any,list]:
        '''converts [{a:1,b:2}, {a:11,b:12}] -> {a:[1,11], b:[2,12]}'''
        keys = set(itertools.chain.from_iterable(list_of_dicts))
        dataframe: Dict[Any,list] = {k:[] for k in keys}
        for d in list_of_dicts:
            for k,v in d.items():
                dataframe[k].append(v)
        return dataframe

    @staticmethod
    def get_pheno_region(phenocode:str, chrom:str, pos_start:int, pos_end:int) -> dict:
        variants = []
        with IndexedVariantFileReader(phenocode) as reader:
            for v in reader.get_region(chrom, pos_start, pos_end+1):
                v['id'] = '{chrom}:{pos}_{ref}/{alt}'.format(**v)
                # TODO: change JS to make these unnecessary
                v['end'] = v['pos']
                _Get_Pheno_Region._rename(v, 'chrom', 'chr')
                _Get_Pheno_Region._rename(v, 'pos', 'position')
                _Get_Pheno_Region._rename(v, 'rsids', 'rsid')
                _Get_Pheno_Region._rename(v, 'pval', 'pvalue')
                variants.append(v)

        df = _Get_Pheno_Region._dataframify(variants)

        return {
            'data': df,
            'lastpage': None,
        }
get_pheno_region = _Get_Pheno_Region.get_pheno_region



def parse_region(region):
    """
    region:1:22-444
    """
    chr = region.split(":")[0]
    start = region.split(":")[1].split("-")[0]
    end = region.split(":")[1].split("-")[1]
    return chr,start,end

def read_tabix(filePath,region):
    chr, start,end = parse_region(region)
    tb = tabix.open(filePath)

    try: # 尝试 2:1234-4567
        query_region = f"{chr}:{start}-{end}"
        records = tb.querys(query_region)
    except Exception:
        records = None 
    if records is not None:
        return list(records)
    else:
        return None
def query_gene_to_json(region, filePath):
    """
    conditional tsv.gz have four cols: 
    chr, start, end, json_str

    will return json
    """
    res = read_tabix(filePath,region)
    if res is not None:
        res = [json.loads(i[3]) for i in res]
    return res 
def get_gene_region(chrom:str, pos_start:int, pos_end:int) -> dict:
    res = query_gene_to_json(f"{chrom}:{pos_start}-{pos_end}", get_filepath("gencode"))

    return {
        'data': res,
        'lastpage': None,
    }
def query_conditional_to_json(region,phenocode=None):
    """
    read_tabix will return a list of tuple:[chr, start, end, condTime, filePath]
    """
    filePath = get_filepath("topLociCond")
    res = read_tabix(filePath,region)
    if res is not None:
        if phenocode is not None:
            phenocode = phenocode.lower()
            res = [ {"chr":i[0], "start":i[1], "end":i[2],"phenocode":i[3],"condTime":i[4], "filePath": i[5]} for i in res if i[3] == phenocode]
        else:
            res = [ {"chr":i[0], "start":i[1], "end":i[2],"phenocode":i[3],"condTime":i[4], "filePath": i[5]} for i in res]
    return {"data":res} 
def query_cond_file(region,fileName):
    filePath = get_generated_path("resources/topLociCond/")+fileName
    # return filePath
    try:
        res = read_tabix(filePath,region)
    # format 
    except:
        return {"error":filePath}
    chr, start,end = parse_region(region)
    tb = tabix.open(filePath)

    try: # 尝试 2:1234-4567
        query_region = f"{chr}:{start}-{end}"
        records = tb.querys(query_region)
    except Exception:
        return {"data":None}
    if records is not None:
        # 满足lz.js 1.13.0 的读取要求，避免更改js代码
        res = {
            "af":[],
            "alt":[],
            "beta":[],
            "chr":[],
            "end":[],
            "id":[],
            "position":[],
            "pvalue":[],
            "ref":[],
            "rsid":[],
            "sebeta":[],
               }
        for record in records:    
            res["af"].append(float(record[5]))
            res["alt"].append(record[3])
            res["beta"].append(float(record[6]))
            res["chr"].append(record[0])
            res["end"].append(record[1])
            res["id"].append(f"{record[0]}:{record[1]}_{record[2]}/{record[3]}")
            res["position"].append(record[1])
            res["pvalue"].append(float(record[4]))
            res["ref"].append(record[2])
            res["rsid"].append(None) 
            res["sebeta"].append(float(record[7]))
    return {"data":res}



class _ParseVariant:
    chrom_regex = re.compile(r'(?:[cC][hH][rR])?([0-9XYMT]+)')
    chrom_pos_regex = re.compile(chrom_regex.pattern + r'[-_:/ ]([0-9]+)')
    chrom_pos_ref_alt_regex = re.compile(chrom_pos_regex.pattern + r'[-_:/ ]([-AaTtCcGg\.]+)[-_:/ ]([-AaTtCcGg\.]+)')
    def parse_variant(self, query, default_chrom_pos=True):
        match = self.chrom_pos_ref_alt_regex.match(query) or self.chrom_pos_regex.match(query) or self.chrom_regex.match(query)
        g = match.groups() if match else ()

        if default_chrom_pos:
            if len(g) == 0: g += ('1',)
            if len(g) == 1: g += (0,)
        if len(g) >= 2: g = (g[0], int(g[1])) + tuple([bases.upper() for bases in g[2:]])
        return g + tuple(itertools.repeat(None, 4-len(g)))
parse_variant = _ParseVariant().parse_variant

class _GetVariant:
    def get_variant(self, query:str) -> Optional[Dict[str,Any]]:
        chrom, pos, ref, alt = parse_variant(query)
        assert None not in [chrom, pos, ref, alt]
        if not hasattr(self, '_matrix_reader'):
            self._matrix_reader = MatrixReader()
        with self._matrix_reader.context() as mr:
            v = mr.get_variant(chrom, pos, ref, alt)
        if v is None: return None
        v['phenos'] = list(v['phenos'].values())
        v['variant_name'] = '{} : {:,} {} / {}'.format(chrom, pos, ref, alt)
        return v
get_variant = _GetVariant().get_variant




def get_random_page() -> Optional[str]:
    with open(get_filepath('top-hits-1k')) as f:
        hits = json.load(f)
    if not hits:
        return None
    hits_to_choose_from = [hit for hit in hits if hit['pval'] < 5e-8]
    if len(hits_to_choose_from) < 10:
        hits_to_choose_from = hits[:10]
    hit = random.choice(hits_to_choose_from)
    r = random.random()
    if r < 0.4:
        return url_for('.pheno_page', phenocode=hit['phenocode'])
    elif r < 0.8:
        return url_for('.variant_page', query='{chrom}-{pos}-{ref}-{alt}'.format(**hit))
    else:
        offset = int(50e3)
        return url_for('.region_page',
                       phenocode=hit['phenocode'],
                       region='{}:{}-{}'.format(hit['chrom'], hit['pos']-offset, hit['pos']+offset))
    # TODO: check if this hit is inside a gene. if so, include that page.

def relative_redirect(url:str) -> Response:
    # `flask.redirect(url)` turns relative URLs into absolute.
    # But modern browsers allow relative location header.
    # And I want relative to avoid thinking about http/https and hostname.
    # Only a few places in pheweb need absolute URLs (eg, auth), and everywhere else can just use relative.
    return redirect(url, Response=RelativeResponse)
class RelativeResponse(Response):
    autocorrect_location_header = False
