"""
Bibliotecas

-> glob, utilizada para buscar arquivos em diretórios 
com base em padrões de nomes (como "precipitacao_*.csv").

-> os, utilizada para manipular caminhos de arquivos 
e diretórios, verificar existência de arquivos, etc.

-> pandas, utilizada para ler, manipular e gravar
 tabelas de dados (DataFrames).

-> geopandas, uma extensão do pandas que adiciona suporte 
a geometrias (pontos, linhas, polígonos) e operações espaciais.

-> geobr, utilizada para baixar malhas oficiais do Brasil
 (como municípios e estados) do IBGE.

Esse script processa arquivos CSV de precipitação, cruza as coordenadas
com a malha de municípios e gera novos CSVs com informações de município, estado,
UF e região para cada ponto de precipitação.

"""

import glob                      
import os                       
import pandas as pd             
import geopandas as gpd       
import geobr              

PATH = "CSV"  # pasta onde ficam os CSVs
PADRAO = os.path.join(PATH, "precipitacao_*.csv") # padrão de busca: CSV/precipitacao_<qualquer coisa>.csv
SEP = ";"  # separador de colunas dos CSVs
COL_LAT, COL_LON = "lat", "lon"  # nomes das colunas de latitude e longitude
TABELA_LOCAIS = os.path.join(PATH, "tabela_locais.csv") # arquivo de cache com coordenada -> município/estado

def listar_arquivos():
    arquivos = sorted(glob.glob(PADRAO)) # lista todos os arquivos que batem com o padrão, em ordem alfabética e ignora arquivos que já foram gerados por este script
    return [a for a in arquivos if not a.endswith("_com_local.csv")]  # remove os de saída, para não reprocessar o que já foi gerado

def construir_tabela_locais(arquivos):
    """
    Cruza todas as coordenadas únicas de todos os arquivos com a malha de municípios.
    Para cada coordenada, determina o município, estado, UF e região.
    Se a coordenada não cair em nenhum município, procura o município mais próximo (até 30 km).
    Salva o resultado em TABELA_LOCAIS para reaproveitamento futuro.
    """
    partes = [
        pd.read_csv(a, sep=SEP, usecols=[COL_LAT, COL_LON]).drop_duplicates()  # lê só lat/lon de cada arquivo e tira repetidos
        for a in arquivos                                                      # faz isso para cada arquivo da lista
    ]
    coords = pd.concat(partes).drop_duplicates().reset_index(drop=True)  # junta tudo, remove repetidos entre arquivos e refaz o índice
    print(f"Coordenadas únicas em todos os arquivos: {len(coords)}")   # informa quantos pontos únicos serão localizados

    lon_corr = coords[COL_LON].where(coords[COL_LON] <= 180, coords[COL_LON] - 360)  # converte longitudes 0-360 para -180 a 180 (o CPC usa 0-360)
    pontos = gpd.GeoDataFrame(
        coords.copy(),  # Copia a tabela de coordenadas
        geometry=gpd.points_from_xy(lon_corr, coords[COL_LAT]),  # cria um ponto geométrico (x=lon, y=lat) para cada linha
        crs="EPSG:4326",  # sistema de coordenadas: lat/lon padrão (WGS84)
    )

    municipios = geobr.read_municipality(code_muni="all", year=2020).to_crs("EPSG:4326")  # baixa polígonos de todos os municípios (2020) e garante o mesmo CRS
    municipios = municipios[["name_muni", "name_state", "abbrev_state", "name_region", "geometry"]]  # mantém só as colunas necessárias 
    municipios = municipios.rename(columns={
        "name_muni": "municipio", "name_state": "estado", # renomeia para nomes mais simples
        "abbrev_state": "uf", "name_region": "regiao",
    })

    juncao = gpd.sjoin(pontos, municipios, how="left", predicate="within")  # para cada ponto, acha o município que o contém (junção espacial)
    juncao = juncao[~juncao.index.duplicated(keep="first")]  # se um ponto caiu em 2 polígonos (borda), fica só com o primeiro

    faltando = juncao["municipio"].isna()  # marca os pontos que não caíram em nenhum município (ex.: mar, fora do Brasil)
    if faltando.any():   # se existir algum ponto sem município
        pts_proj = pontos.loc[faltando].to_crs("EPSG:5880")  # projeta esses pontos para um CRS em metros (SIRGAS 2000 Polyconic)
        mun_proj = municipios.to_crs("EPSG:5880")  # projeta os municípios para o mesmo CRS, para medir distâncias em metros
        proximos = gpd.sjoin_nearest(pts_proj, mun_proj, how="left", max_distance=30000) # acha o município mais próximo, até 30 km de distância
        proximos = proximos[~proximos.index.duplicated(keep="first")]  # remove duplicatas em caso de empate de distância
        for col in ["municipio", "estado", "uf", "regiao"]: # para cada coluna de localização
            juncao.loc[faltando, col] = proximos[col] # preenche os pontos faltantes com os dados do município mais próximo

    tabela = pd.DataFrame(juncao[[COL_LAT, COL_LON, "municipio", "estado", "uf", "regiao"]])  # fica só com lat, lon e os dados de localização (sem geometria)
    tabela.to_csv(TABELA_LOCAIS, sep=SEP, index=False)  # guarda para reutilizar  # Salva a tabela em disco como cache
    return tabela   


def gerar_csvs():
    arquivos = listar_arquivos()    # obtém a lista de CSVs de precipitação a processar
    
    # reaproveita a tabela se ela já existir e cobrir todas as coordenadas
    if os.path.exists(TABELA_LOCAIS):  # se o cache já existe
        tabela = pd.read_csv(TABELA_LOCAIS, sep=SEP)  # apenas lê, sem refazer a junção espacial (que é lenta)
    else:                                                        
        tabela = construir_tabela_locais(arquivos)  # constrói a tabela do zero

    for arquivo in arquivos: # percorre cada arquivo de precipitação
        df = pd.read_csv(arquivo, sep=SEP)  # lê o arquivo completo
        df = df.merge(tabela, on=[COL_LAT, COL_LON], how="left") # anexa município/estado/uf/região usando lat e lon como chave

        saida = arquivo.replace(".csv", "_com_local.csv") # define o nome do arquivo de saída (ex.: precipitacao_2006_com_local.csv)
        df.to_csv(saida, sep=SEP, index=False) # grava o resultado sem a coluna de índice

        vazios = df["estado"].isna().sum()  # conta quantas linhas ficaram sem estado
        print(f"{os.path.basename(arquivo)} -> {os.path.basename(saida)} | linhas sem estado: {vazios}")  # relata o arquivo de entrada, o de saída e as falhas


if __name__ == "__main__":                                          
    gerar_csvs() 