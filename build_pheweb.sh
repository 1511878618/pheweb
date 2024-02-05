#!/bin/bash
root_dir=$1
shell_folder=$(dirname $(readlink -f "$0")) # get real dir

# echo ${shell_folder}
# generate

set -ex

pheweb phenolist glob --star-is-phenocode "${1}/assoc-files/*.tsv.gz"

if [ -d "${shell_folder}/pheweb_cache" ]; then
    echo "using cache"
    if [ -f "${shell_folder}/pheweb_cache/gene_aliases-v44.sqlite3" ]; then
        mkdir -p ${root_dir}/generated-by-pheweb/resources/
        cp ${shell_folder}/pheweb_cache/gene_aliases-v44.sqlite3 ${root_dir}/generated-by-pheweb/resources/

    else
        echo "no found for local resources "
    fi

    # if [ -d "${shell_folder}/pheweb_cache/vep_data" ]; then
    #     cp -r "${shell_folder}/pheweb_cache/vep_data" "${root_dir}/vep_data"
    # else
    #     echo "no found for local vep data"
    # fi
else
    echo "not using local cache"
fi

# run
cd ${root_dir}
pheweb phenolist verify &&
    pheweb parse-input-files &&
    pheweb sites &&
    pheweb make-gene-aliases-sqlite3 &&
    pheweb add-rsids &&
    pheweb add-genes

# bash ${shell_folder}/etc/annotate_vep/run.sh
pheweb make-cpras-rsids-sqlite3 &&
    pheweb augment-phenos &&
    pheweb matrix &&
    pheweb gather-pvalues-for-each-gene &&
    pheweb manhattan &&
    pheweb top-hits &&
    pheweb qq &&
    pheweb phenotypes &&
    pheweb pheno-correlation

# mv generated-by-pheweb/sites/sites.tsv generated-by-pheweb/sites/sites.tsv.back
# mv sites-vep.tsv generated-by-pheweb/sites/sites.tsv
cp ${shell_folder}/pheweb_cache/gencode.v44.annotation.bed* ${root_dir}/generated-by-pheweb/resources/
