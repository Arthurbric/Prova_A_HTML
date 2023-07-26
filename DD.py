import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pyautogui
import random
from time import sleep
from bs4 import BeautifulSoup
import os
os.environ['PATH'] += ":/content/geckodriver"

def coletar_dados(cnpj, data):
    ops = Options()
    ops.add_argument("start-maximized")
    ops.add_argument('window-size=1920x1080')
    user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
    ops.add_argument(f'--user-agent={user_agent}')
    browser = webdriver.Firefox(service=Service(), options=ops)
    pyautogui.PAUSE = 0.4
    # pyautogui.click(907,1052,2)

    pyautogui.moveTo(960 + random.randint(-200, 200), 540 + random.randint(-200, 200), 2)

    browser.get('https://grpfordam.sefin.fortaleza.ce.gov.br/grpfor/pagesPublic/iptu/damIptu/imprimirDamIptu.seam')
    sleep(2.5)

    pyautogui.moveTo(127, 505 + random.randint(-3, 3), 2, pyautogui.easeInOutQuad)
    pyautogui.click(127, 505 + random.randint(-3, 3), 1)

    pyautogui.moveTo(226, 505 + random.randint(-4, 4), 2 + random.randint(-1, 1), pyautogui.easeInOutQuad)
    pyautogui.click(226, 505 + random.randint(-4, 4), 1)

    pyautogui.write(cnpj)

    pyautogui.moveTo(382, 505 + random.randint(-4, 4), 2 + random.randint(-1, 1), pyautogui.easeInOutQuad)
    pyautogui.click(382, 505 + random.randint(-4, 4), 1)

    pyautogui.write(data)

    pyautogui.moveTo(530, 505 + random.randint(-5, 5), 2 + random.randint(-1, 1), pyautogui.easeInOutQuad)
    pyautogui.click(530, 505 + random.randint(-5, 5), 1)
    sleep(2.5)

    return browser

def coletarDadosPagina(cnpj, data, timeout):
  if timeout == 0:
    return None

  browser = coletar_dados(cnpj, data)
  result = browser.page_source

  site = BeautifulSoup(result, 'html.parser')

  alerta = site.find('dt', attrs={'class':'alert alert-danger'})
  if alerta:
    mensagem = alerta.find('span', attrs={'class':'rich-messages-label'})
    if "robô" in mensagem.text:
      sleep(2)
      browser.quit()
      coletarDadosPagina(cnpj, data, timeout - 1)
    else:
      return browser
  else:
    return browser


def coletarDadosImovel(cnpj, data, timeout):
    result = coletarDadosPagina(cnpj, data, timeout)
    if result == None:
        return [0, cnpj, data]

    browser = result

    lista_imoveis = []
    site = BeautifulSoup(browser.page_source, 'html.parser')

    dados_imovel_unico = site.find('span', attrs={'id': 'pmfInclude:cadastroForm:dadosImovel'})
    tabela = site.find('table', attrs={'id': 'pmfInclude:cadastroForm:dataTable'})
    if tabela:
        alteracao = True
        while alteracao:
            imoveis = site.find_all('tr', attrs={'class': 'rich-table-row'})

            for imovel in imoveis:
                dados_imovel_tds = imovel.find_all('td')

                lista_imovel = []
                for dados_imovel_td in dados_imovel_tds[0:4]:
                    lista_imovel.append(dados_imovel_td.text)

                lista_imoveis.append(lista_imovel)

            botao_bs = site.find_all('td', attrs={'class': 'rich-datascr-button'})
            if botao_bs:
                if botao_bs[3]['class'][0] != 'rich-datascr-button-dsbld':
                    textoOnClick = "Event.fire(this, 'rich:datascroller:onscroll', {'page': 'next'});"
                    botao = browser.find_element(By.XPATH, f'//td[@onclick="{textoOnClick}"]')
                    botao.click()
                    sleep(2)
                    site = BeautifulSoup(browser.page_source, 'html.parser')
                else:
                    alteracao = False
            else:
                alteracao = False
        sleep(2)
        browser.quit()
        return lista_imoveis
    elif dados_imovel_unico:
        dados_imovel_unico_fieldset = dados_imovel_unico.find('fieldset')
        dados_imovel_unico_tds = dados_imovel_unico_fieldset.find_all('td')
        lista_imovel_unico = [2]
        for dados_imovel_unico_td in dados_imovel_unico_tds[2::3]:
            lista_imovel_unico.append(dados_imovel_unico_td.text)

        sleep(2)
        browser.quit()
        return lista_imovel_unico
    else:
        mensagem_texto = ''
        alerta = site.find('dt', attrs={'class': 'alert alert-danger'})
        if alerta:
            mensagem = alerta.find('span', attrs={'class': 'rich-messages-label'})
            mensagem_texto = mensagem.text

        sleep(2)
        browser.quit()
        return [1, cnpj, data, mensagem_texto]

lista_imovel = coletarDadosImovel('12279725000140', '04111987', 1)
print(lista_imovel)

import pandas as pd
df = pd.read_excel('lista_fortaleza.xlsx')

lista_nomes = ['Pessoa Jurídica', 'Data Abertura RFB', 'Inscrição', 'Cartografia', 'Endereço de Localização', 'Correspondência', 'Proprietário/Adquirente/Titular']
#lista_nomes = ['Pessoa Jurídica', 'Data Abertura RFB', 'Inscrição', 'Endereço', 'Cartografia', 'Titular']
lista_cnpjs = []
lista_data_abertura = []
lista_inscricao = []
lista_cartografia = []
lista_endereco = []
lista_correspondencia = []
lista_titular = []

cadastro_nao_encontrado = []


def loop_imoveis(index):
    lista_imoveis = coletarDadosImovel(df.loc[index, 'Pessoa Jurídica'], df.loc[index, 'Data Abertura RFB'], 2)
    if not isinstance(lista_imoveis[0], list):
      lista_imovel = lista_imoveis
      if lista_imovel[0] == 0:
        print(f'Index[{index}],Lista{lista_imovel[1:3]}, Erro no Captcha')
        sleep(120)
        loop_imoveis(index)
      elif lista_imovel[0] == 1:
        print(f'Index[{index}],Lista{lista_imovel[1:4]}')
        cadastro_nao_encontrado.append(lista_imovel[1:4])
      else:
        print(f'Index[{index}]')
        lista_cnpjs.append(df.loc[index, 'Pessoa Jurídica'])
        lista_data_abertura.append(df.loc[index, 'Data Abertura RFB'])
        lista_inscricao.append(lista_imovel[1])
        lista_cartografia.append(lista_imovel[2])
        lista_endereco.append(lista_imovel[3])
        lista_correspondencia.append(lista_imovel[4])
        lista_titular.append(lista_imovel[5])
    else:
      print(f'Index[{index}], Imóveis[{len(lista_imoveis)}]')
      for lista_imovel in lista_imoveis:
        lista_cnpjs.append(df.loc[index, 'Pessoa Jurídica'])
        lista_data_abertura.append(df.loc[index, 'Data Abertura RFB'])
        lista_inscricao.append(lista_imovel[0])
        lista_endereco.append(lista_imovel[1])
        lista_cartografia.append(lista_imovel[2])
        lista_titular.append(lista_imovel[3])
        lista_correspondencia.append('')

for index in range (67413,67501): #(0,67413)(67413,134825)//len -> 134824
        loop_imoveis(index)

preparacao_df_imoveis = list(zip(lista_cnpjs, lista_data_abertura, lista_inscricao, lista_cartografia,
                                 lista_endereco, lista_correspondencia, lista_titular))
df_imoveis = pd.DataFrame(preparacao_df_imoveis, columns = lista_nomes)
df_cadastro_nao_encontrado = pd.DataFrame(cadastro_nao_encontrado, columns = ['Pessoa Jurídica', 'Data Abertura RFB', 'Mensagem Erro'])

df_imoveis.to_excel('dados_imoveis_67501.xlsx', index=False)
df_cadastro_nao_encontrado.to_excel(f'dados_cadastro_nao_encontrado_{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.xlsx', index=False)

ops = Options()
ops.add_argument("start-maximized")
ops.add_argument('window-size=1920x1080')

cnpj = '12279725000140'
data = '04111987'

browser = webdriver.Firefox(service=Service(), options=ops)
clique = random.randint(-5,5)

#pyautogui.click(907,1052,2)

pyautogui.moveTo(960+random.randint(-200,200),540+random.randint(-200,200),2)

browser.get('https://grpfordam.sefin.fortaleza.ce.gov.br/grpfor/pagesPublic/iptu/damIptu/imprimirDamIptu.seam')
sleep(5)

pyautogui.moveTo(127,505+random.randint(-3,3),3, pyautogui.easeInOutQuad)
pyautogui.click(127,505+random.randint(-3,3),1)
sleep(1)
pyautogui.moveTo(226,505+random.randint(-4,4),2+random.randint(-1,1), pyautogui.easeInOutQuad)
pyautogui.click(226,505+random.randint(-4,4),1)
sleep(1)
pyautogui.write(cnpj)
sleep(1)
pyautogui.moveTo(382,505+random.randint(-4,4),2+random.randint(-1,1), pyautogui.easeInOutQuad)
pyautogui.click(382,505+random.randint(-4,4),1)
sleep(1)
pyautogui.write(data)
sleep(1)
pyautogui.moveTo(530,505+random.randint(-5,5),2+random.randint(-1,1), pyautogui.easeInOutQuad)
pyautogui.click(530,505+random.randint(-5,5),1)
sleep(5)

delay = random.randint(2,8)
browser.get('https://grpfordam.sefin.fortaleza.ce.gov.br/grpfor/pagesPublic/iptu/damIptu/imprimirDamIptu.seam')
sleep(4)

pyautogui.size()
pyautogui.position()

radioButtom = browser.find_element(By.ID, 'pmfInclude:cadastroForm:tipoDecorate:j_id334:1')
radioButtom.click()
sleep(delay)

elemento1 = browser.find_element(By.ID, 'pmfInclude:cadastroForm:cpfDec:cnpj')
elemento1.click()
elemento1.send_keys(cnpj)

elemento2 = browser.find_element(By.ID, 'pmfInclude:cadastroForm:dataNascimentolDec:dataNascimentoInputDate')
elemento2.click()
elemento2.send_keys(data)

buttomPesquisar = browser.find_element(By.ID, 'pmfInclude:cadastroForm:dataNascimentolDec:botaoRecuperarImovelNaoLogado') #para elementos
sleep(6)
buttomPesquisar.click()
sleep(6)


browser.quit()
print(lista_cnpjs)

"""

def dados(DATE,CNPG):
    # Para ENcontrar a possiçao Point(x=153, y=585)
    sleep(1.5)
    pyautogui.click(152, 585, clicks=1, interval=3, button='left')

    # possiçao --> CNPJ  Point(x=305, y=585)
    pyautogui.click(305, 585, clicks=1, interval=1, button='left')
    pyautogui.write(str(CNPG))
    # pyautogui.write("23.542.756/0001-68")

    # possiçao --> Data  Point(x=500, y=585)
    pyautogui.click(500, 585, clicks=1, interval=1, button='left')
    pyautogui.write(str(DATE))
    # pyautogui.write("25/10/1988")

    # possiçao --> Data  Point(x=670, y=585)
    pyautogui.click(670, 585, clicks=1, interval=2, button='left')

cnpj = "23.542.756/0001-68"
date = "25/10/1988"

dados(date,cnpj)
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⡟⣯⡿⣝⣯⠿⣽⢯⣟⡿⣻⣟⣿⣿⣿⢿⣿⣿⣿⣿⣻⣿⣶⣾⣷⣬⡁⠈⢀⣀⣵⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡰⢌
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⢯⣽⢯⣟⢾⣵⣻⡽⣾⡽⣽⣳⢯⣟⣿⣿⣯⣿⢾⣿⣿⣟⡾⣯⢿⣿⣿⣿⣷⣤⣿⡇⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠠⠁⠊⠀⠁⠀⠀⠀⠀⠀⠂⠘⠂
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣏⣿⢯⣿⢾⣟⡾⣳⣟⣳⣟⡷⣯⣟⣾⣿⣿⣿⢾⣿⣟⡾⣿⣿⣽⣿⣿⣏⣿⣿⣿⣿⣷⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⡳⣞⣿⣿⡯⣿⢾⣽⣳⢯⡷⣯⣟⣷⣻⣽⣿⣿⣿⣿⡽⣯⣿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⢀⣀⣄⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⢯⣗⣻⣿⣟⡾⣽⢿⣛⣾⡽⣯⢟⣷⣻⢾⣽⣿⣿⣞⣯⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⣀⣀⣠⣶⠿⣻⠿⠛⢹⣿⢿⠟⠛⠉⠐⣌⢻⡀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡿⣝⣾⣿⡟⣼⣻⣏⣿⣹⢺⣟⣵⣫⣶⡿⣾⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡄⢀⣠⣴⡾⢋⣽⣿⣯⣿⠋⡔⠉⣼⣿⠇⠀⠀⠀⠣⢌⣻⠇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡿⣽⣿⣟⢾⣿⡵⣯⢾⣱⣯⣿⣷⢯⣷⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⣿⣿⣿⣿⣷⣾⣿⣿⣿⣴⣿⣿⣿⣿⠃⢌⠀⢰⣿⡏⠀⠀⠀⠀⠱⢨⠼⡇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣻⣿⣿⣯⢿⣿⣟⣯⣿⣯⣿⣿⣿⣯⣿⣟⣿⣿⣳⣿⣿⣿⣈⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢳⣿⢣⠘⣀⡞⢸⣿⠁⠀⠀⠀⠀⢀⠃⢾⠁⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣻⣽⣿⣿⣯⢿⣿⣻⣾⢿⣿⣽⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣭⣴⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣧⣿⢋⢆⠃⣾⠀⣸⡟⠀⠀⠀⠀⠀⠀⠎⡽⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣾⡟⣽⣿⣿⣿⣯⣿⣿⣏⣿⣿⢿⣿⣧⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⡟⢯⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⡿⢿⡿⢣⢍⣢⣭⡇⢀⣿⢃⠀⠀⠀⠀⠀⢈⢒⡇⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣼⡟⢰⣿⢾⣿⣯⣷⣿⣿⣿⣞⣿⣿⣿⣿⣦⣛⢿⣿⣿⣿⣿⣿⣿⣽⠏⠉⠗⣚⣩⣾⠟⣭⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣗⣿⣿⣿⣿⣷⣿⡏⢠⠃⢸⡟⠰⠀⠀⠀⠀⠀⢌⣺⠁⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢰⡿⠀⣾⡏⣿⣿⡷⣿⣿⣿⣿⣧⣧⣼⣿⣿⣿⣿⣶⡹⢿⣿⣿⣿⣿⡸⢄⠉⠉⡙⣉⠡⣚⣵⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⣿⣿⣇⡞⠀⣼⠁⠁⠀⠀⠀⠀⠈⡴⡇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⠁⢸⡟⠀⣿⣯⣿⣿⣿⣿⣿⣿⣿⣿⣟⠻⢾⣫⣼⠗⠀⠙⢟⡻⣿⣷⡂⠀⠀⠐⠀⠂⢡⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⣿⣿⣿⠃⣿⣿⠟⠀⢠⡇⠀⠀⠀⠀⠀⠀⣘⡾⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⡇⢀⣿⠁⠀⣿⣿⣳⣿⣿⣿⣿⣿⣿⣿⣬⠉⡒⠋⠁⠀⠀⠀⣤⠙⠌⠻⢆⡀⠀⠀⢀⣰⡿⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⠋⠀⠀⣸⠁⠀⠀⠀⠀⠀⠐⣼⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⢀⣾⠏⠀⢰⡿⣿⣳⣿⣿⣿⣿⣿⣿⣿⣿⣷⣌⢡⣁⡀⠀⠀⠈⠁⠀⠀⠀⠀⠀⠀⠤⠚⢱⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⣸⠇⠀⠀⢠⠇⠀⠀⠀⠀⠀⢀⣹⡏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣾⠟⠀⢀⣾⣟⣿⣟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡻⢎⣀⣀⠄⠀⠀⣤⣠⣤⡀⠀⠀⠀⣠⡿⣿⣿⣿⣿⣿⡟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢟⠏⠀⠀⢠⠏⠀⠀⠀⠀⠀⠠⣜⡾⣷⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢠⣟⡞⠀⠀⣼⣿⣞⡿⣾⣿⣾⢿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣄⣀⠀⠀⠀⠀⠉⠉⠀⠀⢀⡼⢏⣵⣿⣿⣿⡟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠣⠋⠀⢀⣴⠏⠀⡄⠀⠀⠀⣀⢳⡞⠀⢿⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣟⣷⣇⢀⣼⠏⢸⢾⡿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⣿⡲⢤⣄⣀⣠⠖⣏⣱⣾⣿⣿⣿⣿⠇⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠉⠓⢶⣾⠟⠁⠀⡜⠀⠀⠀⡰⣬⠟⠀⠀⠘⣧⠀⠀⠀⠀⠀⠀
⠀⢠⣾⡳⠋⢸⢾⡾⡟⠀⣾⣿⣟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢷⣃⢎⠲⣁⠏⣴⣿⡿⢻⢽⣿⣿⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⢃⠈⣆⠀⠀⠀⣠⠞⠀⠀⢀⡰⣳⠋⠀⠀⠀⠀⠘⠆⠀⠀⠀⠀⠀
⣰⣻⠞⠀⢀⣼⣿⣿⠀⢰⣟⣾⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢋⡜⣻⣆⠣⠜⡒⢼⡿⣈⠗⣚⣏⠿⣼⣿⡿⣿⣿⣿⢿⣙⢮⡿⠃⠀⠈⠒⠶⠾⠋⠀⠀⢀⢦⡟⠁⠀⠀⠀⠀⠀⠀⠈⢆⠀⠀⠀⠀
⡗⠁⠀⣠⡾⢃⣽⡾⣧⡾⣽⣯⣿⣿⣿⣿⣿⡿⠻⠿⠿⣿⣿⣿⣿⣿⣿⣯⣇⠎⡴⢡⢎⠳⡜⢺⣄⢛⣦⢙⡴⢪⠜⣆⣛⣷⣿⣿⣟⢣⠎⠻⠁⠀⠀⠀⠀⠀⠀⠀⠀⡄⣯⡞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣧⠀⠀⠀
⠀⢀⣾⢋⣴⠟⠁⠻⣽⡿⣿⣾⣿⣿⡟⠉⠉⢿⣄⠀⡸⠛⢉⠛⣿⣿⣿⣷⣮⣛⠍⠲⢌⠣⡜⡄⠛⡷⢏⠲⡌⣧⣻⠞⣋⢶⣿⣿⣏⠆⠁⠀⠀⠀⠀⠀⠀⠀⠀⡄⣳⣾⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡄⠀⠀
⣴⣿⣵⠟⠁⠀⢀⣼⣿⣿⢷⣿⣿⡟⠀⠀⠀⠀⠙⣏⠀⠁⢢⡀⠸⣿⣿⣿⣿⠿⣿⣷⡾⠶⢶⣌⢓⡰⢊⣕⡾⢛⠤⡙⡔⢺⣿⢿⣿⠀⠀⠀⠀⠀⠀⠀⠀⡄⣣⣼⡏⢽⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣧⠀⠀
⠟⢏⠀⠀⠀⢀⣾⣿⣟⣿⣿⣿⣿⡁⠀⠀⠀⠀⠀⠸⡄⠀⠀⠈⠂⣿⣿⣿⣿⣿⣷⣤⡙⣷⣬⡘⠳⠐⢃⠌⡰⢉⠆⡱⢈⣽⣿⡎⢿⡆⠰⣇⠀⡀⢄⠢⣍⣶⣿⣿⡅⢺⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡿⠀⠀
⠀⠀⠉⠒⢀⡾⠛⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⢱⠀⠀⠀⢠⣿⣿⣿⣇⢻⣿⣿⢿⣾⣿⣷⠀⠁⠂⠌⢀⠁⠂⠁⢰⣿⣿⣷⡈⢻⡄⢹⡖⣈⠦⡿⣾⣿⣿⣿⣿⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣟⠀⠀
⡰⢪⡕⡴⠃⢠⣾⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠈⢿⣄⡀⣼⣿⠟⣹⠇⠀⢿⣿⠀⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀⠘⠆⣻⣿⣿⣦⣽⣾⣧⣝⣾⣷⢻⣿⣿⣿⣿⣷⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠇⠀⠀
⢡⣣⠞⠀⣰⣿⣿⢋⣿⣿⣿⣿⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣷⡿⠟⠊⠁⠀⣠⣿⣏⣾⣿⣾⡿⢿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⢿⣿⣿⡞⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⣠⣾⡿⠀⠀⠀
⠚⠁⠀⢀⣿⣷⠏⣼⣿⣿⣿⣿⣟⠀⠀⠀⠀⠀⠀⢀⣠⣶⢿⡟⠀⠀⢀⠄⢊⣿⣿⣿⣿⠟⠛⠉⠁⠀⠀⠰⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⢿⣿⣿⣷⡀⠀⠀⠀⠀⠒⠛⠛⠁⠀⠀⠀⠀
⠀⠀⢀⣼⣿⣟⣴⣿⣿⣿⣿⣿⡏⠀⠀⠀⣀⣤⣾⣿⠟⣉⢾⠇⠀⠐⣁⢶⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠙⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⣿⡆⠈⢻⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⣠⣾⣟⣾⣿⣿⣿⣿⣿⣿⣿⠇⢀⣤⠾⠛⠋⠁⠀⠈⡔⣾⠖⢀⠜⣠⡾⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢙⢄⡀⠻⣿⠙⠳⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀
⡴⣟⡷⣯⣿⢿⣿⣿⡿⣿⣿⣿⡴⠋⠀⠀⠀⠀⠀⠀⠐⣸⡿⠀⠘⡶⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠲⢿⣷⡀⠀⠻⡷⣄⠀⠀⠀⠀⠀⠀
⡸⠋⠉⠙⢣⣿⣿⣿⣇⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⢰⡿⠁⠀⢰⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡝⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡖⣦⡘⣧⡀⠀⠉⢌⠳⡀⠀⠀⠀⠀
⠀⠀⠀⠀⢸⣿⢾⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠘⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⣿⠌⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠓⡛⠁⢣⠀⠀⠀⠡⡘⢆⠀⠀⠀
⣦⣀⣀⣤⢾⣿⣻⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⢸⠇⠀⠀⠀⠀⠀⠀⠀⠀⣠⢴⣲⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢽⡚⡌⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠱⠘⢸⠀⠀⠀⠀⠐⣌⡆⠀⠀
⢿⡟⠏⠻⢿⣷⣻⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠻⠟⠗⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⡝⡔⠁⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⣼⡇⠀⠀⠀⠀⢸⡷⠀⠀
⡏⠀⠀⠀⠀⠙⢿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠠⢁⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢾⡹⢬⡁⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⡇⠀⠀⠀⢀⣾⣿⠀⠀
⢇⡀⠂⠀⠀⠀⠈⠙⠿⣯⠀⠀⠀⠀⠀⠀⢀⠑⡂⣯⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⡘⣽⡝⢦⡃⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣺⣿⣿⣷⣄⠀⢀⣾⣿⡇⠀⠀
⡄⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⣄⠀⠀⠀⠀⠠⢃⡕⢺⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⡑⢼⡟⡼⣩⠿⣦⡡⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠰⣌⣷⣿⣿⣿⣿⣿⣶⣿⣿⣿⠁⠀⠀
⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⡈⢳⡄⠀⢠⠡⢣⠜⣹⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢄⠣⣹⢾⡙⠶⡡⢞⡩⢷⣯⡰⠡⢄⠠⣀⠀⡄⢠⢂⡜⣬⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀
⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⡘⢄⢻⡄⢣⠜⣡⢞⣿⣿⣷⡆⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠘⢤⡷⢏⢧⡙⣣⠕⡪⠜⡡⢞⡹⠿⣮⣵⣦⣹⣬⣷⣾⣾⡙⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀
⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀⠐⡈⢦⡙⢦⡙⢦⣻⢡⣿⣿⣿⣦⣐⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠰⣈⣦⢽⢫⠜⡩⢆⡱⢢⠙⠄⠃⠁⠊⠔⢫⠔⢦⠣⣝⢲⣿⠿⣿⡅⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀
⣿⣿⣿⣇⢤⠀⠀⠀⠀⠀⠀⠀⢈⠒⡜⢦⣹⣳⣿⣿⣿⣿⣿⡿⢠⣷⠶⢤⣤⣀⣀⣀⣄⣠⣤⣬⠶⢓⢋⠆⢣⠊⠌⠑⡀⠂⠁⠈⠀⠀⠀⠀⠈⠐⣊⠦⡙⢦⣿⣿⣨⣿⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀
⣿⣿⣿⣿⣿⣶⢄⡀⠀⠀⠀⠀⠠⢩⢜⣣⢷⢃⣿⣿⣿⣿⣿⣇⣿⣿⣧⠀⠀⠈⠉⠉⠈⠁⠀⠀⠐⠈⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠠⢎⣹⣿⣿⢿⣿⣿⢿⣿⣿⣿⣿⣿⣿⠙⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣧⣿⣦⣿⣥⣤⣀⣀⠂⡇⣞⣼⣿⣿⣿⣿⣿⢿⣿⣿⣿⡿⠛⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠱⣨⡿⢻⣿⣿⠏⠀⣸⣿⣿⣿⣿⣿⡿⠀⣿⢿⣿⣿⣿⣿⣿⣿
⡇⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠙⣾⣾⣿⣯⣿⣿⣿⣏⣼⡿⠛⠙⠁⠀⢹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠱⣿⣿⣿⡿⣏⠀⣰⣿⣿⣿⣿⣿⣿⡇⠀⡿⢸⣿⣿⣿⣿⣿⣟
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⢰⣿⡿⠟⠛⢫⡹⠖⠉⠁⠀⠀⠀⠀⠀⠘⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢻⣿⡿⢻⡇⠉⣹⣿⣿⣿⡟⣿⣿⡿⢀⣼⣡⣿⣿⣿⣿⣿⣿⣯
⡿⢿⠟⣿⣿⣿⣿⣿⣿⣿⡿⠟⢋⣁⡤⠒⣠⠞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢲⣿⣿⡀⠘⢛⣿⣿⣿⣿⡟⢀⣿⣿⣅⣾⣿⣿⣿⣿⣿⣿⣿⣿⣧
⣿⣿⢰⣿⣿⣿⣿⣿⠛⢣⠐⢌⣖⠡⠔⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡰⠂⠀⠀⠀⠀⠀⠀⠀⠀⢨⡟⠙⢿⡿⠿⣻⣿⣿⣿⠟⣠⣿⡿⣻⣿⣿⢟⣋⣱⣿⣿⣿⣿⣿⣿
⣿⢿⢿⣿⣭⡿⠃⠄⠀⡠⠈⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠔⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠀⠀⠀⣹⣾⣿⣿⣿⣿⣾⠿⠋⠀⠹⡸⣏⡉⠉⣿⣿⣿⣿⣿⣿⠋
⡟⠁⢸⡾⠋⠀⢡⡤⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡾⢽⠂⢀⣼⣿⠟⠉⠉⠋⠉⠀⠀⠀⣆⣠⠇⠀⠀⣼⣿⣿⣿⣿⣿⣧⡀
⣇⠀⠋⠀⠀⠀⡺⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡃⢻⡇⢸⣿⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⡿⠏⠉⠉
⣿⡀⠀⠀⠀⠠⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠌⡑⣇⠘⣿⠈⢆⡀⠀⠀⠀⣀⠀⠀⣀⠤⣊⡽⢟⠿⠛⠉⠁⠐⠠⠀⠀
"""