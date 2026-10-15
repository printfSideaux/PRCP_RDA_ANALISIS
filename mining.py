'''
Bibliotecas

-> requests, utilizada para fazer requisições HTTP
e acessar as páginas da internet ou baixar arquivos.

-> BeautifulSoup, utilizado para interpretar o HTML de uma página
e localizar elementos, como os links dos arquivos disponíveis.

-> urljoin, que combina uma URL base com um link relativo,
produzindo o endereço completo do arquivo.

-> Path, da biblioteca pathlib, para criar, manipular
e verificar caminhos de arquivos e diretórios no computador.

Esse script baixa os arquivos de precipitação do CPC (Climate Prediction Center) para os anos de 2007 a 2026.

'''

import requests 
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

# Lista com os links de vários anos
URL = [
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2007/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2008/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2009/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2010/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2011/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2012/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2013/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2014/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2015/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2016/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2017/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2018/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2019/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2020/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2021/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2022/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2023/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2024/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2025/",
    "https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/2026/",
]


def listar_arquivos(url):
    response = requests.get(url, timeout=30) # faz uma requisição HTTP GET para acessar o conteúdo da página
    response.raise_for_status() # verifica se a requisição foi bem-sucedida
    soup = BeautifulSoup(response.text, "html.parser") # interpreta o HTML da página e o "html.parser" é o analisador HTML utilizado pelo BeautifulSoup.

    arquivos = [] #lista vazia
    for link in soup.find_all("a", href=True): # localiza todos os elementos <a> (links) na página que possuem o atributo href (o endereço do link)
        href = link["href"] # obtém o valor do atributo href do link, que é o endereço do arquivo ou página vinculada ao link.
        if href.startswith(("?", "#")) or href.endswith("/"): # ignora links que comecam com ? ou #, que sao parametros ou referencias internas, ignora tbm links terminados em "/" que apontam para outros diretorios
            continue
        endereco = urljoin(url, href) # combina a URL base (url) com o link relativo (href) para formar o endereço completo do arquivo.
        if endereco.startswith(url): # verifica se o endereco comeca com URL do diretorio consultado
            arquivos.append(endereco) #coloca o endereco completo do arquivo na lista de arquivos encontrados
    return arquivos


def baixar(url_arquivo, pasta):
    nome = url_arquivo.split("/")[-1] # extrai o nome do arquivo a partir da URL, pegando a última parte após a barra "/"
    caminho = pasta / nome # cria o caminho completo para salvar o arquivo, combinando a pasta de destino com o nome do arquivo

    if caminho.exists(): # verifica se o arquivo já existe no caminho especificado
        return "pulado"

    with requests.get(url_arquivo, stream=True, timeout=60) as r: #inicia uma requisição HTTP GET para baixar o arquivo, com streaming de dados e um tempo limite de 60 segundos
        r.raise_for_status() # verifica se a requisição foi bem-sucedida, caso contrário, lança uma exceção
        with open(caminho, "wb") as f: #abre o arquivo no modo de escrita binária ("wb") para salvar o conteúdo baixado
            for bloco in r.iter_content(chunk_size=8192): # lê o conteúdo do arquivo em blocos de 8192 bytes (8 KB) para evitar sobrecarregar a memória
                f.write(bloco) # escreve cada bloco de dados no arquivo local, salvando o conteúdo baixado no disco
    return "baixado"

# Verifica se o arquivo python está sendo executado diretamente (não importado como módulo) e, nesse caso, executa o código dentro do bloco if.
if __name__ == "__main__":
    total_anos = len(URL) # calcula o número total de anos

    for i, url in enumerate(URL, start=1): # percorre todas a URLs da lista
        ano = [p for p in url.split("/") if p][-1] # divide a URL por "/" e remove as partes vazias, pra ficar apenas o ano do diretorio
        destino_ano = Path("dados_cpc") / ano # cria um caminho para a pasta de destino, combinando o diretório "dados_cpc" com o ano atual, resultando em algo como "dados_cpc/2007"
        destino_ano.mkdir(parents=True, exist_ok=True) # cria a pasta de destino, incluindo quaisquer diretórios pai necessários, e não gera erro se a pasta já existir

        print(f"[{i}/{total_anos}] carregando ano: {ano} (Pasta: {destino_ano.resolve().name})")
     
        try:
            arquivos = listar_arquivos(url) # chama a função listar_arquivos para obter a lista de arquivos disponíveis na URL do ano atual
            total_arquivos = len(arquivos) # calcula o número total de arquivos encontrados na URL do ano atual
            print(f"Total de arquivos encontrados: {total_arquivos}") 

            baixados_neste_ano = 0 # inicializa o contador de arquivos baixados nesta execução.
            pulados_neste_ano = 0 # inicializa o contador de arquivos pulados nesta execução.

            for idx, arq in enumerate(arquivos, start=1): # percorre a lista de arquivos encontrados na URL do ano atual, enumerando-os a partir de 1
                nome_arq = arq.split("/")[-1] # extrai o nome do arquivo a partir da URL, pegando a última parte após a barra "/"
                status = baixar(arq, destino_ano) # chama a função baixar para baixar o arquivo atual, passando a URL do arquivo e a pasta de destino, e armazena o status do download ("baixado" ou "pulado")
                
                if status == "baixado":
                    baixados_neste_ano += 1
                else:
                    pulados_neste_ano += 1

                
                restantes = total_arquivos - idx #alcula quantos faltam para terminar este ano
                print(f"  ({idx}/{total_arquivos}) arquivo: {nome_arq} -> status: {status.upper()} | faltam {restantes} para este ano.")

        except Exception as e:
            print(f"Erro ao processar o ano {ano}: {e}")

    print(f"\nAcabou")