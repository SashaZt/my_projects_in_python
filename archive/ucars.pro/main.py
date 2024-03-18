import requests
from bs4 import BeautifulSoup
import os
import mysql.connector

num = 0

url_list = ['https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	acura	?make=	acura	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	alfa_romeo	?make=	alfa_romeo	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	audi	?make=	audi	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bentley	?make=	bentley	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	bmw	?make=	bmw	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	buick	?make=	buick	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	cadillac	?make=	cadillac	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chery	?make=	chery	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	chevorlet	?make=	chevorlet	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	citroen	?make=	citroen	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	dodge	?make=	dodge	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ferrari	?make=	ferrari	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	fiat	?make=	fiat	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	ford	?make=	ford	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	geely	?make=	geely	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	genesis	?make=	genesis	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	gmc	?make=	gmc	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	honda	?make=	honda	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hummer	?make=	hummer	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	hyundai	?make=	hyundai	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	infiniti	?make=	infiniti	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	isuzu	?make=	isuzu	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	iveco	?make=	iveco	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jac	?make=	jac	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jaguar	?make=	jaguar	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	jeep	?make=	jeep	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	kia	?make=	kia	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lamborghini	?make=	lamborghini	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	land_rover	?make=	land_rover	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lexus	?make=	lexus	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lincoln	?make=	lincoln	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	lucid_motors	?make=	lucid_motors	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maserati	?make=	maserati	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	maybach	?make=	maybach	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mazda	?make=	mazda	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mclaren	?make=	mclaren	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes	?make=	mercedes	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes_benz	?make=	mercedes_benz	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mercedes-benz	?make=	mercedes-benz	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mini	?make=	mini	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	mitsubishi	?make=	mitsubishi	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	nissan	?make=	nissan	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	opel	?make=	opel	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	peugeot	?make=	peugeot	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	polestar	?make=	polestar	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	porsche	?make=	porsche	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	range_rover	?make=	range_rover	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	renault	?make=	renault	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls_royce	?make=	rolls_royce	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	rolls-royce	?make=	rolls-royce	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	seat	?make=	seat	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	skoda	?make=	skoda	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	subaru	?make=	subaru	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	suzuki	?make=	suzuki	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	tesla	?make=	tesla	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	toyota	?make=	toyota	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volkswagen	?make=	volkswagen	&year-from=	2023	&year-to=	2023	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2014	&year-to=	2014	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2015	&year-to=	2015	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2016	&year-to=	2016	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2017	&year-to=	2017	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2018	&year-to=	2018	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2019	&year-to=	2019	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2020	&year-to=	2020	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2021	&year-to=	2021	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2022	&year-to=	2022	&status=2&page=2', 'https://ucars.pro/ru/sales-history/	volvo	?make=	volvo	&year-from=	2023	&year-to=	2023	&status=2&page=2']

cookies = {
    '_ga': 'GA1.1.1877634419.1684588744',
    '__gads': 'ID=44a75626fff762fd-221fc7b6e1dd001a:T=1684588742:RT=1684588742:S=ALNI_MbrVuywU_pclGo22ghdMa9tZkKa-g',
    '__gpi': 'UID=00000c18a0db2a0e:T=1684588742:RT=1684588742:S=ALNI_MZbONx5nQi2oxly5gKcYbLpJF_slA',
    'SLG_G_WPT_TO': 'ru',
    '__cf_bm': 'xEKQ.QTq.fxpp22gWNwikkKvwPAI.21Mqurxm3YaC4M-1684588744-0-AYzXZdUEqfcB31x9Zo+uZ0ptanEflCnzueeV+TCbOdOmLM0STo7uhyTn6alAN6foP27FFrPDdlSubkJM7bZvrxhuj9kOFIa2zEmGdOuYb0B5',
    'SLG_GWPT_Show_Hide_tmp': '1',
    'SLG_wptGlobTipTmp': '1',
    'XSRF-TOKEN': 'eyJpdiI6InN3SkNpak5aQlIvSGpaL3BXWHhVY0E9PSIsInZhbHVlIjoiMklrSnJFY0l6bHRIZzhZa3FSdVFyQUVGT2F3VU12NVovVGRseW9FaDZ4eDU3bDcxcnVKTzR1NmIva0o1aDVVM05xNFd0ZlVzblFKeVgxMnlrQjUwaE12OVhac04xZWNDTHpJN2VpQmF6TUE0RTJwRklMSEl6V09qeW5LbnIwVGciLCJtYWMiOiJmYzQwZTdmNDJhYjFhY2MyNDIzNDcyZThhNDExZjgzY2U1MDg3NjE0ZGEwYzI2MDk3ZTFkNGU5MmIyYWU2YjJhIiwidGFnIjoiIn0%3D',
    'ucars_session': 'eyJpdiI6IlJZYnhrY0JGbXFkZzBnUG1GMVh6MGc9PSIsInZhbHVlIjoiaGZzVmRzcFZSRzVDRm1lWUI4RDdIR3pRMXZtdHhkRytQeEZJS25EOU9XOFUvTVQxTDR2dWZleURRY1dUNUpUOUhOS1BSTFpzWXdTK2htbnpxeWVKdWdJa2xtRnNNQmM3Z0R5WEF1RldYbkpUUzlGYjlTbVlGZTE5cEhuRzVBZVQiLCJtYWMiOiIwNGNlMzhhYjMyZTg2MTQ0ZDk3ZTk0NTAyNjFjYWZiMzY4NjQ4Mjk0MmFmN2I3YWMyZDRhNDY1MThiMGU4YThmIiwidGFnIjoiIn0%3D',
    '_ga_QYNZZE6GRT': 'GS1.1.1684588743.1.1.1684589216.0.0.0',
}
headers = {
    'authority': 'ucars.pro',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    #'cookie': '_ga=GA1.1.1877634419.1684588744; __gads=ID=44a75626fff762fd-221fc7b6e1dd001a:T=1684588742:RT=1684588742:S=ALNI_MbrVuywU_pclGo22ghdMa9tZkKa-g; __gpi=UID=00000c18a0db2a0e:T=1684588742:RT=1684588742:S=ALNI_MZbONx5nQi2oxly5gKcYbLpJF_slA; SLG_G_WPT_TO=ru; __cf_bm=xEKQ.QTq.fxpp22gWNwikkKvwPAI.21Mqurxm3YaC4M-1684588744-0-AYzXZdUEqfcB31x9Zo+uZ0ptanEflCnzueeV+TCbOdOmLM0STo7uhyTn6alAN6foP27FFrPDdlSubkJM7bZvrxhuj9kOFIa2zEmGdOuYb0B5; SLG_GWPT_Show_Hide_tmp=1; SLG_wptGlobTipTmp=1; XSRF-TOKEN=eyJpdiI6InN3SkNpak5aQlIvSGpaL3BXWHhVY0E9PSIsInZhbHVlIjoiMklrSnJFY0l6bHRIZzhZa3FSdVFyQUVGT2F3VU12NVovVGRseW9FaDZ4eDU3bDcxcnVKTzR1NmIva0o1aDVVM05xNFd0ZlVzblFKeVgxMnlrQjUwaE12OVhac04xZWNDTHpJN2VpQmF6TUE0RTJwRklMSEl6V09qeW5LbnIwVGciLCJtYWMiOiJmYzQwZTdmNDJhYjFhY2MyNDIzNDcyZThhNDExZjgzY2U1MDg3NjE0ZGEwYzI2MDk3ZTFkNGU5MmIyYWU2YjJhIiwidGFnIjoiIn0%3D; ucars_session=eyJpdiI6IlJZYnhrY0JGbXFkZzBnUG1GMVh6MGc9PSIsInZhbHVlIjoiaGZzVmRzcFZSRzVDRm1lWUI4RDdIR3pRMXZtdHhkRytQeEZJS25EOU9XOFUvTVQxTDR2dWZleURRY1dUNUpUOUhOS1BSTFpzWXdTK2htbnpxeWVKdWdJa2xtRnNNQmM3Z0R5WEF1RldYbkpUUzlGYjlTbVlGZTE5cEhuRzVBZVQiLCJtYWMiOiIwNGNlMzhhYjMyZTg2MTQ0ZDk3ZTk0NTAyNjFjYWZiMzY4NjQ4Mjk0MmFmN2I3YWMyZDRhNDY1MThiMGU4YThmIiwidGFnIjoiIn0%3D; _ga_QYNZZE6GRT=GS1.1.1684588743.1.1.1684589216.0.0.0',
    'referer': 'https://ucars.pro/ru/live-auctions?status=1&page=3',
    'sec-ch-ua': '"Chromium";v="112", "Not_A Brand";v="24", "Opera";v="98"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': '(Linux; Android 7.0;) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)',
}

conn = mysql.connector.connect(
    host="localhost",  # Адрес хоста базы данных
    user="car_db_user_001",  # Имя пользователя базы данных
    password="wE8wH9jA3jfC5hK6hY6j",  # Пароль пользователя базы данных
    database="lot_database"  # Имя базы данных
)

proxies = {
    'proxy1': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.15.93:50100',
    'proxy2': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.15.51:50100',
    'proxy3': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.13.80:50100',
	'proxy4': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.14.1:50100',
	'proxy5': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.13.207:50100',
	'proxy6': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.14.219:50100',
	'proxy7': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.13.240:50100',
	'proxy8': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.13.215:50100',
	'proxy9': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.14.253:50100',
	'proxy10': 'http://moiseevdeveloper:wnaYkIXznJ@185.121.13.181:50100',	   
}

cursor = conn.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS lot_copart (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_iaai (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_impact (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_emirates_auction (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_auction_wini (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_uk (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_mea (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_us (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_ca (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_gb (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_ie (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_ae (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_om (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_copart_bh (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_iaai_uk (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_iaai_us (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_iaai_ca (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_iaai_gb (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_iaai_ae (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_iaai_qa (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_impact_ca (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_impact_gb (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_usa (
    price DECIMAL(10, 2),
    vin VARCHAR(255),
    title VARCHAR(255),
    number INT,
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date DATE,
    time TIME,
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer INT,
    retail DECIMAL(10, 2),
    fix DECIMAL(10, 2),
    type_auto VARCHAR(255),
    year INT,
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_canada (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_great_britain (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_ireland (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_uae (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_oman (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_bahrain (
    price DECIMAL(10, 2),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_korea (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS lot_qatar (
    price VARCHAR(255),
    vin VARCHAR(255),
    title VARCHAR(255),
    number VARCHAR(255),
    auction VARCHAR(255),
    country VARCHAR(255),
    branch VARCHAR(255),
    dealer VARCHAR(255),
    pos VARCHAR(255),
    date VARCHAR(255),
    time VARCHAR(255),
    docks VARCHAR(255),
    loss VARCHAR(255),
    crush VARCHAR(255),
    second_crush VARCHAR(255),
    state VARCHAR(255),
    odometer VARCHAR(255),
    retail VARCHAR(255),
    fix VARCHAR(255),
    type_auto VARCHAR(255),
    year VARCHAR(255),
    mark VARCHAR(255),
    model VARCHAR(255),
    color VARCHAR(255),
    body VARCHAR(255),
    drive VARCHAR(255),
    fuel VARCHAR(255),
    engine VARCHAR(255),
    transmission VARCHAR(255)
);
"""

#cursor.execute(create_table_query)

def get_links():
    for url in url_list:
        response = requests.get(url, cookies=cookies,headers=headers, proxies=proxies)
        soup = BeautifulSoup(response.text, 'lxml')
        pagination = int(soup.find('ul', class_='pagination').find_all('li')[-2].text)


        for i in range(1,pagination + 1):
            new_url = url.replace('page=2', f'page={i}')

            response = requests.get(new_url, cookies=cookies, headers=headers, proxies=proxies)
            soup = BeautifulSoup(response.text, 'lxml')
            thumbs = soup.find_all('a', class_='vehicle-card__thumb')

            for thumb in thumbs:
                link = thumb.get('href')

                yield link




for link in get_links():
        tds_list1 = []
        tds_list2 = []
        tds_list3 = []
        tds_list4 = []
        image_urls = []
        response = requests.get(
            link,
            cookies=cookies,
            headers=headers,
            proxies=proxies
        )
        soup = BeautifulSoup(response.text, 'lxml')

        pill = soup.find_all('div', class_='pill')
        title = soup.find('div', class_='headline').text if soup.find('div', class_='headline') else None
        tablets = soup.find_all('table', class_='card__table')
        table1 = tablets[2]
        table2=tablets[3]
        table3=tablets[0]
        table4=tablets[1]

        rows1 = table1.find_all('tr')
        for row in rows1:
            tds = row.find_all('td')
            for i in range(1, len(tds), 2):
                tds_list1.append(tds[i].text)

        rows2 = table2.find_all('tr')
        for row in rows2:
            tds = row.find_all('td')
            for i in range(1, len(tds), 2):
                tds_list2.append(tds[i].text)

        rows3 = table3.find_all('tr')
        for row in rows3:
            tds = row.find_all('td')
            for i in range(1, len(tds), 2):
                tds_list3.append(tds[i].text)

        rows4 = table4.find_all('tr')
        for row in rows4:
            tds = row.find_all('td')
            for i in range(1, len(tds), 2):
                tds_list4.append(tds[i].text)

        vin = pill[0].text[5:]
        number = pill[1].text


        price = soup.find('span', class_='lot__bidding-digits').text

        imgs = soup.find_all('img', class_='lot__slider-image')
        for img_tag in imgs:
            if 'data-splide-lazy' in img_tag.attrs:
                image_url = img_tag['data-splide-lazy']
                image_urls.append(image_url)
            elif 'src' in img_tag.attrs:
                image_url = img_tag['src']
                image_urls.append(image_url)

        auction = tds_list1[0]
        country = tds_list1[1]
        branch = tds_list1[2]
        dealer = tds_list1[3]
        pos = tds_list1[4]
        date = tds_list1[5]
        time = tds_list1[6]

        docks = tds_list2[0]
        loss = tds_list2[1]
        crush = tds_list2[2]
        second_crush = tds_list2[3]
        state = tds_list2[4]
        odometer = tds_list2[5]
        retail = tds_list2[6]
        fix = tds_list2[7]

        type_auto = tds_list3[0]
        year = tds_list3[1]
        mark = tds_list3[2]
        model = tds_list3[3]
        color = tds_list3[4]

        body = tds_list4[0]
        drive = tds_list4[1]
        fuel = tds_list4[2]
        engine = tds_list4[3]
        transmission = tds_list4[4]

        folder_name = number
        folder_path = os.path.join(f"c:\\scrap_tutorial-master\\ucars.pro\\{auction}", folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        for url in image_urls:
            response = requests.get(url, cookies=cookies,headers=headers)
            if response.status_code == 200:
                image_name = url.split("/")[-1]
                file_name, _ = os.path.splitext(image_name)
                file_path = os.path.join(folder_path, f'{file_name}.jpg')
                if os.path.exists(file_path):
                    continue
                try:
                    with open(file_path, "wb") as file:
                        file.write(response.content)
                except:
                    None
        if auction == 'Copart':

            insert_query = """
            INSERT INTO lot_copart (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)

            conn.commit()


        elif auction == 'IAAI':
            insert_query = """
            INSERT INTO lot_iaai (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()


        elif auction == 'Impact':
            insert_query = """
            INSERT INTO lot_impact (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Emirates Auction':
            insert_query = """
            INSERT INTO lot_emirates_auction (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Auction Wini':
            insert_query = """
            INSERT INTO lot_auction_wini (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart UK':
            insert_query = """
            INSERT INTO lot_copart_uk (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart MEA':
            insert_query = """
            INSERT INTO lot_copart_mea (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart US':
            insert_query = """
            INSERT INTO lot_copart_us (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart CA':
            insert_query = """
            INSERT INTO lot_copart_ca (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart GB':
            insert_query = """
            INSERT INTO lot_copart_gb (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart IE':
            insert_query = """
            INSERT INTO lot_copart_ie (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart AE':
            insert_query = """
            INSERT INTO lot_copart_ae (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart OM':
            insert_query = """
            INSERT INTO lot_copart_om (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Copart BH':
            insert_query = """
            INSERT INTO lot_copart_bh (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'IAAI UK':
            insert_query = """
            INSERT INTO lot_iaai_uk (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'IAAI US':
            insert_query = """
            INSERT INTO lot_iaai_us (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'IAAI CA':
            insert_query = """
            INSERT INTO lot_iaai_ca (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'IAAI GB':
            insert_query = """
            INSERT INTO lot_iaai_gb (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'IAAI AE':
            insert_query = """
            INSERT INTO lot_iaai_ae (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'IAAI QA':
            insert_query = """
            INSERT INTO lot_iaai_qa (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Impact CA':
            insert_query = """
            INSERT INTO lot_impact_ca (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Impact GB':
            insert_query = """
            INSERT INTO lot_impact_gb (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Usa':
            insert_query = """
            INSERT INTO lot_usa (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Canada':
            insert_query = """
            INSERT INTO lot_canada (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Great Britain':
            insert_query = """
            INSERT INTO lot_great_britain (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Ireland':
            insert_query = """
            INSERT INTO lot_ireland (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Uae':
            insert_query = """
            INSERT INTO lot_uae (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Oman':
            insert_query = """
            INSERT INTO lot_oman (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Bahrain':
            insert_query = """
            INSERT INTO lot_bahrain (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Korea':
            insert_query = """
            INSERT INTO lot_korea (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()

        elif auction == 'Qatar':
            insert_query = """
            INSERT INTO lot_qatar (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                docks, loss, crush, second_crush, state, odometer, retail, fix,
                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission
            )

            cursor.execute(insert_query, values)
            conn.commit()



        num +=1
        print(num)

conn.close()
        
        

