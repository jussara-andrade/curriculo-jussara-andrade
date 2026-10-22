"""
Gera os PDFs do currículo (PT, EN, ES, DE) a partir do index.html e
embute os quatro no próprio index.html, para o botão "Baixar PDF".

Rode sempre que alterar o conteúdo do currículo:
    py gerar_pdfs.py

Precisa do Google Chrome ou do Microsoft Edge instalado.
Não usa bibliotecas extras. Os PDFs também ficam salvos na pasta "pdf".
"""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PASTA = Path(__file__).resolve().parent
HTML = PASTA / "index.html"
SAIDA = PASTA / "pdf"

# Mesmos nomes usados no botão "Baixar PDF" (campo "file" no index.html)
ARQUIVOS = {
    "pt": "Jussara_Andrade_Pereira_Curriculo_PT.pdf",
    "en": "Jussara_Andrade_Pereira_Resume_EN.pdf",
    "es": "Jussara_Andrade_Pereira_Curriculum_ES.pdf",
    "de": "Jussara_Andrade_Pereira_Lebenslauf_DE.pdf",
}

# Bloco do index.html onde os PDFs ficam guardados (em base64)
BLOCO = re.compile(r'(<script type="application/json" id="pdfs">)(.*?)(</script>)', re.S)


def achar_navegador():
    """Procura o Chrome ou o Edge nos caminhos padrão do Windows e no PATH."""
    programas = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    programas_x86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")
    candidatos = [
        Path(programas, "Google", "Chrome", "Application", "chrome.exe"),
        Path(programas_x86, "Google", "Chrome", "Application", "chrome.exe"),
        Path(local, "Google", "Chrome", "Application", "chrome.exe") if local else None,
        Path(programas_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
        Path(programas, "Microsoft", "Edge", "Application", "msedge.exe"),
    ]
    for caminho in candidatos:
        if caminho and caminho.is_file():
            return str(caminho)
    for nome in ("chrome", "msedge", "google-chrome", "chromium"):
        achado = shutil.which(nome)
        if achado:
            return achado
    return None


def gerar_pdf(navegador, idioma, destino, perfil):
    """Abre o index.html no idioma pedido e imprime em PDF (A4, sem cabeçalho/rodapé)."""
    url = HTML.as_uri() + "#" + idioma
    subprocess.run(
        [
            navegador,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={perfil}",
            "--no-pdf-header-footer",
            "--virtual-time-budget=5000",  # espera a fonte e o idioma carregarem
            f"--print-to-pdf={destino}",
            url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=180,
        check=False,
    )
    if not destino.is_file() or destino.stat().st_size == 0:
        sys.exit(f"Erro: o navegador não gerou {destino.name}.")


def main():
    if not HTML.is_file():
        sys.exit("Erro: index.html não encontrado nesta pasta.")

    navegador = achar_navegador()
    if not navegador:
        sys.exit("Erro: instale o Google Chrome ou o Microsoft Edge.")
    print(f"Navegador: {navegador}")

    # 1. Gera um PDF por idioma na pasta "pdf"
    SAIDA.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as perfil:
        for idioma, nome in ARQUIVOS.items():
            destino = SAIDA / nome
            try:
                destino.unlink(missing_ok=True)
            except PermissionError:
                sys.exit(f"Erro: feche o arquivo pdf/{nome} e rode de novo.")
            gerar_pdf(navegador, idioma, destino, perfil)
            print(f"  {idioma.upper()}: pdf/{nome} ({destino.stat().st_size // 1024} KB)")

    # 2. Embute os quatro PDFs no index.html
    dados = {
        idioma: base64.b64encode((SAIDA / nome).read_bytes()).decode("ascii")
        for idioma, nome in ARQUIVOS.items()
    }
    html = HTML.read_text(encoding="utf-8")
    if not BLOCO.search(html):
        sys.exit('Erro: bloco <script id="pdfs"> não encontrado no index.html.')
    html = BLOCO.sub(lambda m: m.group(1) + json.dumps(dados) + m.group(3), html, count=1)
    HTML.write_text(html, encoding="utf-8", newline="\n")

    print("Pronto! PDFs atualizados e embutidos no index.html.")


if __name__ == "__main__":
    main()
