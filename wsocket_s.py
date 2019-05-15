#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
# "sentdex"'s video - server.py
# az odoo.sh-ban működik; Colab-ban nem!
import sys
import socket
import asyncio
from pyppeteer import launch, connect, page

IP = "127.0.0.1"
PORT = 50416#1234

linux = sys.platform.startswith("linux")
logged_in = False
first_run = True
ws_endp = ''
page = None

async def browser_close():
    browser = await connect(options={'browserWSEndpoint': ws_endp})  # csatlakozik a meglévőhöz
    await browser.close()

async def main(part_number):
    global first_run, ws_endp, linux
    if first_run:
        if linux:
          browser = await launch(options={'autoClose': False})  # megnyit egy headless chromiumot és nem zárja be! (7 process marad)
        else:
          browser = await launch(options={'autoClose': False, 'executablePath': r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'})
        ws_endp = browser.wsEndpoint  # websocket
        #page = await browser.newPage()  # új oldal létrehozása a browserben
        first_run = False
    else:
        browser = await connect(options={'browserWSEndpoint': ws_endp})  # csatlakozik a meglévő chromiumhoz

    page = await browser.newPage()  # új oldal létrehozása a browserben
    """ DE NEEEM új fül (tab), ahogy eleinte gondoltam, hanem abban új LAP!!! (browser == tab)
    - az első Page már a launch()-ban létrejön. Használhatnánk azt is végig!? """
    pages = await browser.pages()
    print(pages, len(pages))
    if len(pages) > 4:
        await pages[3].close()  # Opció: runBeforeUnload (bool): Defaults to False.

    #await page.goto('https://mall.industry.siemens.com/mall/en/hu/Catalog/Product/5SY5114-7')
    url = 'https://mall.industry.siemens.com/mall/en/hu/Catalog/Product/'+part_number
    await page.goto(url)
    #await page.goto('https://signin.siemens.com/regpublic/login.aspx?lang=en&app=MALL&ret=https%3a%2f%2fmall.industry.siemens.com%2fmall%2fen%2fhu%2fCatalog%2fProduct%2f'+part_number)
    """ Magyarázat a hosszú sorhoz:
    - csak akkor jut a termékhez, ha be vagyunk jelentkezve; egyébként először a Login oldalra visz, majd azután ide! 
    - ha az oldalon van 'Login' elem, akkor újból be kell jelentkeznünk, mert kilépett egy bizonyos idő után.
    - tehát munka közben először a rövid url-lel kell próbálkozni. Ha van 'login' elem, akkor megismételni ezzel.
    - ez a hosszú link ugyanaz, mintha a '>Login'-ra kattintanánk!
    - ha nem ugyanez az URL van a címsorban, akkor hibás adat miatt a keresőbe jutott: KILÉPNI!!!
    """
    #await asyncio.sleep(3)
    if page.url != url:
        return "-ERROR-"
        
    element = await page.querySelector(".internalLink.whiteLink.hoverInfoPopup")  # = Register now!
    #await page.screenshot({'path': 'xample.png'})
    if element != None:
        print('Logging in...')  # sys.stderr.write() csak kilépéskor írja ki a végén!!!
        
        await page.goto('https://signin.siemens.com/regpublic/login.aspx?lang=en&app=MALL&ret=https%3a%2f%2fmall.industry.siemens.com%2fmall%2fen%2fhu%2fCatalog%2fProduct%2f'+part_number)
        # ----------------
        await page.type('#ContentPlaceHolder1_TextSiemensLogin', 'mezei.zoltan') # id
        await page.type('#ContentPlaceHolder1_TextPassword', 'Gyoga2012')

        await page.click('#ContentPlaceHolder1_LoginUserNamePasswordButton')

        await page.waitForNavigation()
    
    #await page.screenshot({'path': 'xample2.png'})
    element = await page.querySelector(".LoginCompanyName.hoverInfoPopup")	# $() helyett!
    text = await page.evaluate('(element) => element.textContent', element)
    print('s:User:', text.strip()[1:8])  # Sonepar
    #await page.screenshot({'path': 'example.png'})

    #await page.waitForSelector(".greenCheck")
    # 2 féle eredmény is előfordulhat: class="warningTriangle" és ".greenCheck", ezért ez kell:
    await page.waitForXPath('//*[@id="atpresulttext"]/text()') # a sleep(3) helyett, kb. 2 sec! (id nem jó, csak class!!!)
    #await page.screenshot({'path': 'xample.png'})

    element = await page.querySelector("#atpresulttext")
    rtext = await page.evaluate('(element) => element.textContent', element)
    #await page.screenshot({'path': 'xample.png'})
    #print('\n', part_number.strip(), ':', rtext)
    return rtext

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # enélkül legközelebb: OSError: [Errno 98] Address already in use
server_socket.bind((IP, PORT))
server_socket.listen()  #5

while True:
    client_socket, client_address = server_socket.accept()
    print(f"s:Connection from {client_address} has been established!")
    
    request = client_socket.recv(64)
    print('s:Request:', request)  # sys.stderr.write()
    
    if request == b'q':  # = quit
        asyncio.get_event_loop().run_until_complete(browser_close())
        client_socket.send(bytes("Server closed!", "utf-8"))
        client_socket.close()
        server_socket.close()
        sys.exit()
    elif request == b'l':  # = login
        if logged_in == False:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(main('5SY5114-7'))
            #loop.close()
            client_socket.send(bytes("Welcome to the server!", "utf-8"))
            logged_in = True
        else:
            client_socket.send(bytes("Server is already running!", "utf-8"))
    else:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(main(request.decode("utf-8")))
        #loop.close()
        """ készlet adat átadása """
        client_socket.send(bytes(result, "utf-8"))
    client_socket.close()
    