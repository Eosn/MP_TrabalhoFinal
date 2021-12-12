#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

'''
Éllen Oliveira Silva Neves (20202BSI0071)
Trabalho solicitado pelo professor de Metodologia da Pesquisa, Maxwell Monteiro
'''

import argparse
import json
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt  # type: ignore
from pdftotext import PDF as PDFopener  # type: ignore
from reportlab.lib.pagesizes import A4, landscape  # type: ignore
from reportlab.lib.units import mm  # type: ignore
from reportlab.platypus import (KeepInFrame, SimpleDocTemplate,  # type: ignore
                                Table)
from svglib.svglib import svg2rlg  # type: ignore


def le_argumentos() -> Tuple[Path, Path]:
    'Lê argumentos do programa'
    parser = argparse.ArgumentParser(
        description='Cria relatorio com tabela e grafico'
    )
    parser.add_argument(
        'termos', type=Path,
        help='o caminho para o arquivo JSON contendo os termos a buscar'
    )
    parser.add_argument(
        'pasta', type=Path,
        help='o caminho da pasta a qual buscar PDFs'
    )
    args = parser.parse_args()
    return args.termos, args.pasta


def pdfpath2text(path: Path) -> str:
    'Converte o PDF fornecido como caminho em string'
    with path.open('rb') as file:
        return ''.join(list(PDFopener(file)))


def grafico_pizza_svg(**freqs: int) -> bytes:
    'Transforma dicionario de frequencias em grafico de pizza'
    rotulos, quantidades = zip(*freqs.items())
    axis = plt.subplots()[1]
    axis.pie(quantidades, labels=rotulos,
             autopct='%1.2f%%', startangle=90)
    axis.axis('equal')
    bio = BytesIO()
    plt.savefig(bio, format='svg', bbox_inches='tight')
    axis.cla()
    plt.clf()
    return bio.getvalue()


def conta_aparecimentos_termo(texto: str, termo: str) -> int:
    'Conta aparecimentos de string no texto'
    return len(texto.split(termo))-1  # Fencepost Problem


def conta_aparecimentos_termos(texto: str, termos: List[str]
                               ) -> Dict[str, int]:
    'Conta aparecimentos das strings no texto e retorna dicionario'
    return {termo: conta_aparecimentos_termo(texto, termo) for termo in termos}


class ContaAparecimentosDosTermos:
    'Conta aparecimentos das strings no texto e retorna dicionario'

    def __init__(self, termos: List[str]):
        self.termos = termos

    def __call__(self, texto: str):
        return conta_aparecimentos_termos(texto, self.termos)


def identifiable_dicts_to_table(
    identifiable_dicts: List[Tuple[str, Dict[str, Any]]],
    identity_label: str = 'Identity'
) -> List[List[str]]:
    'Transforma lista de dicionarios em tabela'
    all_labels: List[str] = list()
    for _, info in identifiable_dicts:
        all_labels = list(set(all_labels).union(info.keys()))
    all_labels.sort()
    return [[identity_label]+all_labels]+[
        [identity]+[
            str(info.get(label, ''))
            for index, label in enumerate(all_labels)
        ]
        for identity, info in identifiable_dicts
    ]


def soma_dicts(dcts: List[Dict[str, int]]) -> Dict[str, int]:
    d: Dict[str, int] = defaultdict(int)
    for dct in dcts:
        for k, v in dct.items():
            d[k] += v
    return dict(d)


def main():
    'Função principal'
    arq_json, pasta = le_argumentos()
    if not arq_json.is_file():
        raise FileNotFoundError(arq_json)
    if not pasta.is_dir():
        raise NotADirectoryError(pasta)
    descricao: Dict[str, List[str]] = json.loads(arq_json.read_text())
    termos: List[str] = descricao['termos']
    conta_termos = ContaAparecimentosDosTermos(termos)
    pdf_paths: List[Path] = sorted(filter(
        lambda p: p.suffix.lower() == '.pdf' and p.is_file(),
        pasta.rglob('*')
    ))
    pdf_paths_str = list(map(str, pdf_paths))
    pdf_texts = list(map(pdfpath2text, pdf_paths))
    pdf_stats = list(map(conta_termos, pdf_texts))
    data = identifiable_dicts_to_table(
        list(zip(pdf_paths_str, pdf_stats)),
        'Caminho')
    gpp = grafico_pizza_svg(**soma_dicts(pdf_stats))
    doc = SimpleDocTemplate(
        str(arq_json.with_suffix('.pdf')),
        pagesize=landscape(A4),
        leftMargin=30*mm,
        rightMargin=20*mm,
        topMargin=30*mm,
        bottomMargin=20*mm,
    )
    doc_el = []
    bigtbl = Table(data)
    kiftbl = KeepInFrame(0, 0, [bigtbl],
                         mode='shrink', hAlign='CENTER',
                         vAlign='MIDDLE', fakeWidth=False)
    doc_el.append(kiftbl)
    biggpp = svg2rlg(BytesIO(gpp))
    kifgpp = KeepInFrame(0, 0, [biggpp],
                         mode='shrink', hAlign='CENTER',
                         vAlign='MIDDLE', fakeWidth=False)
    doc_el.append(kifgpp)
    doc.build(doc_el)
    return 0


if __name__ == "__main__":
    main()
