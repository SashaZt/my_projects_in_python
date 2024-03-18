from hmac import new
from operator import ne
from bs4 import BeautifulSoup
import csv
import urllib.parse
import glob
import re
import requests
import json
import os
import time

cookies = {
    'ActiveBasket': '1',
    'dv_consent': '{"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1701526738}',
    'PHPSESSID_MIKE': '0l3vv3p66d8feiupnlbj1i8tef',
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
}


def get_all_brand():
    # urls = [
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Adiva/?ftype=1&type=99&Marke=Adiva&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Adly%2FHerchee/?ftype=1&type=99&Marke=Adly%2FHerchee&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Aeon/?ftype=1&type=99&Marke=Aeon&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/AGM/?ftype=1&type=99&Marke=AGM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Aiyumo/?ftype=1&type=99&Marke=Aiyumo&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/AJP/?ftype=1&type=99&Marke=AJP&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/AJS/?ftype=1&type=99&Marke=AJS&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Alpha+Mobil/?ftype=1&type=99&Marke=Alpha%20Mobil&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Aprilia/?ftype=1&type=99&Marke=Aprilia&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Arctic+Cat%2FTextron/?ftype=1&type=99&Marke=Arctic%20Cat%2FTextron&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Askoll/?ftype=1&type=99&Marke=Askoll&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Atala%2FRizzato/?ftype=1&type=99&Marke=Atala%2FRizzato&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/ATU/?ftype=1&type=99&Marke=ATU&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Azel/?ftype=1&type=99&Marke=Azel&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Bajaj/?ftype=1&type=99&Marke=Bajaj&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Baotian/?ftype=1&type=99&Marke=Baotian&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Beeline/?ftype=1&type=99&Marke=Beeline&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Benelli/?ftype=1&type=99&Marke=Benelli&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Benzhou/?ftype=1&type=99&Marke=Benzhou&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Beta/?ftype=1&type=99&Marke=Beta&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Bimota/?ftype=1&type=99&Marke=Bimota&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/BMW/?ftype=1&type=99&Marke=BMW&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Bombardier/?ftype=1&type=99&Marke=Bombardier&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Brixton/?ftype=1&type=99&Marke=Brixton&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/BSA/?ftype=1&type=99&Marke=BSA&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Buell/?ftype=1&type=99&Marke=Buell&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Buffalo%2FQuelle/?ftype=1&type=99&Marke=Buffalo%2FQuelle&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Cagiva/?ftype=1&type=99&Marke=Cagiva&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/CAN-AM/?ftype=1&type=99&Marke=CAN-AM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/CCF/?ftype=1&type=99&Marke=CCF&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Cectek%2FHerkules/?ftype=1&type=99&Marke=Cectek%2FHerkules&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/CFMOTO/?ftype=1&type=99&Marke=CFMOTO&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/CH+Racing/?ftype=1&type=99&Marke=CH%20Racing&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/China+Motor/?ftype=1&type=99&Marke=China%20Motor&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/CPI/?ftype=1&type=99&Marke=CPI&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/CSR/?ftype=1&type=99&Marke=CSR&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/CZ/?ftype=1&type=99&Marke=CZ&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Daelim/?ftype=1&type=99&Marke=Daelim&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Derbi/?ftype=1&type=99&Marke=Derbi&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Dinli/?ftype=1&type=99&Marke=Dinli&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Ducati/?ftype=1&type=99&Marke=Ducati&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/E-max/?ftype=1&type=99&Marke=E-max&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/E-Ton/?ftype=1&type=99&Marke=E-Ton&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Ecobike/?ftype=1&type=99&Marke=Ecobike&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Ecooter/?ftype=1&type=99&Marke=Ecooter&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Emco/?ftype=1&type=99&Marke=Emco&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Energica/?ftype=1&type=99&Marke=Energica&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Ering/?ftype=1&type=99&Marke=Ering&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Etropolis/?ftype=1&type=99&Marke=Etropolis&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/EVT/?ftype=1&type=99&Marke=EVT&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Explorer/?ftype=1&type=99&Marke=Explorer&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/F.B.Mondial/?ftype=1&type=99&Marke=F.B.Mondial&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Fantic/?ftype=1&type=99&Marke=Fantic&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/FKM/?ftype=1&type=99&Marke=FKM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Flex+Tech/?ftype=1&type=99&Marke=Flex%20Tech&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Gas+Gas/?ftype=1&type=99&Marke=Gas%20Gas&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Generic/?ftype=1&type=99&Marke=Generic&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Giantco/?ftype=1&type=99&Marke=Giantco&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Gilera/?ftype=1&type=99&Marke=Gilera&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Goes/?ftype=1&type=99&Marke=Goes&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Govecs/?ftype=1&type=99&Marke=Govecs&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Harley+Davidson/?ftype=1&type=99&Marke=Harley%20Davidson&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Heinkel/?ftype=1&type=99&Marke=Heinkel&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Hercules/?ftype=1&type=99&Marke=Hercules&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/HM-Moto/?ftype=1&type=99&Marke=HM-Moto&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Honda/?ftype=1&type=99&Marke=Honda&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Horex/?ftype=1&type=99&Marke=Horex&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Huatian%2FLintex/?ftype=1&type=99&Marke=Huatian%2FLintex&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Husaberg/?ftype=1&type=99&Marke=Husaberg&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Husqvarna/?ftype=1&type=99&Marke=Husqvarna&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Hyosung/?ftype=1&type=99&Marke=Hyosung&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Indian/?ftype=1&type=99&Marke=Indian&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Innoscooter/?ftype=1&type=99&Marke=Innoscooter&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Italjet/?ftype=1&type=99&Marke=Italjet&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Jawa/?ftype=1&type=99&Marke=Jawa&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Jiajue/?ftype=1&type=99&Marke=Jiajue&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Jinlun/?ftype=1&type=99&Marke=Jinlun&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Jmstar/?ftype=1&type=99&Marke=Jmstar&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Jonway/?ftype=1&type=99&Marke=Jonway&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Junak/?ftype=1&type=99&Marke=Junak&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Kawasaki/?ftype=1&type=99&Marke=Kawasaki&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Keeway/?ftype=1&type=99&Marke=Keeway&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Kreidler/?ftype=1&type=99&Marke=Kreidler&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/KSR-Moto/?ftype=1&type=99&Marke=KSR-Moto&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/KTM/?ftype=1&type=99&Marke=KTM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Kymco/?ftype=1&type=99&Marke=Kymco&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Lambretta/?ftype=1&type=99&Marke=Lambretta&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Laverda/?ftype=1&type=99&Marke=Laverda&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Leonart/?ftype=1&type=99&Marke=Leonart&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Lexmoto/?ftype=1&type=99&Marke=Lexmoto&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Lifan/?ftype=1&type=99&Marke=Lifan&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Linhai/?ftype=1&type=99&Marke=Linhai&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/LML/?ftype=1&type=99&Marke=LML&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Longbo/?ftype=1&type=99&Marke=Longbo&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Longjia/?ftype=1&type=99&Marke=Longjia&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Luxxon/?ftype=1&type=99&Marke=Luxxon&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Maico/?ftype=1&type=99&Marke=Maico&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Malaguti/?ftype=1&type=99&Marke=Malaguti&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Masai/?ftype=1&type=99&Marke=Masai&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Mash/?ftype=1&type=99&Marke=Mash&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/MBK/?ftype=1&type=99&Marke=MBK&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Meko/?ftype=1&type=99&Marke=Meko&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/MITT/?ftype=1&type=99&Marke=MITT&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Moto+Guzzi/?ftype=1&type=99&Marke=Moto%20Guzzi&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Moto+Morini/?ftype=1&type=99&Marke=Moto%20Morini&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Motorhispania/?ftype=1&type=99&Marke=Motorhispania&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Motowell/?ftype=1&type=99&Marke=Motowell&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/MV+Agusta/?ftype=1&type=99&Marke=MV%20Agusta&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/MZ%2FMUZ/?ftype=1&type=99&Marke=MZ%2FMUZ&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Niu/?ftype=1&type=99&Marke=Niu&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Norton/?ftype=1&type=99&Marke=Norton&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Online/?ftype=1&type=99&Marke=Online&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/OSSA/?ftype=1&type=99&Marke=OSSA&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Pegasus/?ftype=1&type=99&Marke=Pegasus&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Peugeot/?ftype=1&type=99&Marke=Peugeot&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/PGO/?ftype=1&type=99&Marke=PGO&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Piaggio/?ftype=1&type=99&Marke=Piaggio&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Polaris/?ftype=1&type=99&Marke=Polaris&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Puch/?ftype=1&type=99&Marke=Puch&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Qingqi/?ftype=1&type=99&Marke=Qingqi&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Quadro/?ftype=1&type=99&Marke=Quadro&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Quickfoot%2FOpen+Concepts/?ftype=1&type=99&Marke=Quickfoot%2FOpen%20Concepts&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Rex/?ftype=1&type=99&Marke=Rex&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Rieju/?ftype=1&type=99&Marke=Rieju&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Rivero/?ftype=1&type=99&Marke=Rivero&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Royal+Alloy/?ftype=1&type=99&Marke=Royal%20Alloy&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Royal+Enfield/?ftype=1&type=99&Marke=Royal%20Enfield&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Sachs/?ftype=1&type=99&Marke=Sachs&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Scomadi/?ftype=1&type=99&Marke=Scomadi&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/SFM/?ftype=1&type=99&Marke=SFM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Sherco/?ftype=1&type=99&Marke=Sherco&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Silence+Urban+Ecomobility/?ftype=1&type=99&Marke=Silence%20Urban%20Ecomobility&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Simson/?ftype=1&type=99&Marke=Simson&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Sky+Team/?ftype=1&type=99&Marke=Sky%20Team&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/SMC%2FBarossa/?ftype=1&type=99&Marke=SMC%2FBarossa&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Super+Soco/?ftype=1&type=99&Marke=Super%20Soco&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Suzuki/?ftype=1&type=99&Marke=Suzuki&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/SWM/?ftype=1&type=99&Marke=SWM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/SYM/?ftype=1&type=99&Marke=SYM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Tauris/?ftype=1&type=99&Marke=Tauris&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/TGB/?ftype=1&type=99&Marke=TGB&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/TM+Racing/?ftype=1&type=99&Marke=TM%20Racing&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Triton/?ftype=1&type=99&Marke=Triton&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Triumph/?ftype=1&type=99&Marke=Triumph&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/UK-Moden/?ftype=1&type=99&Marke=UK-Moden&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/UM/?ftype=1&type=99&Marke=UM&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Ural/?ftype=1&type=99&Marke=Ural&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Vent-Moto/?ftype=1&type=99&Marke=Vent-Moto&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Vespa/?ftype=1&type=99&Marke=Vespa&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Victory/?ftype=1&type=99&Marke=Victory&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Voge/?ftype=1&type=99&Marke=Voge&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/WMI/?ftype=1&type=99&Marke=WMI&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Wottan/?ftype=1&type=99&Marke=Wottan&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Yadea/?ftype=1&type=99&Marke=Yadea&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Yamaha/?ftype=1&type=99&Marke=Yamaha&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Zero/?ftype=1&type=99&Marke=Zero&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Zongshen/?ftype=1&type=99&Marke=Zongshen&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Zontes/?ftype=1&type=99&Marke=Zontes&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Z%C3%BCndapp/?ftype=1&type=99&Marke=Z%C3%BCndapp&vsr=all",
    #     "https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/ZZZ/?ftype=1&type=99&Marke=ZZZ&vsr=all",
    # ]
    # for u in urls[:1]:
    #     filename = f"{u.replace('//', '_').replace('-', '_').replace(' ', '_')}.html"
    #     print(filename)
    #     exit()
    #     if not os.path.exists(filename):
    #         response = requests.get(u, cookies=cookies, headers=headers)
    #         src_res = response.text
    #         soup_res = BeautifulSoup(src_res, 'lxml')
    #         # Поиск тега title
    #         title_tag = soup_res.find('title')

    #         # Проверка содержимого тега title и его вывод
    #         if title_tag and title_tag.get_text() == "404 Not Found":
    #             print(u)
    #         else:
    #             with open(filename, "w", encoding='utf-8') as file:
    #                 file.write(src_res)
    #             time.sleep(10)
    #             print(f'Сохранил {u}, пауза 10сек')


    url_template = 'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/{}/?ftype=1&type=99&Marke={}&vsr=all'
    with open("larsson.html", encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    all_brand_tag = soup.find('select', attrs={'id': 'Marke'})
    for a in all_brand_tag:
        br = a.get_text(strip=True)
        if not br:
            continue
        part1 = urllib.parse.quote_plus(br)
        part2 = urllib.parse.quote(br, safe='')
        new_url = url_template.format(part1, part2)
        filename = f"{br.replace('//', '_').replace('-', '_').replace(' ', '_')}.html"
        if not os.path.exists(filename):
            part1 = urllib.parse.quote_plus(br)
            part2 = urllib.parse.quote(br, safe='')
            new_url = url_template.format(part1, part2)
            response = requests.get(new_url, cookies=cookies, headers=headers)
            src_res = response.text
            soup_res = BeautifulSoup(src_res, 'lxml')
            # Поиск тега title
            title_tag = soup_res.find('title')

            # Проверка содержимого тега title и его вывод
            if title_tag and title_tag.get_text() == "404 Not Found":
                print(new_url)
            else:
                with open(filename, "w", encoding='utf-8') as file:
                    file.write(src_res)
                time.sleep(10)
                print(f'Сохранил {br}, пауза 10сек')


if __name__ == "__main__":
    get_all_brand()
