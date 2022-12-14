import datetime
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

def yield_curve(maxdate):
    r = requests.get(f"https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-taxas-referenciais-bmf-ptBR.asp#")
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find('table', {"id": "tb_principal1"})

    data = str(soup.find('input'))
    data = data.split(sep='"')[7]
    data = datetime.datetime.strptime(data, '%Y%m%d').strftime('%Y-%m-%d')

    rows = table.find_all('td')
    rows = [i.string for i in rows]

    vertices = []
    di_252 = []
    di_360 = []

    x = 1
    for i in rows:
        if x == 1:
            vertices.append(i)
            x = 2
        elif x == 2:
            di_252.append(i)
            x = 3
        elif x == 3:
            di_360.append(i)
            x = 1

    df = pd.DataFrame(columns=['Vertices', 'Di 252', 'Di 360'])
    df['Vertices'] = vertices
    df['Di 252'] = di_252
    df['Di 360'] = di_360

    df['Di 252'] = df['Di 252'].replace(',', '.', regex=True)
    df['Di 360'] = df['Di 360'].replace(',', '.', regex=True)

    df['Vertices'] = df.apply(lambda x: int(x['Vertices']), axis=1)
    df['Di 252'] = df.apply(lambda x: float(x['Di 252']), axis=1)
    df['Di 360'] = df.apply(lambda x: float(x['Di 360']), axis=1)

    vertices_interpolados = []
    taxas_interpoladas_252 = []
    taxas_interpoladas_360 = []

    for i in range(1,maxdate):
        if i not in df['Vertices'].values:
            arr = df['Vertices'].tolist()
            abaixo = arr[np.searchsorted(arr, i, 'left') - 1]
            acima = arr[np.searchsorted(arr, i, 'right')]
            taxa_abaixo = df[df['Vertices'] == abaixo]['Di 252'].values[0]
            taxa_acima = df[df['Vertices'] == acima]['Di 252'].values[0]

            dados_252 = [[abaixo, taxa_abaixo], [acima, taxa_acima]]
            v = linear_interpolation(dados_252, i)

            taxa_abaixo = df[df['Vertices'] == abaixo]['Di 252'].values[0]
            taxa_acima = df[df['Vertices'] == acima]['Di 252'].values[0]

            dados_360 = [[abaixo, taxa_abaixo], [acima, taxa_acima]]
            x = linear_interpolation(dados_360, i)

            vertices_interpolados.append(i)
            taxas_interpoladas_252.append(v)
            taxas_interpoladas_360.append(x)
        else:
            pass

    df_interpolados = pd.DataFrame(columns=['Vertices', 'Di 252', 'Di 360'])
    df_interpolados['Vertices'] = vertices_interpolados
    df_interpolados['Di 252'] = taxas_interpoladas_252
    df_interpolados['Di 360'] = taxas_interpoladas_360
    
    frames = [df, df_interpolados]
    result = pd.concat(frames)
    result = result.sort_values(by=['Vertices'])

    return result

def linear_interpolation(d, x):
    output = d[0][1] + (x - d[0][0]) * ((d[1][1] - d[0][1]) / (d[1][0] - d[0][0]))

    return output

max_days = 2520

df = yield_curve(max_days)
df = df[df['Vertices'] <= max_days] #Vertices até 10 anos
df['Di 252'] = df.apply(lambda x: round(x['Di 252'],2), axis=1)
df['Di 360'] = df.apply(lambda x: round(x['Di 360'],2), axis=1)

print(df)

data = datetime.datetime.now().strftime('%Y%m%d')

#Altere o output para a pasta de sua preferência
output = "C:\Temp"

df.to_csv(f"{output}/Curva_DI_{data}.csv",index=False,sep=";",decimal=",")