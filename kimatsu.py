import tabula
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import sys, os
import json
import tabulate


src_code = "./config.json"
with open(src_code, 'r') as f:
    s = f.read()
USERNAME, PASSWORD, MATRIXCODE = json.loads(s).values()

# マトリックスコードの 　index から値への対応
def idx2code(alphabet: str, number: int) -> str:
    r = number-1
    c = "ABCDEFGHIJ".index(alphabet)
    return MATRIXCODE[7*c + r]

def get_pdf():
    url = "https://www.titech.ac.jp/student/students/life/undergraduate-exam"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    url_pdf = "https://www.titech.ac.jp" + soup.select("#mainIn > div.section.spSection01 > ul > li:nth-child(2) > a")[0].attrs["href"]
    pdf_data = requests.get(url_pdf)
    if not os.path.exists("./pdf"):
        os.mkdir("./pdf")
    with open("./pdf/timetable.pdf", "wb") as f:
        f.write(pdf_data.content)

# 期末試験時間割のPDFへのパスを受け取り, DataFrame に変換したものを返す
def pdf2pandas(src: str) -> pd.DataFrame:
    # tabula で読み取り　　この時点ではページごとに異なる　DataFrame のリストになっている
    data = tabula.read_pdf(src, pages='all', guess=True, lattice=True, force_subprocess=True)

    # ラベルを取得 英語名はいらないので落とす
    label = list(map(lambda s: re.sub(
        r'[\n\r].*', '', s), data[0].columns.to_list()))
    
    # ラベルを統一してDFを結合
    for i in range(len(data)):
        data[i].loc[data[i].shape[0]] = data[i].columns.to_list()
        data[i].columns = label
    data = pd.concat(data)

    # 科目が何百番台かの識別 特に使わなそうなのでコメントアウト
    # data['番台'] = data.loc[:, '科目コード'].map(lambda x: x[5])
    
    # クソコード書いてごめん
    for i in range(data.shape[1]):
        data.iloc[:, i] = data.iloc[:, i].map(lambda s: re.sub(
            r'[\n\r]', ' ', s) if type(s) == str else '')
        
    # index ぐちゃぐちゃなので振り直し
    data = data.reset_index(drop=True)

    # ラベルが重複して入ってるので落とす
    data = data.drop(data[data.loc[:, '日付'] == '日付 Date'].index)

    # 日本語名に続いて英語名が書いてあるので落とす
    for c in ["区分", "科目名"]:
        data[c] = data[c].map(lambda s: re.sub(r"\s.*", "", s))

    return data
    # data.to_csv("./src/res.csv", index=False)


def get_class():
    # セッションを開始
    session = requests.session()

    url = "https://portal.nap.gsic.titech.ac.jp/GetAccess/Login?Template=userpass_key&AUTHMETHOD=UserPassword"
    response = session.get(url)
    # print(response.status_code)

    url2 = "https://portal.nap.gsic.titech.ac.jp/GetAccess/Login"

    # BeautifulSoupを用いて、必要なパラメーターを抽出
    soup = BeautifulSoup(response.text, "html.parser")
    csrfformtoken = soup.find("input", {"name": "CSRFFormToken"}).get("value")
    pageGenTime = soup.find("input", {"name": "pageGenTime"}).get("value")
    locale = soup.find("input", {"name": "LOCALE"}).get("value")
    hiddenuri = soup.find("input", {"name": "HiddenURI"}).get("value")

    # POSTリクエストのパラメーターをセット
    payload = {
        "usr_name": USERNAME,
        "usr_password": PASSWORD,
        "LOCALE": locale,
        "CSRFFormToken": csrfformtoken,
        "pageGenTime": pageGenTime,
        "HiddenURI": hiddenuri,
        "AUTHMETHOD": "UserPassword",
        "AUTHTYPE": "",
        "Template": "userpass_key",
        "OK": "    OK    ",
    }

    # Headerをセット
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://portal.nap.gsic.titech.ac.jp/GetAccess/Login?Template=okutama&AUTHMETHOD=CERTIFICATE&LOCALE=ja_JP&RESOURCE=Portal&GAURI=https%3A%2F%2Fportal.nap.gsic.titech.ac.jp%2FGetAccess%2FResourceList&PAGE=main.jsp%3FresourceKey%3DPortal&GASF=CERTIFICATE%2CIG.GRID%2CIG.TOKENRO%2CIG.OTP&PageDir=",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Cookie は 自動でセットされる
    response = session.post(
        url2, data=payload, headers=headers, allow_redirects=True)

    # 帰ってきたHTMLを保存
    # with open("portal.html", "w") as f:
    #     f.write(response.text)

    url3 = "https://portal.nap.gsic.titech.ac.jp/GetAccess/Login"

    soup = BeautifulSoup(response.text, "html.parser")
    message0 = soup.find("input", {"name": "message0"}).get("value")
    pamsession = soup.find("input", {"name": "PAMSESSION"}).get("value")
    garesourceid = soup.find("input", {"name": "GARESOURCEID"}).get("value")
    pageGenTime = soup.find("input", {"name": "pageGenTime"}).get("value")
    id_reference = soup.find("input", {"name": "ID_REFERENCE"}).get("value")
    hiddenuri = soup.find("input", {"name": "HiddenURI"}).get("value")
    locale = soup.find("input", {"name": "LOCALE"}).get("value")
    csrfformtoken = soup.find("input", {"name": "CSRFFormToken"}).get("value")

    # パラメータをセット
    payload = {
        "message0": message0,
        "message3": " ",
        "message4": "GridAuthOption",
        "OK": "    OK    ",
        "AUTHTYPE": "",
        "ContinueAuth": "true",
        "AUTHMETHOD": "IG",
        "PAMSESSION": pamsession,
        "GARESOURCEID": garesourceid,
        "pageGenTime": pageGenTime,
        "ID_REFERENCE": id_reference,
        "HiddenURI": hiddenuri,
        "Template": "idg_key",
        "GASF": "CERTIFICATE,IG.GRID,IG.TOKENRO,IG.OTP",
        "LOCALE": locale,
        "Responses": "5",
        "CSRFFormToken": csrfformtoken,
    }

    # ログイン情報を送信
    response = session.post(url3, data=payload, headers=headers)
    # print(response.status_code)
    # with open("portal.html", "w") as f:
    #     f.write(response.text)

    url4 = "https://portal.nap.gsic.titech.ac.jp/GetAccess/Login"

    soup = BeautifulSoup(response.text, "html.parser")
    message0 = soup.find("input", {"name": "message0"}).get("value")
    pamsession = soup.find("input", {"name": "PAMSESSION"}).get("value")
    garesourceid = soup.find("input", {"name": "GARESOURCEID"}).get("value")
    pageGenTime = soup.find("input", {"name": "pageGenTime"}).get("value")
    id_reference = soup.find("input", {"name": "ID_REFERENCE"}).get("value")
    hiddenuri = soup.find("input", {"name": "HiddenURI"}).get("value")
    locale = soup.find("input", {"name": "LOCALE"}).get("value")
    csrfformtoken = soup.find("input", {"name": "CSRFFormToken"}).get("value")

    code = [(e.string[1], int(e.string[3])) for e in soup.find_all(
        "th", {"align": "left"}, string=re.compile(r'\[[A-Z],[1-7]\]'))]

    message3 = idx2code(code[0][0], code[0][1])
    message4 = idx2code(code[1][0], code[1][1])
    message5 = idx2code(code[2][0], code[2][1])

    # パラメータをセット
    payload = {
        "message0": message0,
        "message3": message3,
        "message4": message4,
        "message5": message5,
        "message6": "NoOtherIGAuthOption",
        "OK": "    OK    ",
        "AUTHTYPE": "",
        "ContinueAuth": "true",
        "AUTHMETHOD": "IG",
        "PAMSESSION": pamsession,
        "GARESOURCEID": garesourceid,
        "pageGenTime": pageGenTime,
        "ID_REFERENCE": id_reference,
        "HiddenURI": hiddenuri,
        "Template": "idg_key",
        "GASF": "CERTIFICATE,IG.GRID,IG.TOKENRO,IG.OTP",
        "LOCALE": locale,
        "Responses": "7",
        "CSRFFormToken": csrfformtoken,
    }

    # ログイン情報を送信
    response = session.post(url4, data=payload, headers=headers)

    # print(response.status_code)
    # with open("portal.html", "w") as f:
    #     f.write(response.text)

    url5 = "https://kyomu0.gakumu.titech.ac.jp/Titech/Default.aspx"
    response = session.get(url5, headers=headers)
    # print(response.status_code)

    url6 = "https://kyomu0.gakumu.titech.ac.jp/Titech/Student/%E7%A7%91%E7%9B%AE%E7%94%B3%E5%91%8A/PID1_1.aspx"
    response = session.get(url6, headers=headers)
    # print(response.status_code)

    # with open("kyomu.html", 'w') as f:
    #     f.write(response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    res = [e.string.strip() for e in soup.find_all("td", {"align": "left"})]

    return res

get_pdf()
data = pdf2pandas("./pdf/timetable.pdf")
class_info = get_class()

res = data[data["科目コード"].isin(class_info)]

# print(res.to_csv(index=False))

print(tabulate.tabulate(res, headers=res.columns.to_list(),
      showindex=False, tablefmt="github"))
